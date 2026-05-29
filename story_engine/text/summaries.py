from __future__ import annotations

from typing import Any


def _card_attr(card: Any, name: str, default: Any = "") -> Any:
    if isinstance(card, dict):
        return card.get(name, default)
    return getattr(card, name, default)


def already_written_summary(cards_done: list) -> str:
    entries: list[str] = []
    for card in cards_done:
        scene = _card_attr(card, "scene")
        scene_change = str(_card_attr(card, "scene_change", "")).rstrip(".")
        paragraph_beats = _card_attr(card, "paragraph_beats", []) or []
        dialogue = _card_attr(card, "dialogue", []) or []
        first_must_show = ""
        if paragraph_beats:
            beat = paragraph_beats[0]
            must_show = _card_attr(beat, "must_show", []) or []
            if must_show:
                first_must_show = str(must_show[0]).rstrip(".")
        entry = f"Scene {scene} already happened: {scene_change}. Main action: {first_must_show}."
        if dialogue:
            first_purpose = str(_card_attr(dialogue[0], "purpose", "")).rstrip(".")
            if first_purpose:
                entry += f" Dialogue: {first_purpose}."
        entries.append(entry)
    return " ".join(entries)


def upcoming_scene_summary(cards_future: list) -> str:
    entries: list[str] = []
    for card in cards_future:
        scene = _card_attr(card, "scene")
        scene_change = str(_card_attr(card, "scene_change", "")).rstrip(".")
        paragraph_beats = _card_attr(card, "paragraph_beats", []) or []
        first_must_show = ""
        if paragraph_beats:
            beat = paragraph_beats[0]
            must_show = _card_attr(beat, "must_show", []) or []
            if must_show:
                first_must_show = str(must_show[0]).rstrip(".")
        entries.append(f"Scene {scene}: {scene_change}. Main action: {first_must_show}.")
    return " ".join(entries)
