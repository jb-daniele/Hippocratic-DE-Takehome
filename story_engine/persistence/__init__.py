"""Story persistence helpers."""

from .store import (
    load_for_read,
    load_for_remix,
    persist_story,
    record_user_rating,
    run_id_for,
)


def ensure_seed_examples() -> None:
    from story_engine.persistence.seeds import ensure_seed_examples as _ensure_seed_examples

    _ensure_seed_examples()
