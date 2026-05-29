from __future__ import annotations

from story_engine import checks
from story_engine.agents import judge_safety
from story_engine.errors import raise_run_failed
from story_engine.schemas import DraftStory, JudgeDecision, JudgeReport, RequestClassification, StoryBlueprint
from story_engine.text.normalizers import normalize_dialogue
from story_engine.trace import event as trace_event

from ._common import APPROVAL_BLOCKING_CHECKS
from .judge import FAILURE_PRIORITY

def _language_failure_from_decision(decision: JudgeDecision) -> JudgeReport | None:
    polishable_checks = {"phrase_repetition"}
    failed = [
        failure
        for failure in decision.deterministic_failures
        if not failure.get("ok", True) and failure.get("check_name") in polishable_checks
    ]
    if not failed:
        return None
    reasons = []
    guidance = []
    for failure in failed:
        check_name = failure.get("check_name", "language")
        issues = failure.get("issues") or []
        reasons.append(f"{check_name}: {'; '.join(str(issue) for issue in issues) if issues else 'failed'}")
        if failure.get("revision_guidance"):
            guidance.append(str(failure["revision_guidance"]))
    return JudgeReport(
        judge_name="language",
        verdict="fail",
        reason=" | ".join(reasons),
        revision_guidance=" ".join(guidance) if guidance else "Fix only the flagged language and surface-form issues.",
    )


def _polish_failures(judge_reports: list[JudgeReport], decision: JudgeDecision) -> list[JudgeReport]:
    failures = [
        report
        for report in judge_reports
        if report.verdict == "fail" and report.judge_name != "coherence_judge"
    ]
    language = _language_failure_from_decision(decision)
    if language is not None:
        failures.append(language)
    return sorted(failures, key=lambda report: FAILURE_PRIORITY.get(report.judge_name, 99))

def _apply_post_polish_normalizers(draft: DraftStory) -> DraftStory:
    body, dialogue_stats = normalize_dialogue(draft.body)
    trace_event("normalizer.normalize_dialogue", event_type="normalizer", details=dialogue_stats, **dialogue_stats)
    return DraftStory(title=draft.title, body=body, actual_word_count=checks.calculate_word_count(body), scenes=[])


def _run_final_safety_gate(
    draft: DraftStory,
    blueprint: StoryBlueprint,
    classification: RequestClassification,
    request: str,
) -> None:
    report = judge_safety(draft, blueprint, classification, request)
    trace_event("pipeline.safety_final_gate", verdict=report.verdict)
    if report.verdict != "pass":
        raise_run_failed(
            agent_name="safety_judge",
            failure_category="safety_fail",
            last_raw_response=repr(report.to_dict()),
            attempt_count=1,
        )


def _fail_loud_after_normalizers(
    draft: DraftStory,
    blueprint: StoryBlueprint,
) -> list[str]:
    post = checks.run_all(draft, blueprint)
    blocking_failures = [
        {"check_name": name, **result}
        for name, result in post.checks.items()
        if name in APPROVAL_BLOCKING_CHECKS and not result.get("ok", True)
    ]
    return [f"Post-normalizer residual failure: {failure}" for failure in blocking_failures]
