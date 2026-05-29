from __future__ import annotations

import re
from time import perf_counter
from typing import Any

from story_engine.agents import design_characters, plan_arc, plan_scenes
from story_engine.config import scene_plan_for
from story_engine.prompts.paragraph_structures import paragraph_structure_for
from story_engine.schemas import CharacterCard, RequestClassification, SceneCard, StoryBlueprint, StorySpine
from story_engine.trace import event as trace_event

from ._common import _latency_ms

def _character_names(classification: RequestClassification, character_cards: list[CharacterCard]) -> list[str]:
    if classification.main_characters:
        return [character.name for character in classification.main_characters]
    return [card.name for card in character_cards]


def _placeholder_title(classification: RequestClassification, character_names: list[str]) -> str:
    if character_names:
        return f"{character_names[0].title()} and the Quiet Night"
    return classification.category_display_name


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


def _synthesized_scene_card(
    *,
    index: int,
    scene_count: int,
    spine: StorySpine,
    category_id: str,
) -> SceneCard:
    step = spine.scene_steps[index]
    structures = paragraph_structure_for(category_id).get("scenes", [])
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
        end_with=spine.ending_image if index == scene_count - 1 else None,
    )


def _duplicate_scene_card(card: SceneCard, *, index: int, scene_count: int, spine: StorySpine) -> SceneCard:
    payload = card.to_dict()
    payload["scene"] = index + 1
    payload["paragraphs"] = [2 * index + 1, 2 * index + 2]
    payload["end_with"] = spine.ending_image if index == scene_count - 1 else None
    beats = list(payload.get("paragraph_beats") or [])
    for offset, beat in enumerate(beats[:2]):
        if isinstance(beat, dict):
            beat["paragraph"] = 2 * index + 1 + offset
    payload["paragraph_beats"] = beats
    return SceneCard(**payload)


def assemble_blueprint(
    classification: RequestClassification,
    spine: StorySpine,
    character_cards: list[CharacterCard],
    scene_cards: list[SceneCard],
    scene_plan: dict[str, int],
) -> StoryBlueprint:
    start = perf_counter()
    character_names = _character_names(classification, character_cards)
    blueprint = StoryBlueprint(
        title=_placeholder_title(classification, character_names),
        category_id=classification.category_id,
        category_display_name=classification.category_display_name,
        selected_story_mode=classification.selected_story_mode,
        main_characters=character_names,
        character_cards=character_cards,
        scene_plan=scene_plan,
        story_spine=spine,
        scene_cards=scene_cards,
    )
    if len(blueprint.scene_cards) != scene_plan["scene_count"]:
        scene_count = scene_plan["scene_count"]
        trace_event(
            "pipeline.assemble_blueprint",
            event_type="degraded",
            reason="scene_cards_count_mismatch",
            expected=scene_count,
            actual=len(blueprint.scene_cards),
            fallback=True,
        )
        normalized_cards = list(blueprint.scene_cards[:scene_count])
        for index in range(len(normalized_cards), scene_count):
            if index < len(spine.scene_steps):
                normalized_cards.append(
                    _synthesized_scene_card(
                        index=index,
                        scene_count=scene_count,
                        spine=spine,
                        category_id=blueprint.category_id,
                    )
                )
            elif normalized_cards:
                normalized_cards.append(
                    _duplicate_scene_card(
                        normalized_cards[-1],
                        index=index,
                        scene_count=scene_count,
                        spine=spine,
                    )
                )
            else:
                normalized_cards.append(
                    SceneCard(
                        scene=index + 1,
                        setting=spine.setting or "a cozy place",
                        scene_change=spine.central_problem or "a gentle shift in the moment",
                        paragraphs=[2 * index + 1, 2 * index + 2],
                        paragraph_beats=[
                            {
                                "paragraph": 2 * index + 1,
                                "function": "gentle_setup",
                                "must_show": ["the gentle moment began", "a small detail anchors the scene"],
                            },
                            {
                                "paragraph": 2 * index + 2,
                                "function": "gentle_continuation",
                                "must_show": ["the moment continued gently", "a quiet beat closes the moment"],
                            },
                        ],
                        dialogue=[],
                        end_with=spine.ending_image if index == scene_count - 1 else None,
                    )
                )
        blueprint.scene_cards = normalized_cards
    trace_event("pipeline.assemble_blueprint", category_id=blueprint.category_id, latency_ms=_latency_ms(start))
    return blueprint


def plan_blueprint(understanding: dict[str, Any]) -> StoryBlueprint:
    start = perf_counter()
    classification = understanding["classification"]
    scene_plan = scene_plan_for(classification.category_id)
    trace_event("agent.scene_plan", **scene_plan)
    trace_event("agent.character_designer.before_arc", category_id=classification.category_id)
    character_cards = design_characters(classification)
    interactive_categories = {"friendship_and_feelings", "silly_soft_story"}
    if classification.category_id in interactive_categories and len(character_cards) < 2:
        from story_engine.agents import _build_support_character

        support = _build_support_character(classification, existing_names={card.name for card in character_cards})
        character_cards.append(support)
        trace_event("agent.support_character_added", name=support.name, category_id=classification.category_id)
    trace_event("agent.arc_planner.after_character_designer", character_count=len(character_cards), category_id=classification.category_id)
    spine = plan_arc(classification, scene_plan, character_cards)
    scene_cards = plan_scenes(spine, character_cards, classification)
    blueprint = assemble_blueprint(classification, spine, character_cards, scene_cards, scene_plan)
    trace_event("agent.blueprint", scenes=len(blueprint.scene_cards), category_id=blueprint.category_id, latency_ms=_latency_ms(start))
    return blueprint
