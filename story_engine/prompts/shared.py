from story_engine.categories import CATEGORIES


def category_writer_guidance(category_id: str) -> str:
    for category in CATEGORIES:
        if category["id"] == category_id:
            return str(category.get("writer_guidance", "")).strip()
    return ""
