from __future__ import annotations

from story_engine.schemas import DraftStory, StoryBlueprint


def split_scenes(body: str, blueprint: StoryBlueprint, draft: DraftStory | None = None) -> list[str]:
    if draft is not None and getattr(draft, "scenes", None):
        return list(draft.scenes)
    paragraphs = [paragraph.strip() for paragraph in body.split("\n\n") if paragraph.strip()]
    scene_count = blueprint.scene_plan["scene_count"]
    if scene_count <= 0:
        return []
    base, remainder = divmod(len(paragraphs), scene_count)
    sizes = [base + (1 if index < remainder else 0) for index in range(scene_count)]
    scenes: list[str] = []
    start = 0
    for size in sizes:
        if size <= 0:
            scenes.append("")
            continue
        scenes.append("\n\n".join(paragraphs[start:start + size]))
        start += size
    return scenes
