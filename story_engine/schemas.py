from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, ClassVar


class SchemaError(ValueError):
    """Raised when a story engine schema receives malformed data."""


Validator = Callable[[Any, str], Any]


def _validate_type(value: Any, field: str, expected: type | tuple[type, ...]) -> Any:
    if not isinstance(value, expected):
        name = expected.__name__ if isinstance(expected, type) else " or ".join(t.__name__ for t in expected)
        raise SchemaError(f"{field} must be {name}")
    return value


def _string(value: Any, field: str) -> str:
    return _validate_type(value, field, str)


def _non_empty_string(value: Any, field: str) -> str:
    value = _string(value, field).strip()
    if not value:
        raise SchemaError(f"{field} must not be empty")
    return value


def _max_chars(limit: int, validator: Validator = _non_empty_string) -> Validator:
    def validate(value: Any, field: str) -> str:
        value = validator(value, field)
        if len(value) > limit:
            raise SchemaError(f"{field} must be <= {limit} chars")
        return value

    return validate


def _optional_max_chars(limit: int, validator: Validator = _non_empty_string) -> Validator:
    def validate(value: Any, field: str) -> str | None:
        if value is None:
            return None
        return _max_chars(limit, validator)(value, field)

    return validate


def _enum(options: set[str]) -> Validator:
    def validate(value: Any, field: str) -> str:
        value = _non_empty_string(value, field)
        if value not in options:
            raise SchemaError(f"{field} must be one of: {', '.join(sorted(options))}")
        return value

    return validate


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise SchemaError(f"{field} must be bool")
    return value


def _int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaError(f"{field} must be int")
    return value


def _optional_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    return _int(value, field)


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _dict(value: Any, field: str) -> dict[str, Any]:
    return _validate_type(value, field, dict)


def _any(value: Any, field: str) -> Any:
    return value


def _list_of(item_validator: Validator) -> Validator:
    def validate(value: Any, field: str) -> list[Any]:
        if not isinstance(value, list):
            raise SchemaError(f"{field} must be list")
        return [item_validator(item, f"{field}[{index}]") for index, item in enumerate(value)]

    return validate


def _scene_plan(value: Any, field: str) -> dict[str, int]:
    data = _dict(value, field)
    scene_count = _int(data.get("scene_count"), f"{field}.scene_count")
    paragraphs_per_scene = _int(data.get("paragraphs_per_scene"), f"{field}.paragraphs_per_scene")
    if scene_count < 3 or scene_count > 5:
        raise SchemaError(f"{field}.scene_count must be between 3 and 5")
    if paragraphs_per_scene < 1:
        raise SchemaError(f"{field}.paragraphs_per_scene must be positive")
    return {"scene_count": scene_count, "paragraphs_per_scene": paragraphs_per_scene}


def _confidence(value: Any, field: str) -> str:
    value = _string(value, field)
    if value not in {"high", "medium", "low"}:
        raise SchemaError(f"{field} must be one of: high, medium, low")
    return value


def _judge_verdict(value: Any, field: str) -> str:
    value = _string(value, field)
    if value not in {"pass", "fail", "unknown"}:
        raise SchemaError(f"{field} must be pass, fail, or unknown")
    return value


def _schema_validator(schema_type: type[StrictSchema]) -> Validator:
    def validate(value: Any, field: str) -> StrictSchema:
        if isinstance(value, schema_type):
            return value
        if isinstance(value, dict):
            return schema_type(**value)
        raise SchemaError(f"{field} must be {schema_type.__name__}")

    return validate


def _coherence_fail_code(value: Any, field: str) -> StrictSchema:
    if isinstance(value, CoherenceFailCode):
        return value
    if isinstance(value, dict):
        return CoherenceFailCode(**value)
    raise SchemaError(f"{field} must be CoherenceFailCode")


# MainCharacter is defined later; this validator resolves that name only when called.
def _main_character(value: Any, field: str) -> StrictSchema:
    if isinstance(value, str):
        return MainCharacter(name=value, role="main")
    if isinstance(value, MainCharacter):
        return value
    if isinstance(value, dict):
        return MainCharacter(**value)
    raise SchemaError(f"{field} must be MainCharacter")


def _character_card(value: Any, field: str) -> StrictSchema:
    if isinstance(value, CharacterCard):
        return value
    if isinstance(value, dict):
        return CharacterCard(**value)
    raise SchemaError(f"{field} must be CharacterCard")


def _story_spine(value: Any, field: str) -> StrictSchema:
    if isinstance(value, StorySpine):
        return value
    if isinstance(value, dict):
        return StorySpine(**value)
    raise SchemaError(f"{field} must be StorySpine")


def _scene_card(value: Any, field: str) -> StrictSchema:
    if isinstance(value, SceneCard):
        return value
    if isinstance(value, dict):
        return SceneCard(**value)
    raise SchemaError(f"{field} must be SceneCard")


def _plain(value: Any) -> Any:
    if isinstance(value, StrictSchema):
        return value.to_dict()
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_plain(item) for item in value)
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


class StrictSchema:
    _fields: ClassVar[dict[str, Validator]] = {}
    _defaults: ClassVar[dict[str, Any]] = {}
    _ignored_fields: ClassVar[set[str]] = set()

    def __init__(self, **kwargs: Any) -> None:
        unknown = set(kwargs) - set(self._fields) - set(self._ignored_fields)
        if unknown:
            raise SchemaError(f"{self.__class__.__name__} got unexpected field(s): {', '.join(sorted(unknown))}")

        object.__setattr__(self, "_initializing", True)
        for field, validator in self._fields.items():
            if field in kwargs:
                value = kwargs[field]
            elif field in self._defaults:
                value = deepcopy(self._defaults[field])
            else:
                raise SchemaError(f"{self.__class__.__name__} missing required field: {field}")
            object.__setattr__(self, field, validator(value, field))
        object.__setattr__(self, "_initializing", False)

    def __setattr__(self, field: str, value: Any) -> None:
        if field.startswith("_"):
            object.__setattr__(self, field, value)
            return
        if field not in self._fields:
            raise SchemaError(f"{self.__class__.__name__} got unexpected field: {field}")
        object.__setattr__(self, field, self._fields[field](value, field))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrictSchema:
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return {field: _plain(getattr(self, field)) for field in self._fields}

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, StrictSchema):
            return self.to_dict() == other.to_dict()
        if isinstance(other, dict):
            return self.to_dict() == other
        return False

    def __repr__(self) -> str:
        fields = ", ".join(f"{key}={value!r}" for key, value in self.to_dict().items())
        return f"{self.__class__.__name__}({fields})"


class RequestOptions(StrictSchema):
    _fields = {
        "story_mode": _non_empty_string,
        "main_character_name": _string,
    }


class MainCharacter(StrictSchema):
    _fields = {
        "name": _non_empty_string,
        "role": _non_empty_string,
    }


class CharacterCard(StrictSchema):
    _fields = {
        "name": _max_chars(30),
        "pronouns": _enum({"she/her", "he/him", "they/them"}),
        "kind": _max_chars(30),
        "role": _max_chars(80),
    }

    @property
    def gender(self) -> str:
        return {"she/her": "female", "he/him": "male", "they/them": "neutral"}[self.pronouns]

class RequestClassification(StrictSchema):
    _fields = {
        "request_text": _non_empty_string,
        "selected_story_mode": _non_empty_string,
        "main_character_name": _string,
        "category_id": _non_empty_string,
        "category_display_name": _non_empty_string,
        "classifier_confidence": _confidence,
        "classifier_rationale": _non_empty_string,
        "matched_signals": _list_of(_non_empty_string),
        "fallback": _bool,
        "classifier_skipped": _bool,
        "main_characters": _list_of(_main_character),
    }


class SafetyAssessment(StrictSchema):
    _fields = {
        "allowed": _bool,
        "redirected_request": _string,
        "reason": _string,
    }


class StorySpine(StrictSchema):
    _fields = {
        "story_premise": _max_chars(200),
        "protagonist_name": _max_chars(60),
        "setting": _max_chars(120),
        "central_problem": _max_chars(220),
        "resolution": _max_chars(220),
        "ending_image": _max_chars(220),
        "scene_count": _int,
        "scene_steps": _list_of(_max_chars(240)),
        "must_avoid": _list_of(_max_chars(120)),
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if self.scene_count != 4:
            raise SchemaError("scene_count must equal 4")
        if len(self.scene_steps) != 4:
            raise SchemaError("scene_steps must contain exactly 4 items")
        if len(self.must_avoid) > 5:
            raise SchemaError("must_avoid must contain at most 5 items")


class ParagraphBeat(StrictSchema):
    _fields = {
        "paragraph": _int,
        "function": _max_chars(80),
        "must_show": _list_of(_max_chars(240)),
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if len(self.must_show) not in {2, 3}:
            raise SchemaError("must_show must contain exactly 2 or 3 items")


class DialogueItem(StrictSchema):
    _fields = {
        "speaker": _non_empty_string,
        "purpose": _max_chars(160),
    }


def _paragraph_beat(value: Any, field: str) -> StrictSchema:
    if isinstance(value, ParagraphBeat):
        return value
    if isinstance(value, dict):
        return ParagraphBeat(**value)
    raise SchemaError(f"{field} must be ParagraphBeat")


def _dialogue_item(value: Any, field: str) -> StrictSchema:
    if isinstance(value, DialogueItem):
        return value
    if isinstance(value, dict):
        return DialogueItem(**value)
    raise SchemaError(f"{field} must be DialogueItem")


class SceneCard(StrictSchema):
    _fields = {
        "scene": _int,
        "paragraphs": _list_of(_int),
        "setting": _max_chars(120),
        "scene_change": _max_chars(220),
        "paragraph_beats": _list_of(_paragraph_beat),
        "dialogue": _list_of(_dialogue_item),
        "end_with": _optional_max_chars(260),
    }
    _defaults = {
        "dialogue": [],
        "end_with": None,
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if len(self.paragraphs) != 2:
            raise SchemaError("paragraphs must contain exactly 2 items")
        if len(self.paragraph_beats) != 2:
            raise SchemaError("paragraph_beats must contain exactly 2 items")
        if len(self.dialogue) > 2:
            raise SchemaError("dialogue must contain at most 2 items")


class StoryBlueprint(StrictSchema):
    _fields = {
        "title": _non_empty_string,
        "category_id": _non_empty_string,
        "category_display_name": _non_empty_string,
        "selected_story_mode": _non_empty_string,
        "main_characters": _list_of(_non_empty_string),
        "character_cards": _list_of(_character_card),
        "scene_plan": _scene_plan,
        "story_spine": _story_spine,
        "scene_cards": _list_of(_scene_card),
    }
    _defaults = {
        "character_cards": [],
        "selected_story_mode": "auto_detect",
    }

    def __init__(self, **kwargs: Any) -> None:
        if "scene_plan" not in kwargs and "story_spine" in kwargs:
            kwargs["scene_plan"] = {"scene_count": 4, "paragraphs_per_scene": 2}
        super().__init__(**kwargs)


class DraftStory(StrictSchema):
    _fields = {
        "title": _non_empty_string,
        "body": _non_empty_string,
        "actual_word_count": _int,
        "scenes": _list_of(_string),
    }
    _defaults = {"scenes": []}


class CoherenceFailCode(StrictSchema):
    """scene_index is a 1-indexed scene number (1-4); None means whole-story."""

    _fields = {
        "code": _enum(
            {
                "request_drift",
                "ownership_drift",
                "continuity_break",
                "weak_scene_progression",
                "unresolved_central_problem",
                "missing_resolution",
                "missing_ending_image",
                "must_avoid_violation",
            }
        ),
        "evidence": _max_chars(120),
        "scene_index": _optional_int,
    }


SCENE_FAIL_CODES = frozenset(
    {
        "paragraph_count_invalid",
        "missing_setting",
        "missing_planned_beat",
        "missing_dialogue",
        "extra_dialogue",
        "end_with_missing",
    }
)


class JudgeReport(StrictSchema):
    _fields = {
        "verdict": _judge_verdict,
        "reason": _optional_string,
        "revision_guidance": _optional_string,
        "judge_name": _non_empty_string,
        "fail_codes": _list_of(_coherence_fail_code),
    }
    _defaults = {"fail_codes": []}


class JudgeDecision(StrictSchema):
    _fields = {
        "all_pass": _bool,
        "failures": _list_of(_any),
        "deterministic_failures": _list_of(_any),
        "approved": _bool,
    }
    _defaults = {"deterministic_failures": []}


class RevisionPlan(StrictSchema):
    _fields = {
        "must_fix": _list_of(_non_empty_string),
        "revision_guidance_hints": _list_of(_non_empty_string),
        "preserve": _list_of(_non_empty_string),
    }


class FinalStoryPackage(StrictSchema):
    _fields = {
        "request": _schema_validator(RequestOptions),
        "classification": _schema_validator(RequestClassification),
        "blueprint": _schema_validator(StoryBlueprint),
        "story": _schema_validator(DraftStory),
        "judge_decision": _schema_validator(JudgeDecision),
        "judge_trail": _list_of(_any),
        "revision_plans": _list_of(_any),
        "warnings": _list_of(_non_empty_string),
        "iterations_used": _int,
        "approved": _bool,
        "remix_source": _optional_string,
        "cover": _dict,
        "actual_word_count": _int,
        "page_break_suggestions": _list_of(_int),
        "pages": _list_of(_non_empty_string),
    }
    _defaults = {
        "revision_plans": [],
        "warnings": [],
        "iterations_used": 0,
        "approved": False,
        "remix_source": None,
    }


class PostDraftReport(StrictSchema):
    _fields = {
        "word_count": _int,
        "checks": _dict,
        "ok": _bool,
    }


def validate_category_id(category_id: str) -> bool:
    from story_engine.categories import CATEGORIES

    if not isinstance(category_id, str):
        return False
    return category_id in {category["id"] for category in CATEGORIES}
