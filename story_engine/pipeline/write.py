from __future__ import annotations

from typing import Any

from story_engine import checks
from story_engine.agents import _paragraph_count, rewrite_scene, stitch_scenes, validate_written_scene, write_draft
from story_engine.agents.stitcher import compute_scene_boundaries
from story_engine.agents.stitcher_failure import build_stitch_failure
from story_engine.checks import calculate_word_count
from story_engine.config import SCENE_STITCHER_BYPASS_ENABLED
from story_engine.schemas import DraftStory, StoryBlueprint
from story_engine.text.summaries import already_written_summary, upcoming_scene_summary
from story_engine.trace import event as trace_event

from ._common import _split_scenes, _trace_check_result, _trace_route
from .judge import WHOLE_STORY_TARGET_SCENE

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


def _normalized_scene_paragraphs(draft: DraftStory, blueprint: StoryBlueprint) -> list[list[str]]:
    raw = list(draft.scenes) if draft.scenes else _split_scenes(draft.body, blueprint, draft=draft)
    normalized: list[list[str]] = []
    for scene in raw:
        normalized.append([paragraph.strip() for paragraph in str(scene).split("\n\n") if paragraph.strip()])
    return normalized


def _validate_stitched_output(stitched_body: str, assembled_body: str, blueprint) -> tuple[bool, list[str]]:
    del blueprint

    def _paragraphs(body: str) -> list[str]:
        return [paragraph.strip() for paragraph in body.split("\n\n") if paragraph.strip()]

    def _jaccard(left: str, right: str) -> float:
        left_tokens = checks._content_tokens(left)
        right_tokens = checks._content_tokens(right)
        if not left_tokens or not right_tokens:
            return 0.0
        left_set = set(left_tokens)
        right_set = set(right_tokens)
        return len(left_set & right_set) / len(left_set | right_set)

    assembled_paragraphs = _paragraphs(assembled_body)
    stitched_paragraphs = _paragraphs(stitched_body)
    issues: list[str] = []

    if len(stitched_paragraphs) != len(assembled_paragraphs):
        issues.append("paragraph_count_mismatch")

    assembled_word_count = calculate_word_count(assembled_body)
    stitched_word_count = calculate_word_count(stitched_body)
    if not 0.9 * assembled_word_count <= stitched_word_count <= 1.1 * assembled_word_count:
        issues.append("word_count_out_of_band")

    if assembled_paragraphs and stitched_paragraphs:
        assembled_final_tokens = checks._content_tokens(assembled_paragraphs[-1])
        stitched_final_tokens = checks._content_tokens(stitched_paragraphs[-1])
        if len(assembled_final_tokens) >= 6 and len(stitched_final_tokens) >= 6 and _jaccard(stitched_paragraphs[-1], assembled_paragraphs[-1]) < 0.5:
            issues.append("final_paragraph_diverged")

    catastrophic = 0
    for stitched_paragraph, assembled_paragraph in zip(stitched_paragraphs, assembled_paragraphs):
        stitched_tokens = checks._content_tokens(stitched_paragraph)
        assembled_tokens = checks._content_tokens(assembled_paragraph)
        if len(stitched_tokens) >= 6 and len(assembled_tokens) >= 6 and _jaccard(stitched_paragraph, assembled_paragraph) < 0.3:
            catastrophic += 1
            if catastrophic >= 2:
                issues.append("catastrophic_paragraph_divergence")
                break

    return (not issues, issues)


def _target_paragraph_count(blueprint: StoryBlueprint) -> int:
    return blueprint.scene_plan["scene_count"] * blueprint.scene_plan["paragraphs_per_scene"]


def _apply_title(draft: DraftStory, blueprint: StoryBlueprint) -> DraftStory:
    title = write_title(blueprint)
    # Keep later revision prompts and saved blueprint metadata aligned with the visible title.
    blueprint.title = title
    return DraftStory(title=title, body=draft.body, actual_word_count=draft.actual_word_count, scenes=[])


def _assert_target_paragraphs(draft: DraftStory, blueprint: StoryBlueprint, stage_name: str) -> list[str]:
    actual = _paragraph_count(draft.body)
    expected = _target_paragraph_count(blueprint)
    if actual == expected:
        return []
    trace_event(
        "pipeline.paragraph_count_drift",
        event_type="degraded",
        stage_name=stage_name,
        expected=expected,
        actual=actual,
        fallback=True,
    )
    return [f"paragraph_count_drift at {stage_name}: expected {expected} got {actual}"]


def _repair_scene_failures(draft: DraftStory, blueprint: StoryBlueprint, failures: list[dict[str, Any]]) -> tuple[DraftStory, list[str]]:
    if not failures:
        return draft, []
    trace_event(
        "pipeline.scene_repair",
        event_type="repair_budget",
        repair_stage="scene",
        consumed=len(failures),
        targeted_scenes=sorted({int(failure.get("scene_index", -1)) for failure in failures if failure.get("scene_index") is not None}),
    )
    scenes = _split_scenes(draft.body, blueprint, draft=draft)
    rewritten_any = False
    rewritten_indexes: set[int] = set()
    ending_image_recheck_indexes = {
        (
            int(failure.get("scene_index")) - 1
            if failure.get("scene_index") is not None
            else WHOLE_STORY_TARGET_SCENE["missing_ending_image"] - 1
        )
        for failure in failures
        if str(failure.get("code") or failure.get("check_name") or "").strip() in {"missing_ending_image", "ending_image"}
    }
    warnings: list[str] = []
    for failure in failures:
        raw_index = failure.get("scene_index")
        code = str(failure.get("code") or failure.get("check_name") or "").strip()
        if raw_index is None:
            if code in WHOLE_STORY_TARGET_SCENE:
                index = WHOLE_STORY_TARGET_SCENE[code] - 1
            elif code in {"request_drift", "must_avoid_violation", "ownership_drift", "continuity_break", "weak_scene_progression"}:
                index = 3
                warnings.append(f"{code} routed to scene 4 by default (no scene_index)")
            else:
                index = 3
        else:
            index = int(raw_index) - 1
        if index in rewritten_indexes or index >= len(scenes) or index >= len(blueprint.scene_cards):
            continue
        card = blueprint.scene_cards[index]
        done = blueprint.scene_cards[:index]
        future = blueprint.scene_cards[index + 1 :]
        hits = failure.get("hits")
        if isinstance(hits, list) and hits:
            fail_codes_with_evidence = [
                {"code": str(hit.get("code", "")).strip(), "evidence": str(hit.get("evidence", "")).strip()}
                for hit in hits
                if str(hit.get("code", "")).strip()
            ]
        else:
            hard_failures = [str(item).strip() for item in failure.get("hard_failures", []) if str(item).strip()]
            issues = [str(item).strip() for item in failure.get("issues", []) if str(item).strip()]
            fail_codes_with_evidence = []
            for offset, item in enumerate(hard_failures):
                evidence = issues[offset] if offset < len(issues) else item
                prefix = f"{item}: "
                if evidence.startswith(prefix):
                    evidence = evidence[len(prefix):]
                fail_codes_with_evidence.append({"code": item, "evidence": evidence[:120]})
            if not fail_codes_with_evidence and code:
                evidence = "; ".join(issues)[:120] if issues else "scene failure"
                fail_codes_with_evidence = [{"code": code, "evidence": evidence}]
        rewritten = rewrite_scene(
            card,
            scenes[index],
            fail_codes_with_evidence,
            character_cards=blueprint.character_cards,
            already_written_summary=already_written_summary(done),
            upcoming_scene_summary=upcoming_scene_summary(future),
        )
        trace_event(
            "pipeline.scene_repair.rewrite",
            scene_index=index,
            residual_failures=rewritten.get("residual_failures", []),
        )
        scenes[index] = rewritten["body"]
        if index in ending_image_recheck_indexes:
            body = "\n\n".join(scene for scene in scenes if scene.strip())
            draft_after_rewrite = DraftStory(
                title=draft.title,
                body=body,
                actual_word_count=checks.calculate_word_count(body),
                scenes=list(scenes),
            )
            ending_image_result = checks.check_ending_image(draft_after_rewrite, blueprint)
            trace_event(
                "pipeline.scene_repair.ending_image_recheck",
                passed=ending_image_result["ok"],
                scene_index=index + 1,
            )
            if not ending_image_result["ok"]:
                warnings.append("ending_image still failing after scene 4 rewrite")
        rewritten_indexes.add(index)
        rewritten_any = True
    if not rewritten_any:
        return draft, warnings
    body = "\n\n".join(scene for scene in scenes if scene.strip())
    return DraftStory(title=draft.title, body=body, actual_word_count=checks.calculate_word_count(body), scenes=scenes), warnings
