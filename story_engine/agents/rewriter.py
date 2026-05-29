from __future__ import annotations

from typing import Any, Iterable

from story_engine import model_client
from story_engine.config import AGENT_TEMPERATURES
from story_engine.errors import RunFailed
from story_engine.prompts.scene_rewriter import build_prompt as build_scene_rewriter_prompt
from story_engine.schemas import CharacterCard, SceneCard, SchemaError
from story_engine.text.normalizers import normalize_dialogue
from story_engine.trace import event as trace_event

from .writer import _parse_scene_paragraphs, validate_written_scene


_RETRY_GUIDANCE_BY_CODE: dict[str, str] = {
    "missing_dialogue": "Your previous rewrite still failed `missing_dialogue`. The replacement scene must include the planned dialogue as quoted spoken speech from the planned speaker. Thoughts, narration, feelings, gestures, and actions do not count as dialogue.",
    "missing_setting": "Your previous rewrite still failed `missing_setting`. The replacement scene must visibly show the SceneCard setting through a concrete place or object detail.",
    "missing_planned_beat": "Your previous rewrite still failed `missing_planned_beat`. The replacement scene must visibly show the missing planned beat as action, object detail, speech, or what a character notices. Do not summarize it as a feeling or conclusion.",
    "end_with_missing": "Your previous rewrite still failed `end_with_missing`. The second paragraph must end with the SceneCard `end_with` image exactly or with only tiny grammar changes.",
}

_RETRY_GENERIC_REMINDER = "Do not include a code in `addresses_codes` unless the rewritten paragraphs visibly fix it."


def _build_retry_guidance(codes: Iterable[str]) -> str:
    seen: set[str] = set()
    instructions: list[str] = []
    for code in codes:
        clean_code = code.strip()
        if not clean_code or clean_code in seen:
            continue
        seen.add(clean_code)
        if clean_code in _RETRY_GUIDANCE_BY_CODE:
            instructions.append(_RETRY_GUIDANCE_BY_CODE[clean_code])
    if not instructions:
        return ""
    instructions.append(_RETRY_GENERIC_REMINDER)
    return "\n".join(instructions)


def rewrite_scene(
    card: SceneCard,
    failed_scene_text: str,
    fail_codes_with_evidence: list[dict[str, Any]],
    *,
    character_cards: list[CharacterCard] | None = None,
    already_written_summary: str = "",
    upcoming_scene_summary: str = "",
) -> dict[str, Any]:
    prompt = build_scene_rewriter_prompt(
        card,
        already_written_summary=already_written_summary,
        upcoming_scene_summary=upcoming_scene_summary,
        failed_scene_text=failed_scene_text,
        fail_codes_with_evidence=fail_codes_with_evidence,
        character_cards=character_cards,
    )
    requested_codes = [str(item.get("code", "")).strip() for item in fail_codes_with_evidence if str(item.get("code", "")).strip()]
    requested = set(requested_codes)

    def _parse_response(response: Any) -> dict[str, Any]:
        if not isinstance(response, dict):
            raise SchemaError("Scene rewriter response must be a JSON object")
        body = normalize_dialogue(_parse_scene_paragraphs(response, "rewriter"))[0]
        addresses_codes = response.get("addresses_codes", requested_codes)
        if not isinstance(addresses_codes, list) or not all(isinstance(code, str) and code.strip() for code in addresses_codes):
            addresses_codes = requested_codes
        trimmed_codes = [code.strip() for code in addresses_codes]
        residual = validate_written_scene(body, card)
        omitted_codes = requested - set(trimmed_codes)
        residual_codes = {item["code"] for item in residual if item.get("code") in requested}
        return {
            "body": body,
            "addresses_codes": trimmed_codes,
            "residual_failures": residual,
            "omitted_codes": sorted(omitted_codes),
            "requested_residual_codes": sorted(residual_codes),
        }

    guidance = "; ".join(
        f"{item.get('code', 'unknown')}: {item.get('evidence', '')}"
        for item in fail_codes_with_evidence
    )
    last_response: Any = None
    last_error: Exception | None = None
    last_parsed: dict[str, Any] | None = None
    for attempt in range(3):
        try:
            last_response = model_client.call_model_json(
                prompt,
                temperature=AGENT_TEMPERATURES["scene_rewriter"],
                max_tokens=4000,
                agent_name="scene_rewriter",
                iteration=attempt,
            )
            parsed = _parse_response(last_response)
            last_parsed = dict(parsed)
            omitted_codes = parsed.pop("omitted_codes")
            residual_codes = parsed.pop("requested_residual_codes")
            if omitted_codes or residual_codes:
                if attempt < 2:
                    trace_event(
                        "agents.rewrite_scene",
                        event_type="retry",
                        attempt=attempt + 1,
                        reason=f"rewrite_incomplete: omitted_codes={omitted_codes}; residual_codes={residual_codes}",
                    )
                    residual_for_guidance = list(omitted_codes) + [
                        c for c in residual_codes if c not in set(omitted_codes)
                    ]
                    deterministic_block = _build_retry_guidance(residual_for_guidance)
                    prompt = (
                        f"{prompt}\n\n# Repair\n"
                        f"Repair: omitted_codes={omitted_codes}. "
                        f"Repair: residual_codes={residual_codes}. "
                        f"Fix these requested fail codes with evidence: {guidance}. "
                        "Return the complete paragraphs array and addresses_codes."
                        + (
                            f"\n\n## Code-specific repair guidance\n{deterministic_block}"
                            if deterministic_block
                            else ""
                        )
                    )
                    continue
                return parsed
            return parsed
        except RunFailed as exc:
            if exc.failure_category == "safety_fail":
                raise
            last_error = exc
            break
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                trace_event("agents.rewrite_scene", event_type="retry", attempt=attempt + 1, reason=f"{type(exc).__name__}: {exc}")
                prompt = (
                    f"{prompt}\n\n# Repair\n"
                    f"The previous scene rewrite failed with {type(exc).__name__}: {exc}. "
                    f"Fix these requested fail codes with evidence: {guidance}. "
                    "Return the complete paragraphs array and addresses_codes."
                )
                continue
    if last_parsed is not None:
        trace_event(
            "agents.rewrite_scene",
            event_type="degraded",
            reason="rewriter_last_parsed_after_retries",
            fallback=True,
        )
        return {key: last_parsed[key] for key in ("body", "addresses_codes", "residual_failures")}
    trace_event(
        "agents.rewrite_scene",
        event_type="degraded",
        reason="rewriter_original_scene_after_retries",
        fallback=True,
        last_error=str(last_error) if last_error else None,
    )
    return {"body": failed_scene_text, "addresses_codes": [], "residual_failures": []}
