from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from typing import Any

from story_engine import checks
from story_engine.agents import judge_coherence, judge_language, judge_safety, polish
from story_engine.errors import RunFailed, raise_run_failed
from story_engine.guardrails import pre_request_guard
from story_engine.schemas import DraftStory, FinalStoryPackage, JudgeReport, RequestOptions, RevisionPlan
from story_engine.trace import event as trace_event

from ._common import _latency_ms, _submit_with_trace_context, _trace_check_result, _trace_route
from .classify import understand
from .judge import ROUTE_BY_CODE, WHOLE_STORY_TARGET_SCENE, _dedupe, _fail_loud_if_unrepairable, _is_severe_coherence_failure, _route_failure_buckets, aggregate_and_decide, build_revision_plan
from .package import _apply_title, _package
from .plan import assemble_blueprint, plan_blueprint
from .polish_helpers import _apply_post_polish_normalizers, _fail_loud_after_normalizers, _polish_failures, _run_final_safety_gate
from .write import SCENE_STITCHER_BYPASS_ENABLED, _assert_target_paragraphs, _normalized_scene_paragraphs, _pre_stitch_scene_failures, _repair_scene_failures, _validate_stitched_output, build_stitch_failure, compute_scene_boundaries, rewrite_scene, stitch_scenes, write_draft


def judge_all(
    draft,
    blueprint,
    classification,
    request: str,
):
    start = perf_counter()
    def _judge_language_only(draft, blueprint, classification, request):
        del blueprint, classification, request
        return judge_language(draft)

    judges = [
        ("safety_judge", judge_safety),
        ("coherence_judge", judge_coherence),
        ("language", _judge_language_only),
    ]
    with ThreadPoolExecutor(max_workers=len(judges)) as executor:
        futures = {
            name: _submit_with_trace_context(executor, fn, draft, blueprint, classification, request)
            for name, fn in judges
        }
        reports = [futures[name].result() for name, _ in judges]
    trace_event("pipeline.judge_all", verdicts={report.judge_name: report.verdict for report in reports}, latency_ms=_latency_ms(start))
    return reports


def _evaluate_draft(draft, blueprint, classification, request: str):
    post_draft_report = checks.run_all(draft, blueprint)
    for name, result in post_draft_report.checks.items():
        _trace_check_result("pipeline.checks", name, result)
    judge_reports = judge_all(draft, blueprint, classification, request)
    for report in judge_reports:
        trace_event(
            "pipeline.judges",
            event_type="check_result",
            check_name=report.judge_name,
            passed=report.verdict == "pass",
            fail_codes=[code.to_dict() for code in report.fail_codes],
            reason=report.reason,
        )
    judge_decision = aggregate_and_decide(judge_reports, post_draft_report)
    trace_event(
        "agent.judges",
        approved=judge_decision.approved,
        failures=[failure.get("judge_name") for failure in judge_decision.failures if isinstance(failure, dict)],
    )
    return post_draft_report, judge_reports, judge_decision


def run(request: str, options: RequestOptions | dict[str, Any], *, remix_source: str | None = None) -> FinalStoryPackage:
    start = perf_counter()
    try:
        if isinstance(options, RequestOptions):
            request_options = options
        elif hasattr(options, "to_dict"):
            request_options = RequestOptions(**options.to_dict())
        else:
            request_options = RequestOptions(**options)
        trace_event("agent.pre_guard")
        pre_guard = pre_request_guard(request)
        if not pre_guard["allowed"]:
            raise_run_failed(
                agent_name="pre_guard",
                failure_category="safety_fail",
                last_raw_response=pre_guard.get("reason"),
                attempt_count=1,
            )

        understanding = understand(request, request_options)
        classification = understanding["classification"]

        blueprint = plan_blueprint(understanding)
        trace_event("agent.writer", scene_count=blueprint.scene_plan["scene_count"])
        warnings: list[str] = []
        last_valid_draft: DraftStory | None = None
        draft = write_draft(blueprint)
        _drift = _assert_target_paragraphs(draft, blueprint, "scene_writer")
        warnings.extend(_drift)
        if not _drift:
            last_valid_draft = draft
        elif last_valid_draft is not None:
            draft = last_valid_draft
            warnings.append("reverted to last structurally valid draft at scene_writer")
        repair_invocations = 0
        pre_stitch_failures = _pre_stitch_scene_failures(draft, blueprint)
        trace_event("pipeline.pre_stitch_routing", event_type="route", route="pre_stitch", failures=len(pre_stitch_failures))
        unresolved_scene_failures = [failure for failure in pre_stitch_failures if failure.get("route") == "scene"]
        if unresolved_scene_failures:
            draft, repair_warnings = _repair_scene_failures(draft, blueprint, unresolved_scene_failures)
            warnings.extend(repair_warnings)
            repair_invocations += len(unresolved_scene_failures)
        assembled_body = draft.body
        scene_paragraphs = _normalized_scene_paragraphs(draft, blueprint)
        scene_boundaries = compute_scene_boundaries(list(draft.scenes)) if draft.scenes else compute_scene_boundaries(
            ["\n\n".join(paragraphs) for paragraphs in scene_paragraphs]
        )
        seam_check = checks.check_scene_seams(scene_paragraphs, blueprint)
        _trace_check_result("pipeline.pre_stitch", "scene_seams", seam_check)
        seams_clean = seam_check["ok"]
        stitch_failure = None

        if SCENE_STITCHER_BYPASS_ENABLED and seams_clean:
            _trace_route("pipeline.stitch", "bypass", "seams_clean")
        else:
            if seams_clean:
                stitch_failure = build_stitch_failure(seam_check, assembled_body, blueprint, legacy=True)
            else:
                stitch_failure = build_stitch_failure(seam_check, assembled_body, blueprint, legacy=False)
                if not stitch_failure["seam_failures"]:
                    trace_event(
                        "pipeline.stitch",
                        event_type="fallback",
                        reason="seam_check_unparseable",
                        raw_issues=seam_check["issues"],
                    )
                    warnings.append("seam_check_unparseable; stitcher skipped")
                    stitch_failure = None
            if stitch_failure is not None:
                trace_event("agent.stitcher", scene_count=blueprint.scene_plan["scene_count"])
                trace_event("pipeline.stitch", event_type="repair_budget", repair_stage="stitch", consumed=1)
                repair_invocations += 1
                candidate = stitch_scenes(blueprint, draft, stitch_failure=stitch_failure)
                valid, validation_issues = _validate_stitched_output(candidate.body, assembled_body, blueprint)
                if not valid:
                    trace_event(
                        "pipeline.stitch",
                        event_type="fallback",
                        reason="stitched_output_invalid",
                        issues=validation_issues,
                    )
                    warnings.append("stitched_output_invalid; using assembled body")
                else:
                    boundary_check = checks.check_boundary_only_edits(
                        assembled_body,
                        candidate.body,
                        stitch_failure["boundary_indexes"],
                        scene_boundaries,
                    )
                    if not boundary_check["ok"]:
                        trace_event(
                            "pipeline.stitch",
                            event_type="fallback_boundary_edit",
                            issues=boundary_check["issues"],
                        )
                        warnings.append("stitched_output_edited_non_boundary; using assembled body")
                    else:
                        draft = candidate
        _drift = _assert_target_paragraphs(draft, blueprint, "post_stitch")
        warnings.extend(_drift)
        if not _drift:
            last_valid_draft = draft
        elif last_valid_draft is not None:
            draft = last_valid_draft
            warnings.append("reverted to last structurally valid draft at post_stitch")
        post_draft_report, judge_reports, judge_decision = _evaluate_draft(draft, blueprint, classification, request)
        route_buckets = _route_failure_buckets(judge_reports, post_draft_report)
        for _ in range(2):
            if not route_buckets["scene"]:
                break
            draft, repair_warnings = _repair_scene_failures(draft, blueprint, route_buckets["scene"])
            warnings.extend(repair_warnings)
            repair_invocations += len(route_buckets["scene"])
            post_draft_report, judge_reports, judge_decision = _evaluate_draft(draft, blueprint, classification, request)
            route_buckets = _route_failure_buckets(judge_reports, post_draft_report)
        if any(str(item.get("check_name") or item.get("code") or "").strip() in {"ending_image", "missing_ending_image"} for item in route_buckets["scene"]):
            warnings.append("ending_image unresolved after repair")
        if _is_severe_coherence_failure(judge_reports, judge_decision):
            warnings.append("Severe coherence failure detected; packaging with approved=False.")
        judge_trail = [[report.to_dict() for report in judge_reports]]
        revision_plans: list[dict[str, Any]] = []

        MAX_POLISH_ITERATIONS = 3  # initial attempt + up to 2 retries
        polish_iterations_run = 0
        total_polish_failures = 0
        for polish_iteration in range(1, MAX_POLISH_ITERATIONS + 1):
            failures_to_polish = _polish_failures(judge_reports, judge_decision)
            if not failures_to_polish:
                break
            safety_attempted_this_pass = any(
                f.judge_name == "safety_judge" for f in failures_to_polish
            )
            plan = build_revision_plan(judge_decision, draft, blueprint)
            revision_plans.append({"polish_failures": [failure.to_dict() for failure in failures_to_polish], **plan.to_dict()})
            trace_event("agent.polish", iteration=polish_iteration, failures=[failure.judge_name for failure in failures_to_polish])
            trace_event("pipeline.polish", event_type="repair_budget", repair_stage="polish", consumed=1, failure_count=len(failures_to_polish), iteration=polish_iteration)
            for failure in failures_to_polish:
                draft = polish(draft, failure, blueprint)
                _drift = _assert_target_paragraphs(draft, blueprint, "polish")
                warnings.extend(_drift)
                if not _drift:
                    last_valid_draft = draft
                elif last_valid_draft is not None:
                    draft = last_valid_draft
                    warnings.append("reverted to last structurally valid draft at polish")
                repair_invocations += 1
            polish_iterations_run = polish_iteration
            total_polish_failures += len(failures_to_polish)
            post_draft_report, judge_reports, judge_decision = _evaluate_draft(draft, blueprint, classification, request)
            judge_trail.append([report.to_dict() for report in judge_reports])
            if safety_attempted_this_pass:
                safety_still_failing = any(
                    r.judge_name == "safety_judge" and r.verdict == "fail"
                    for r in judge_reports
                )
                if safety_still_failing:
                    raise_run_failed(
                        agent_name="safety_judge",
                        failure_category="safety_fail",
                        last_raw_response="Safety polish did not clear safety failure",
                        attempt_count=polish_iteration,
                    )
        if polish_iterations_run > 0:
            warnings.append(f"Polish ran {polish_iterations_run} iteration(s) on {total_polish_failures} failure(s); result packaged regardless.")

        if not judge_decision.approved:
            residual_buckets = _route_failure_buckets(judge_reports, post_draft_report)
            if residual_buckets["scene"]:
                warning = _fail_loud_if_unrepairable("scene", residual_buckets["scene"])
                if warning:
                    warnings.append(warning)
            if polish_iterations_run >= MAX_POLISH_ITERATIONS and _polish_failures(judge_reports, judge_decision):
                warnings.append(f"Polish cap reached after {MAX_POLISH_ITERATIONS} iterations; returning last draft.")

        draft = _apply_post_polish_normalizers(draft)
        _drift = _assert_target_paragraphs(draft, blueprint, "normalizer")
        warnings.extend(_drift)
        if not _drift:
            last_valid_draft = draft
        elif last_valid_draft is not None:
            draft = last_valid_draft
            warnings.append("reverted to last structurally valid draft at normalizer")
        warnings.extend(_fail_loud_after_normalizers(draft, blueprint))
        _run_final_safety_gate(draft, blueprint, classification, request)
        draft = _apply_title(draft, blueprint)
        _drift = _assert_target_paragraphs(draft, blueprint, "final_package")
        warnings.extend(_drift)
        if not _drift:
            last_valid_draft = draft
        elif last_valid_draft is not None:
            draft = last_valid_draft
            warnings.append("reverted to last structurally valid draft at final_package")

        package = _package(
            request_options=request_options,
            classification=classification,
            blueprint=blueprint,
            draft=draft,
            post_draft_report=post_draft_report,
            judge_trail=judge_trail,
            judge_decision=judge_decision,
            revision_plans=revision_plans,
            warnings=warnings,
            iterations_used=repair_invocations,
            remix_source=remix_source,
        )
        trace_event("pipeline.run", approved=package.approved, iterations_used=package.iterations_used, latency_ms=_latency_ms(start))
        return package
    except RunFailed as exc:
        trace_event("pipeline.run", event_type="run_failed", agent_name=exc.agent_name, failure_category=exc.failure_category)
        raise


def revise_with_feedback(package: FinalStoryPackage, feedback: str, request: str) -> FinalStoryPackage:
    start = perf_counter()
    pre_guard = pre_request_guard(feedback)
    if not pre_guard["allowed"]:
        raise_run_failed(
            agent_name="pre_guard_revise",
            failure_category="safety_fail",
            last_raw_response=pre_guard.get("reason"),
            attempt_count=1,
        )

    base_plan = build_revision_plan(package.judge_decision, package.story, package.blueprint)
    must_fix = _dedupe(base_plan.must_fix + [f"user_feedback: {feedback}"])
    plan = RevisionPlan(
        must_fix=must_fix,
        revision_guidance_hints=base_plan.revision_guidance_hints,
        preserve=base_plan.preserve,
    )
    feedback_failure = JudgeReport(
        judge_name="language",
        verdict="fail",
        reason=f"user_feedback: {feedback}",
        revision_guidance="Apply the user's feedback with the smallest safe polish; preserve paragraph structure.",
    )
    draft = polish(package.story, feedback_failure, package.blueprint)
    draft = _apply_post_polish_normalizers(draft)
    warnings = list(package.warnings)
    warnings.extend(_fail_loud_after_normalizers(draft, package.blueprint))
    _run_final_safety_gate(draft, package.blueprint, package.classification, request)
    draft = _apply_title(draft, package.blueprint)
    post_draft_report, judge_reports, judge_decision = _evaluate_draft(draft, package.blueprint, package.classification, request)
    judge_trail = package.judge_trail + [[report.to_dict() for report in judge_reports]]
    revision_plans = package.revision_plans + [plan.to_dict()]
    revised = _package(
        request_options=package.request,
        classification=package.classification,
        blueprint=package.blueprint,
        draft=draft,
        post_draft_report=post_draft_report,
        judge_trail=judge_trail,
        judge_decision=judge_decision,
        revision_plans=revision_plans,
        warnings=warnings,
        iterations_used=package.iterations_used + 1,
        remix_source=package.remix_source,
    )
    trace_event("pipeline.revise_with_feedback", approved=revised.approved, latency_ms=_latency_ms(start))
    return revised
