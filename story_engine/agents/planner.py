from __future__ import annotations

import hashlib
import re
from time import perf_counter
from typing import Any

from story_engine import model_client
from story_engine.config import AGENT_TEMPERATURES
from story_engine.errors import RunFailed
from story_engine.prompts.arc_planner import build_prompt as build_arc_prompt
from story_engine.prompts.character_designer import build_prompt as build_character_prompt
from story_engine.prompts.paragraph_structures import paragraph_structure_for
from story_engine.prompts.scene_planner import build_prompt as build_scene_planner_prompt
from story_engine.schemas import CharacterCard, RequestClassification, SceneCard, SchemaError, StorySpine
from story_engine.trace import event as trace_event

from ._common import ArcValidationError, SceneCardValidationError, _latency_ms, _trace_degraded
from .tool_schemas import (
    CHARACTER_CARDS_TOOL_NAME,
    CHARACTER_CARDS_TOOL_SCHEMA,
    SCENE_CARDS_TOOL_NAME,
    SCENE_CARDS_TOOL_SCHEMA,
    STORY_SPINE_TOOL_NAME,
    STORY_SPINE_TOOL_SCHEMA,
)


def _stable_index(seed: str, count: int) -> int:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % count


def _stable_choice(options: list[str], seed: str) -> str:
    return options[_stable_index(seed, len(options))]


_CHARACTER_KINDS_BY_CATEGORY = {
    "general_bedtime_story": ["child", "parent", "sibling", "grandparent", "stuffed bear", "stuffed bunny"],
    "cozy_animal_story": ["hedgehog", "mole", "field mouse", "rabbit", "otter", "sparrow"],
    "gentle_adventure": ["child", "neighbor", "mail carrier", "gardener", "shopkeeper", "librarian"],
    "magical_bedtime_story": ["child", "fairy", "garden gnome", "friendly dragon", "forest elf", "talking owl"],
    "friendship_and_feelings": ["child", "friend", "classmate", "teammate", "sibling", "new neighbor"],
    "silly_soft_story": ["child", "parent", "sibling", "stuffed duck", "stuffed frog", "family cat"],
    "calm_educational_story": ["child", "parent", "caregiver", "teacher", "garden plant", "pond snail"],
}

_SUPPORT_NAMES_BY_CATEGORY = {
    "general_bedtime_story": ["Hazel", "Nia", "Oren", "Milo"],
    "cozy_animal_story": ["Hazel", "Moss", "Junie", "Pip"],
    "gentle_adventure": ["Tavi", "Nia", "Piper", "Otis"],
    "magical_bedtime_story": ["Asha", "Nova", "Ivo", "Mina"],
    "friendship_and_feelings": ["Hazel", "Mina", "Tavi", "Asha", "Ben", "Kai"],
    "silly_soft_story": ["Marta", "Tessa", "Parsnip", "Otis"],
    "calm_educational_story": ["Nia", "Marta", "Otis", "Lina"],
}


def _build_support_character(
    classification: RequestClassification,
    existing_names: set[str],
) -> CharacterCard:
    seed = f"{classification.request_text}:{classification.category_id}"
    kind_options = _CHARACTER_KINDS_BY_CATEGORY.get(
        classification.category_id,
        _CHARACTER_KINDS_BY_CATEGORY["general_bedtime_story"],
    )
    name_options = _SUPPORT_NAMES_BY_CATEGORY.get(
        classification.category_id,
        _SUPPORT_NAMES_BY_CATEGORY["general_bedtime_story"],
    )
    normalized_existing = {name.strip().lower() for name in existing_names if str(name).strip()}
    available_names = [name for name in name_options if name.lower() not in normalized_existing]
    if available_names:
        name = _stable_choice(available_names, seed + ":support_name")
    else:
        base_name = _stable_choice(name_options, seed + ":support_name")
        suffix = 2
        while f"{base_name} {suffix}".lower() in normalized_existing:
            suffix += 1
        name = f"{base_name} {suffix}"

    kind = _stable_choice(kind_options, seed + ":support_kind")
    group_like_kinds = {"group", "pair", "trio", "family", "toy"}
    if any(token in kind for token in group_like_kinds):
        pronouns = "they/them"
    else:
        pronouns = _stable_choice(["she/her", "he/him"], seed + ":support_pronouns")
    return CharacterCard(
        name=name[:30],
        pronouns=pronouns,
        kind=kind[:30],
        role="comforting friend",
    )


def _story_spine_from_response(response: Any, scene_plan: dict[str, int], classification: RequestClassification) -> StorySpine:
    if not isinstance(response, dict):
        raise SchemaError("Arc planner response must be a JSON object")
    allowed = {
        "story_premise",
        "protagonist_name",
        "setting",
        "central_problem",
        "resolution",
        "ending_image",
        "scene_count",
        "scene_steps",
        "must_avoid",
    }
    extra = sorted(set(response) - allowed)
    if extra:
        raise SchemaError(f"Arc planner returned unexpected field(s): {', '.join(extra)}")
    spine = StorySpine(**response)
    if spine.scene_count != scene_plan["scene_count"]:
        raise SchemaError("Arc planner returned the wrong scene_count")
    issues: list[dict[str, Any]] = []
    if not spine.setting.strip():
        issues.append({"code": "arc_missing_setting", "evidence": "story_spine.setting"})
    if not spine.resolution.strip():
        issues.append({"code": "arc_missing_resolution", "evidence": "story_spine.resolution"})
    if not spine.ending_image.strip():
        issues.append({"code": "arc_missing_ending_image", "evidence": "story_spine.ending_image"})
    if spine.scene_count != 4:
        issues.append({"code": "arc_scene_count_invalid", "evidence": str(spine.scene_count)})
    normalized_steps = [step.strip().casefold() for step in spine.scene_steps if step.strip()]
    if len(normalized_steps) != 4:
        issues.append({"code": "arc_scene_steps_count_invalid", "evidence": str(len(normalized_steps))})
    elif len(set(normalized_steps)) != 4:
        issues.append({"code": "arc_scene_steps_not_distinct", "evidence": "; ".join(spine.scene_steps)})
    if issues:
        details = "; ".join(f"{issue['code']}: {issue['evidence']}" for issue in issues)
        raise ArcValidationError(
            f"StorySpine failed validation: {details}",
            check=str(issues[0]["code"]),
            retry_details=details,
            details={"issues": issues},
        )
    return spine


def _split_scene_step(step: str) -> tuple[list[str], list[str]]:
    cleaned = step.strip() or "the gentle moment began"
    parts = re.split(r" then ", cleaned, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        first, second = parts[0].strip(), parts[1].strip()
    else:
        first, second = cleaned, "the moment continued gently"
    return (
        [first, "a small detail anchors the scene"],
        [second, "a quiet beat closes the moment"],
    )


def _synthesize_scene_card(
    *,
    index: int,
    step: str,
    spine: StorySpine,
    classification: RequestClassification,
) -> SceneCard:
    structures = paragraph_structure_for(classification.category_id).get("scenes", [])
    functions = structures[index].get("functions", []) if index < len(structures) else []
    first_must_show, second_must_show = _split_scene_step(step)
    return SceneCard(
        scene=index + 1,
        setting=spine.setting or "a cozy place",
        scene_change=spine.central_problem or "a gentle shift in the moment",
        paragraphs=[2 * index + 1, 2 * index + 2],
        paragraph_beats=[
            {
                "paragraph": 2 * index + 1,
                "function": functions[0] if len(functions) > 0 else "gentle_setup",
                "must_show": first_must_show,
            },
            {
                "paragraph": 2 * index + 2,
                "function": functions[1] if len(functions) > 1 else "gentle_continuation",
                "must_show": second_must_show,
            },
        ],
        dialogue=[],
        end_with=spine.ending_image if index == 3 else None,
    )


def plan_arc(
    classification: RequestClassification,
    scene_plan: dict[str, int],
    character_cards: list[CharacterCard] | None = None,
) -> StorySpine:
    start = perf_counter()
    prompt = build_arc_prompt(classification, scene_plan, character_cards)
    last_error: Exception | None = None
    last_response: Any = None
    last_spine: StorySpine | None = None
    for attempt in range(3):
        try:
            last_response = model_client.call_model_tool(
                prompt,
                tool_name=STORY_SPINE_TOOL_NAME,
                tool_schema=STORY_SPINE_TOOL_SCHEMA,
                temperature=AGENT_TEMPERATURES["arc_planner"],
                agent_name="arc_planner",
                iteration=attempt,
            )
            if isinstance(last_response, dict):
                try:
                    last_spine = StorySpine(**last_response)
                except Exception:
                    pass
            spine = _story_spine_from_response(
                last_response,
                scene_plan,
                classification,
            )
            trace_event(
                "agents.plan_arc",
                fallback=False,
                attempt=attempt + 1,
                category_id=classification.category_id,
                scenes=spine.scene_count,
                latency_ms=_latency_ms(start),
            )
            return spine
        except RunFailed as exc:
            if exc.failure_category == "safety_fail":
                raise
            last_error = exc
            break
        except Exception as exc:
            last_error = exc
            trace_event(
                "agents.plan_arc.attempt",
                ok=False,
                attempt=attempt + 1,
                error_type=type(exc).__name__,
                category_id=classification.category_id,
                latency_ms=_latency_ms(start),
            )
            if attempt < 2:
                retry_details = getattr(exc, "retry_details", str(exc))
                trace_event("agents.plan_arc", event_type="retry", attempt=attempt + 1, reason=retry_details)
                prompt = (
                    f"{prompt}\n\n# Repair\n"
                    f"Your previous StorySpine failed validation: {retry_details}. "
                    "Return exactly the StorySpine fields. "
                    f"Schema errors: {retry_details}"
                )

    if last_spine is not None:
        trace_event(
            "agents.plan_arc",
            event_type="degraded",
            reason="arc_planner_last_spine_after_retries",
            fallback=True,
            category_id=classification.category_id,
            scenes=last_spine.scene_count,
            latency_ms=_latency_ms(start),
        )
        return last_spine
    scene_count = scene_plan["scene_count"]
    spine = StorySpine(
        story_premise=classification.request_text or classification.category_display_name,
        protagonist_name=_protagonist_name(classification) or "Pip",
        setting="a cozy place",
        central_problem="a small worry",
        resolution="comfort and rest",
        ending_image="they settle in for the night",
        scene_count=scene_count,
        scene_steps=[
            "arrive at the cozy place",
            "notice a small worry",
            "find a gentle solution",
            "settle in for the night",
        ],
        must_avoid=[],
    )
    trace_event(
        "agents.plan_arc",
        event_type="degraded",
        reason="arc_planner_synth_from_classification",
        fallback=True,
        category_id=classification.category_id,
        scenes=scene_count,
        last_error=str(last_error) if last_error else None,
        latency_ms=_latency_ms(start),
    )
    return spine


def _protagonist_name(classification: RequestClassification) -> str:
    if classification.main_characters:
        return classification.main_characters[0].name
    return classification.main_character_name.strip()


def _character_cards_from_response(response: Any) -> tuple[list[CharacterCard], list[str]]:
    if isinstance(response, dict):
        cards_payload = response.get("cast")
    else:
        cards_payload = response
    if not isinstance(cards_payload, list) or not cards_payload:
        raise SchemaError("Character designer must return a non-empty character list")

    cards: list[CharacterCard] = []
    errors: list[str] = []
    for index, item in enumerate(cards_payload, start=1):
        label = ""
        if isinstance(item, dict) and isinstance(item.get("name"), str) and item.get("name", "").strip():
            label = f" '{item['name'].strip()}'"
        if not isinstance(item, dict):
            errors.append(f"Card {index}{label}: card must be a JSON object")
            continue
        try:
            cards.append(CharacterCard(**item))
        except SchemaError as exc:
            errors.append(f"Card {index}{label}: {exc}")
    return cards, errors


def design_characters(classification: RequestClassification) -> list[CharacterCard]:
    start = perf_counter()
    prompt = build_character_prompt(classification)
    last_response: Any = None
    last_errors: list[str] = []
    last_cards: list[CharacterCard] = []
    protagonist = _protagonist_name(classification).casefold()
    for attempt in range(3):
        try:
            last_response = model_client.call_model_tool(
                prompt,
                tool_name=CHARACTER_CARDS_TOOL_NAME,
                tool_schema=CHARACTER_CARDS_TOOL_SCHEMA,
                temperature=AGENT_TEMPERATURES["character_designer"],
                agent_name="character_designer",
                iteration=attempt,
            )
            cards, errors = _character_cards_from_response(last_response)
            last_cards = cards
            last_errors = errors
            has_protagonist = bool(protagonist) and any(card.name.casefold() == protagonist for card in cards)
            if cards and not errors and (not protagonist or has_protagonist):
                trace_event("agents.design_characters", fallback=False, count=len(cards), latency_ms=_latency_ms(start))
                return cards
            if cards and has_protagonist:
                _trace_degraded(
                    "character_designer",
                    fields_coerced=[],
                    original_value=last_response,
                    coerced_value=[card.to_dict() for card in cards],
                    reason="discarded invalid character cards after repairable field errors",
                )
                trace_event("agents.design_characters", fallback=False, degraded=True, count=len(cards), latency_ms=_latency_ms(start))
                return cards
            raise SchemaError("; ".join(errors or ["protagonist character card missing"]))
        except RunFailed as exc:
            if exc.failure_category == "safety_fail":
                raise
            last_errors = [str(exc)]
            break
        except Exception as exc:
            if not last_errors:
                last_errors = [str(exc)]
            trace_event(
                "agents.design_characters.attempt",
                ok=False,
                attempt=attempt + 1,
                error_type=type(exc).__name__,
                latency_ms=_latency_ms(start),
            )
            if attempt < 2:
                guidance = "; ".join(last_errors)
                trace_event("agents.design_characters", event_type="retry", attempt=attempt + 1, reason=guidance)
                prompt = (
                    f"{prompt}\n\n# Repair\n"
                    "Your previous character payload had these per-card errors verbatim: "
                    f"{guidance}. Return the full cast array again."
                )
                continue
    if last_cards:
        trace_event(
            "agents.design_characters",
            event_type="degraded",
            reason="character_designer_last_cards_after_retries",
            fallback=True,
            count=len(last_cards),
            latency_ms=_latency_ms(start),
        )
        return last_cards
    card = CharacterCard(
        name=_protagonist_name(classification) or "Pip",
        pronouns="they/them",
        kind="small friend",
        role="comforting friend",
    )
    trace_event(
        "agents.design_characters",
        event_type="degraded",
        reason="character_designer_synth_from_classification",
        fallback=True,
        count=1,
        last_errors=last_errors,
        latency_ms=_latency_ms(start),
    )
    return [card]


def _scene_cards_from_response(response: Any) -> list[SceneCard]:
    if not isinstance(response, dict):
        raise SchemaError("Scene Planner response must be a JSON object")
    payload = response.get("scene_cards")
    if not isinstance(payload, list):
        raise SchemaError("Scene Planner must return scene_cards as a list")
    return [SceneCard(**item) for item in payload]


def _speaker_match(raw_speaker: str, valid_names: list[str]) -> str | None:
    raw = raw_speaker.strip().casefold()
    if not raw:
        return None
    for name in valid_names:
        if raw == name.casefold():
            return name
    return None


def _normalize_scene_cards(cards: list[SceneCard], character_cards: list[CharacterCard]) -> tuple[list[SceneCard], list[str], dict[str, Any]]:
    valid_names = [card.name for card in character_cards]
    changed_fields: set[str] = set()
    original = [card.to_dict() for card in cards]
    normalized: list[SceneCard] = []
    for expected_scene, card in enumerate(cards, start=1):
        payload = card.to_dict()
        if payload.get("scene") != expected_scene:
            payload["scene"] = expected_scene
            changed_fields.add("scene")
        dialogue = []
        for item in payload.get("dialogue", []) or []:
            speaker = str(item.get("speaker", ""))
            matched = _speaker_match(speaker, valid_names)
            if matched is None:
                changed_fields.add("dialogue")
                dialogue.append({"speaker": speaker, "purpose": item.get("purpose", "")})
                continue
            if matched != speaker:
                changed_fields.add("dialogue")
            dialogue.append({"speaker": matched, "purpose": item.get("purpose", "")})
        payload["dialogue"] = dialogue
        if expected_scene != 4 and payload.get("end_with") is not None:
            payload["end_with"] = None
            changed_fields.add("end_with")
        normalized_card = SceneCard(**payload)
        normalized.append(normalized_card)
    return normalized, sorted(changed_fields), {"original": original, "coerced": [card.to_dict() for card in normalized]}


def _scene_plan_repair_guidance(
    issues: list[dict[str, Any]],
    *,
    valid_speakers: list[str],
    spine: StorySpine,
) -> str:
    issue_details = "; ".join(f"{issue.get('code')}: {issue.get('evidence')}" for issue in issues)
    extras: list[str] = []
    wrong_count_issue = next(
        (issue for issue in issues if str(issue.get("code")) == "cards_wrong_count"),
        None,
    )
    if wrong_count_issue is not None:
        actual_count = wrong_count_issue.get("evidence")
        extras.append(
            f"You returned {actual_count} scene_cards, but must return exactly 4. "
            "Return one SceneCard for each story_spine.scene_steps item. "
            "Do not merge scenes. Do not stop after two cards. "
            "The output must contain `scene_cards` with exactly 4 items, in order: scenes 1, 2, 3, and 4."
        )
    extras.append(f"Valid character names/actors are exactly: {valid_speakers}.")
    if any(str(issue.get("code")) == "card_unknown_speaker" for issue in issues):
        extras.append(f"Use only these dialogue speakers: {valid_speakers}.")
    if any(str(issue.get("code")) == "card_thin_must_show" for issue in issues):
        extras.append(
            "Each `must_show` must be detailed enough to guide the writer. Replace very short beats with concrete visible beats that include a character or object, a concrete place/object detail, and a visible action or state change."
        )
    if any(str(issue.get("code")) == "card_end_with_only_scene4" for issue in issues):
        extras.append(
            "Your previous SceneCards set `end_with` on a non-final scene. "
            "Set `end_with` to null for Scene 1, Scene 2, and Scene 3. "
            "Only Scene 4 may have a non-null `end_with`, and it must match `story_spine.ending_image`."
        )
    if any(str(issue.get("code")) == "card_end_with_diverges" for issue in issues):
        extras.append(f"Scene 4 end_with must overlap with story_spine.ending_image: {spine.ending_image}.")
    return " ".join(part for part in [issue_details, *extras] if part)


def _scene_plan_failure_category(
    last_error: Exception | None,
    last_issues: list[dict[str, Any]] | None,
) -> str:
    if last_issues:
        for issue in reversed(last_issues):
            code = issue.get("code")
            if code:
                return str(code)
    if isinstance(last_error, SceneCardValidationError):
        for issue in reversed(getattr(last_error, "issues", []) or []):
            code = issue.get("code")
            if code:
                return str(code)
    if isinstance(last_error, SchemaError):
        return "schema_error"
    return "missing_required_field"


def _content_tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text.lower())
        if len(token) > 2 and token not in {"the", "and", "for", "with", "into", "from", "that"}
    ]


def _validate_scene_cards_inline(
    cards: list[SceneCard],
    spine: StorySpine,
    character_cards: list[CharacterCard],
    classification: RequestClassification,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if len(cards) != 4:
        issues.append({"code": "cards_wrong_count", "evidence": str(len(cards))})
        return issues
    valid_speakers = {card.name for card in character_cards}
    structures = paragraph_structure_for(classification.category_id).get("scenes", [])
    ending_tokens = set(_content_tokens(spine.ending_image))
    for index, card in enumerate(cards):
        expected_scene = index + 1
        expected_paragraphs = [2 * index + 1, 2 * index + 2]
        if card.scene != expected_scene:
            issues.append({"code": "card_wrong_scene", "evidence": f"scene {card.scene}", "scene_number": expected_scene})
        if card.paragraphs != expected_paragraphs:
            issues.append({"code": "card_wrong_paragraphs", "evidence": str(card.paragraphs), "scene_number": expected_scene})
        expected_functions = set(structures[index].get("functions", [])) if index < len(structures) else set()
        for beat in card.paragraph_beats:
            if beat.function not in expected_functions:
                issues.append({"code": "card_wrong_function", "evidence": beat.function, "scene_number": expected_scene})
            for item in beat.must_show:
                if len(item.split()) < 4:
                    issues.append({"code": "card_thin_must_show", "evidence": item, "scene_number": expected_scene, "paragraph": beat.paragraph})
        for item in card.dialogue:
            if item.speaker not in valid_speakers:
                issues.append({"code": "card_unknown_speaker", "evidence": item.speaker, "scene_number": expected_scene})
        if expected_scene != 4 and card.end_with is not None:
            issues.append({"code": "card_end_with_only_scene4", "evidence": str(card.end_with), "scene_number": expected_scene})
        if expected_scene == 4:
            if card.end_with is None:
                issues.append({"code": "card_missing_end_with", "evidence": "scene 4", "scene_number": expected_scene})
            else:
                if not (set(_content_tokens(card.end_with)) & ending_tokens):
                    issues.append({"code": "card_end_with_diverges", "evidence": card.end_with, "scene_number": expected_scene})
    return issues


def plan_scenes(
    spine: StorySpine,
    character_cards: list[CharacterCard],
    classification: RequestClassification,
) -> list[SceneCard]:
    start = perf_counter()
    prompt = build_scene_planner_prompt(spine, character_cards, classification)
    last_error: Exception | None = None
    last_issues: list[dict[str, Any]] = []
    last_response: Any = None
    last_cards: list[SceneCard] = []
    valid_speakers = [card.name for card in character_cards]
    for attempt in range(3):
        try:
            last_response = model_client.call_model_tool(
                prompt,
                tool_name=SCENE_CARDS_TOOL_NAME,
                tool_schema=SCENE_CARDS_TOOL_SCHEMA,
                temperature=AGENT_TEMPERATURES["scene_planner"],
                max_tokens=4000,
                agent_name="scene_planner",
                iteration=attempt,
            )
            cards = _scene_cards_from_response(
                last_response
            )
            cards, changed_fields, normalized_values = _normalize_scene_cards(cards, character_cards)
            last_cards = cards
            issues = _validate_scene_cards_inline(cards, spine, character_cards, classification)
            if attempt == 2 and issues:
                thin_issues = [issue for issue in issues if issue.get("code") == "card_thin_must_show"]
                blocking_issues = [issue for issue in issues if issue.get("code") != "card_thin_must_show"]
                if thin_issues and not blocking_issues:
                    trace_event(
                        "agents.plan_scenes.thin_must_show_accepted",
                        count=len(thin_issues),
                        issues=thin_issues,
                    )
                    issues = []
            if issues:
                last_issues = issues
                details = "; ".join(f"{issue['code']}: {issue['evidence']}" for issue in issues)
                raise SceneCardValidationError(
                    f"SceneCards failed validation: {details}",
                    issues=issues,
                )
            last_issues = []
            if changed_fields:
                _trace_degraded(
                    "scene_planner",
                    fields_coerced=changed_fields,
                    original_value=normalized_values["original"],
                    coerced_value=normalized_values["coerced"],
                    reason=f"mechanically normalized scene cards; valid speakers: {valid_speakers}",
                )
            trace_event(
                "agents.plan_scenes",
                fallback=False,
                attempt=attempt + 1,
                category_id=classification.category_id,
                scenes=len(cards),
                latency_ms=_latency_ms(start),
            )
            return cards
        except RunFailed as exc:
            if exc.failure_category == "safety_fail":
                raise
            last_error = exc
            break
        except Exception as exc:
            last_error = exc
            if isinstance(exc, SceneCardValidationError):
                last_issues = list(getattr(exc, "issues", []) or [])
            trace_event(
                "agents.plan_scenes.attempt",
                ok=False,
                attempt=attempt + 1,
                error_type=type(exc).__name__,
                category_id=classification.category_id,
                latency_ms=_latency_ms(start),
            )
            if attempt < 2:
                issue_details = (
                    _scene_plan_repair_guidance(getattr(exc, "issues", []), valid_speakers=valid_speakers, spine=spine)
                    if isinstance(exc, SceneCardValidationError)
                    else f"{exc}. Valid character names/actors are exactly: {valid_speakers}."
                )
                trace_event("agents.plan_scenes", event_type="retry", attempt=attempt + 1, reason=issue_details)
                wrong_count_issue = (
                    next(
                        (issue for issue in getattr(exc, "issues", []) if str(issue.get("code")) == "cards_wrong_count"),
                        None,
                    )
                    if isinstance(exc, SceneCardValidationError)
                    else None
                )
                final_directive = (
                    (
                        f"FINAL REMINDER: return `scene_cards` with EXACTLY 4 items. "
                        f"You returned {wrong_count_issue.get('evidence')}. "
                        "Produce one SceneCard per story_spine.scene_steps item, in order 1, 2, 3, 4. "
                        "Do not stop early."
                    )
                    if wrong_count_issue is not None
                    else "Return the full scene_cards array again, preserving spine.scene_steps exactly and fixing card_* / cards_* issues."
                )
                prompt = (
                    f"{prompt}\n\n# Repair\n"
                    f"Your previous SceneCards failed validation: {issue_details}.\n\n"
                    f"{final_directive}"
                )
    if last_cards:
        trace_event(
            "agents.plan_scenes",
            event_type="degraded",
            reason="scene_planner_last_normalized_cards_after_retries",
            fallback=True,
            category_id=classification.category_id,
            scenes=len(last_cards),
            latency_ms=_latency_ms(start),
        )
        return last_cards
    cards = [
        _synthesize_scene_card(
            index=index,
            step=spine.scene_steps[index] if index < len(spine.scene_steps) else "the gentle moment continued",
            spine=spine,
            classification=classification,
        )
        for index in range(4)
    ]
    trace_event(
        "agents.plan_scenes",
        event_type="degraded",
        reason="scene_planner_synth_from_spine",
        fallback=True,
        category_id=classification.category_id,
        scenes=len(cards),
        failure_category=_scene_plan_failure_category(last_error, last_issues),
        last_error=str(last_error) if last_error else None,
        latency_ms=_latency_ms(start),
    )
    return cards
