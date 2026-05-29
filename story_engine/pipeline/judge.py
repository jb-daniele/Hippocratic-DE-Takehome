from __future__ import annotations

from time import perf_counter
from typing import Any

from story_engine import checks
from story_engine.schemas import DraftStory, JudgeDecision, JudgeReport, RequestClassification, RevisionPlan, StoryBlueprint
from story_engine.trace import event as trace_event

from ._common import APPROVAL_BLOCKING_CHECKS, _latency_ms, _trace_check_result, _trace_route


def aggregate_and_decide(reports: list[JudgeReport], post_draft_report) -> JudgeDecision:
    start = perf_counter()
    failures = [
        {
            "judge_name": report.judge_name,
            "reason": report.reason,
            "revision_guidance": report.revision_guidance,
        }
        for report in reports
        if report.verdict != "pass"
    ]
    deterministic_failures = [
        {"check_name": name, **result}
        for name, result in post_draft_report.checks.items()
        if not result.get("ok") or result.get("revision_guidance")
    ]
    all_pass = not failures
    blocking_checks_ok = all(post_draft_report.checks.get(name, {}).get("ok", True) for name in APPROVAL_BLOCKING_CHECKS)
    blocking_checks_ok = blocking_checks_ok and post_draft_report.checks.get("ending_image", {}).get("ok", True)
    approved = all_pass and blocking_checks_ok
    decision = JudgeDecision(
        all_pass=all_pass,
        failures=failures,
        deterministic_failures=deterministic_failures,
        approved=approved,
    )
    trace_event("pipeline.aggregate_and_decide", approved=decision.approved, failures=len(decision.failures), latency_ms=_latency_ms(start))
    return decision


FAILURE_PRIORITY = {
    "safety_judge": 1,
    "coherence_judge": 2,
    "language": 3,
}
ROUTE_BY_CODE = {
    "request_drift": "scene",
    "ownership_drift": "scene",
    "continuity_break": "scene",
    "weak_scene_progression": "scene",
    "unresolved_central_problem": "scene",
    "missing_resolution": "scene",
    "missing_ending_image": "scene",
    "must_avoid_violation": "scene",
}
WHOLE_STORY_TARGET_SCENE = {
    "missing_resolution": 3,
    "missing_ending_image": 4,
    "unresolved_central_problem": 4,
}
def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = " ".join(str(item).split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _failure_sort_key(item: dict[str, Any]) -> int:
    return FAILURE_PRIORITY.get(item.get("judge_name") or item.get("kind") or "", 99)


def _check_failure_priority(check_name: str) -> int:
    if check_name in APPROVAL_BLOCKING_CHECKS:
        return APPROVAL_BLOCKING_CHECKS.index(check_name) + 10
    return 60


def _preserve_items(draft: DraftStory, blueprint: StoryBlueprint) -> list[str]:
    return [
        f"title: {draft.title}",
        f"character_names: {', '.join(blueprint.main_characters)}",
        f"selected_story_mode: {blueprint.selected_story_mode}",
        f"category_id: {blueprint.category_id}",
    ]


def _remove_contested_preserve(preserve: list[str], must_fix: list[str]) -> list[str]:
    contested = " ".join(must_fix).lower()
    result = []
    for item in preserve:
        key = item.split(":", 1)[0].lower()
        if key and key in contested:
            continue
        result.append(item)
    return result


def build_revision_plan(decision: JudgeDecision, draft: DraftStory, blueprint: StoryBlueprint) -> RevisionPlan:
    start = perf_counter()
    prioritized: list[tuple[int, str, str | None]] = []
    for failure in decision.failures:
        if isinstance(failure, dict):
            label = failure.get("judge_name") or failure.get("kind") or "failure"
            reason = failure.get("reason")
            if reason:
                prioritized.append((_failure_sort_key(failure), f"{label}: {reason}", failure.get("revision_guidance")))

    guidance: list[str] = []
    for _priority, must_fix_item, revision_guidance in prioritized:
        if revision_guidance:
            guidance.append(str(revision_guidance))

    ranked_must_fix: list[tuple[int, str]] = [(priority, item) for priority, item, _guidance in prioritized]
    for failure in decision.deterministic_failures:
        check_name = failure.get("check_name", "deterministic_check")
        if failure.get("ok", False):
            revision_guidance = failure.get("revision_guidance")
            if revision_guidance:
                guidance.append(str(revision_guidance))
            continue
        issues = failure.get("issues") or []
        issue_text = "; ".join(str(issue) for issue in issues) if issues else failure.get("severity", "failed")
        ranked_must_fix.append((_check_failure_priority(check_name), f"{check_name}: {issue_text}"))
        revision_guidance = failure.get("revision_guidance")
        if revision_guidance:
            guidance.append(str(revision_guidance))

    ranked_must_fix.sort(key=lambda item: item[0])
    must_fix = _dedupe([item for _priority, item in ranked_must_fix])[:3]
    guidance = _dedupe(guidance)
    preserve = _remove_contested_preserve(_preserve_items(draft, blueprint), must_fix)
    plan = RevisionPlan(
        must_fix=must_fix,
        revision_guidance_hints=guidance,
        preserve=preserve,
    )
    trace_event("pipeline.build_revision_plan", must_fix=len(plan.must_fix), latency_ms=_latency_ms(start))
    return plan


def _category_chip(classification: RequestClassification) -> str:
    chips = {
        "general_bedtime_story": "Classic bedtime story",
        "cozy_animal_story": "Animal story",
        "gentle_adventure": "Gentle adventure",
        "magical_bedtime_story": "Magical story",
        "friendship_and_feelings": "Friendship story",
        "silly_soft_story": "Silly story",
        "calm_educational_story": "Educational story",
    }
    return chips.get(classification.category_id, classification.category_display_name)


def _page_break_suggestions(pages: list[str]) -> list[int]:
    counts: list[int] = []
    total = 0
    for page in pages[:-1]:
        total += checks.calculate_word_count(page)
        counts.append(total)
    return counts


def _cover(classification: RequestClassification, blueprint: StoryBlueprint, actual_word_count: int, pages: list[str]) -> dict[str, Any]:
    return {
        "title": blueprint.title,
        "category_id": classification.category_id,
        "category_display_name": classification.category_display_name,
        "category_chip": _category_chip(classification),
        "actual_word_count": actual_word_count,
        "characters": blueprint.main_characters,
        "page_count": len(pages),
        "fallback": classification.fallback,
        "classifier_skipped": classification.classifier_skipped,
    }


def _pre_stitch_scene_failures(draft: DraftStory, blueprint: StoryBlueprint) -> list[dict[str, Any]]:
    scenes = _split_scenes(draft.body, blueprint, draft=draft)
    failures: list[dict[str, Any]] = []
    writer_residuals = getattr(draft, "_writer_residuals", None)
    for index, (scene, card) in enumerate(zip(scenes, blueprint.scene_cards)):
        hits = validate_written_scene(scene, card)
        residual_codes = set()
        if writer_residuals is not None and index < len(writer_residuals):
            residual_codes = {str(code).strip() for code in writer_residuals[index] if str(code).strip()}
        new_hits = hits if writer_residuals is None else [hit for hit in hits if hit.get("code") not in residual_codes]
        result = {
            "ok": not new_hits,
            "severity": "failure" if new_hits else "none",
            "route": "scene" if new_hits else None,
            "issues": [f"{hit['code']}: {hit['evidence']}" for hit in hits],
            "new_issues": [f"{hit['code']}: {hit['evidence']}" for hit in new_hits],
            "writer_residual_codes": sorted(residual_codes),
        }
        _trace_check_result("pipeline.pre_stitch.scene_card", "validate_written_scene", result, scene_index=index)
        if new_hits:
            _trace_route("pipeline.pre_stitch.scene_card", "scene", "hard_failure", scene_index=index)
            failures.append(
                {
                    "source": "validate_written_scene",
                    "scene_index": index + 1,
                    "route": "scene",
                    "hard_failures": [hit["code"] for hit in new_hits],
                    "issues": [f"{hit['code']}: {hit['evidence']}" for hit in new_hits],
                    "hits": new_hits,
                }
            )
    return failures


def _route_failure_buckets(judge_reports: list[JudgeReport], post_draft_report) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {"scene": [], "polish_language": [], "safety": []}
    for report in judge_reports:
        if report.judge_name == "safety_judge" and report.verdict != "pass":
            _trace_route("pipeline.route_failure_buckets", "safety", "safety_judge", judge_name=report.judge_name)
            buckets["safety"].append(report.to_dict())
        if report.judge_name == "coherence_judge":
            for code in report.fail_codes:
                payload = code.to_dict()
                payload["source"] = report.judge_name
                route = ROUTE_BY_CODE.get(code.code, "scene")
                _trace_route("pipeline.route_failure_buckets", route, code.code, scene_index=code.scene_index)
                buckets[route].append(payload)
    for name, result in post_draft_report.checks.items():
        if result.get("ok", True):
            continue
        if name == "ending_image":
            _trace_route("pipeline.route_failure_buckets", "scene", "ending_image", check_name="ending_image")
            buckets["scene"].append({"check_name": "ending_image", "code": "missing_ending_image", "scene_index": 4, **result})
            continue
        route = result.get("route")
        if route is None:
            if name == "phrase_repetition":
                route = "polish_language"
        if route:
            _trace_route("pipeline.route_failure_buckets", route, name, check_name=name)
            buckets.setdefault(route, []).append({"check_name": name, **result})
    return buckets


def _fail_loud_if_unrepairable(route: str, failures: list[dict[str, Any]]) -> str | None:
    if not failures:
        return None
    return f"Unrepairable {route} failure: {failures[0]}"


def _is_severe_coherence_failure(judge_reports: list[JudgeReport], decision: JudgeDecision) -> bool:
    coherence_failed = any(report.judge_name == "coherence_judge" and report.verdict != "pass" for report in judge_reports)
    high_severity = sum(
        1
        for failure in decision.deterministic_failures
        if not failure.get("ok", True) and failure.get("severity") == "failure"
    )
    return coherence_failed and high_severity >= 3
