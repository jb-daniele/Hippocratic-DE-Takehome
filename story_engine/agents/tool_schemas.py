from __future__ import annotations

from story_engine.categories import CATEGORIES
from story_engine.prompts.language_judge import LANGUAGE_JUDGE_FAILURE_CODES


_CATEGORY_IDS = [category["id"] for category in CATEGORIES]
_COHERENCE_FAIL_CODES = [
    "request_drift",
    "ownership_drift",
    "continuity_break",
    "weak_scene_progression",
    "unresolved_central_problem",
    "missing_resolution",
    "missing_ending_image",
    "must_avoid_violation",
]


# Mirror of classifier._OUTPUT_SCHEMA and RequestClassification.
CLASSIFICATION_TOOL_NAME = "submit_classification"
CLASSIFICATION_TOOL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["category_id", "confidence", "rationale", "matched_signals", "fallback"],
    "properties": {
        "category_id": {"type": "string", "enum": _CATEGORY_IDS},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "rationale": {"type": "string", "minLength": 1},
        "matched_signals": {"type": "array", "items": {"type": "string"}},
        "fallback": {"type": "boolean"},
    },
}


# Mirror of character_designer._OUTPUT_SCHEMA and CharacterCard.
CHARACTER_CARDS_TOOL_NAME = "submit_character_cards"
CHARACTER_CARDS_TOOL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["cast"],
    "properties": {
        "cast": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "pronouns", "kind", "role"],
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 30},
                    "pronouns": {"type": "string", "enum": ["she/her", "he/him", "they/them"]},
                    "kind": {"type": "string", "minLength": 1, "maxLength": 30},
                    "role": {"type": "string", "minLength": 1, "maxLength": 80},
                },
            },
        }
    },
}


# Mirror of arc_planner._OUTPUT_SCHEMA and StorySpine.
STORY_SPINE_TOOL_NAME = "submit_story_spine"
STORY_SPINE_TOOL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "story_premise",
        "protagonist_name",
        "setting",
        "central_problem",
        "resolution",
        "ending_image",
        "scene_count",
        "scene_steps",
        "must_avoid",
    ],
    "properties": {
        "story_premise": {"type": "string", "minLength": 1, "maxLength": 200},
        "protagonist_name": {"type": "string", "minLength": 1, "maxLength": 60},
        "setting": {"type": "string", "minLength": 1, "maxLength": 120},
        "central_problem": {"type": "string", "minLength": 1, "maxLength": 220},
        "resolution": {"type": "string", "minLength": 1, "maxLength": 220},
        "ending_image": {"type": "string", "minLength": 1, "maxLength": 220},
        "scene_count": {"type": "integer", "enum": [4]},
        "scene_steps": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {"type": "string", "minLength": 1, "maxLength": 240},
        },
        "must_avoid": {
            "type": "array",
            "maxItems": 5,
            "items": {"type": "string", "minLength": 1, "maxLength": 120},
        },
    },
}


# Mirror of scene_planner._OUTPUT_SCHEMA and SceneCard.
SCENE_CARDS_TOOL_NAME = "submit_scene_cards"
SCENE_CARDS_TOOL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["scene_cards"],
    "properties": {
        "scene_cards": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["scene", "paragraphs", "setting", "scene_change", "paragraph_beats", "dialogue", "end_with"],
                "properties": {
                    "scene": {"type": "integer"},
                    "paragraphs": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": {"type": "integer"},
                    },
                    "setting": {"type": "string", "minLength": 1, "maxLength": 120},
                    "scene_change": {"type": "string", "minLength": 1, "maxLength": 220},
                    "paragraph_beats": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["paragraph", "function", "must_show"],
                            "properties": {
                                "paragraph": {"type": "integer"},
                                "function": {"type": "string", "minLength": 1, "maxLength": 80},
                                "must_show": {
                                    "type": "array",
                                    "minItems": 2,
                                    "maxItems": 3,
                                    "items": {"type": "string", "minLength": 1, "maxLength": 240},
                                },
                            },
                        },
                    },
                    "dialogue": {
                        "type": "array",
                        "maxItems": 2,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["speaker", "purpose"],
                            "properties": {
                                "speaker": {"type": "string"},
                                "purpose": {"type": "string", "minLength": 1, "maxLength": 160},
                            },
                        },
                    },
                    "end_with": {"type": ["string", "null"], "maxLength": 260},
                },
            },
        }
    },
}


# Mirror of coherence_judge._OUTPUT_SCHEMA and CoherenceFailCode.
COHERENCE_JUDGMENT_TOOL_NAME = "submit_coherence_judgment"
COHERENCE_JUDGMENT_TOOL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["passed", "fail_codes"],
    "properties": {
        "passed": {"type": "boolean"},
        "fail_codes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "evidence", "scene_index"],
                "properties": {
                    "code": {"type": "string", "enum": _COHERENCE_FAIL_CODES},
                    "evidence": {"type": "string", "minLength": 1, "maxLength": 120},
                    "scene_index": {"type": ["integer", "null"]},
                },
            },
        },
    },
}


# Mirror of safety_judge._OUTPUT_SCHEMA and JudgeReport.
SAFETY_JUDGMENT_TOOL_NAME = "submit_safety_judgment"
SAFETY_JUDGMENT_TOOL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["judge_name", "verdict", "reason", "revision_guidance"],
    "properties": {
        "judge_name": {"type": "string", "enum": ["safety_judge"]},
        "verdict": {"type": "string", "enum": ["pass", "fail"]},
        "reason": {"type": ["string", "null"]},
        "revision_guidance": {"type": ["string", "null"]},
    },
}


LANGUAGE_JUDGMENT_TOOL_NAME = "submit_language_judgment"
LANGUAGE_JUDGMENT_TOOL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verdict", "failures"],
    "properties": {
        "verdict": {"type": "string", "enum": ["pass", "fail"]},
        "failures": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "evidence", "revision_guidance"],
                "properties": {
                    "code": {"type": "string", "enum": LANGUAGE_JUDGE_FAILURE_CODES},
                    "evidence": {"type": "string", "maxLength": 120},
                    "revision_guidance": {"type": "string", "minLength": 1},
                },
            },
        },
    },
}


# Mirror of title_writer._OUTPUT_SCHEMA and title rules.
TITLE_TOOL_NAME = "submit_title"
TITLE_TOOL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title"],
    "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 80},
    },
}
