from __future__ import annotations

from time import perf_counter
from typing import Any

from story_engine import checks
from story_engine.agents import write_title
from story_engine.schemas import DraftStory, FinalStoryPackage, JudgeDecision, JudgeReport, RequestClassification, RequestOptions, StoryBlueprint
from story_engine.text import reader
from story_engine.trace import event as trace_event

from ._common import _latency_ms

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


def _apply_title(draft: DraftStory, blueprint: StoryBlueprint) -> DraftStory:
    title = write_title(blueprint)
    # Keep later revision prompts and saved blueprint metadata aligned with the visible title.
    blueprint.title = title
    return DraftStory(title=title, body=draft.body, actual_word_count=draft.actual_word_count, scenes=[])


def _package(
    request_options: RequestOptions,
    classification: RequestClassification,
    blueprint: StoryBlueprint,
    draft: DraftStory,
    post_draft_report,
    judge_trail: list[list[dict[str, Any]]],
    judge_decision: JudgeDecision,
    revision_plans: list[dict[str, Any]],
    warnings: list[str],
    iterations_used: int,
    remix_source: str | None = None,
) -> FinalStoryPackage:
    start = perf_counter()
    pages = reader.paginate(draft.body)
    page_break_suggestions = _page_break_suggestions(pages)
    cover = _cover(classification, blueprint, draft.actual_word_count, pages)
    cover["post_draft_report"] = post_draft_report.to_dict()
    cover["category_display_name_chip"] = classification.category_display_name
    cover["fallback"] = classification.fallback
    cover["classifier_skipped"] = classification.classifier_skipped
    if remix_source:
        cover["remix_source"] = remix_source
    package = FinalStoryPackage(
        request=request_options,
        classification=classification,
        blueprint=blueprint,
        story=draft,
        judge_decision=judge_decision,
        judge_trail=judge_trail,
        revision_plans=revision_plans,
        warnings=warnings,
        iterations_used=iterations_used,
        approved=judge_decision.approved,
        remix_source=remix_source,
        cover=cover,
        actual_word_count=draft.actual_word_count,
        page_break_suggestions=page_break_suggestions,
        pages=pages,
    )
    trace_event("pipeline.package", pages=len(package.pages), actual_word_count=package.actual_word_count, latency_ms=_latency_ms(start))
    return package
