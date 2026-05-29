from __future__ import annotations

import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, canonical_character_cards, canonical_classification, canonical_story_spine, varied_scene_paragraphs
from story_engine import agents, model_client
from story_engine.agents.tool_schemas import (
    CHARACTER_CARDS_TOOL_NAME,
    CLASSIFICATION_TOOL_NAME,
    COHERENCE_JUDGMENT_TOOL_NAME,
    SAFETY_JUDGMENT_TOOL_NAME,
    SCENE_CARDS_TOOL_NAME,
    STORY_SPINE_TOOL_NAME,
    TITLE_TOOL_NAME,
)
from story_engine.checks import calculate_word_count
from story_engine.schemas import DraftStory


def _draft_from_blueprint():
    blueprint = canonical_blueprint()
    scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
    body = "\n\n".join(scenes)
    draft = DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)
    return blueprint, draft


class AgentToolWiringTests(unittest.TestCase):
    def test_classify_request_calls_tool_and_retries_on_enum_violation(self) -> None:
        bad = {
            "category_id": "friendship_and_feelings",
            "confidence": "certain",
            "rationale": "test fixture",
            "matched_signals": ["user_selection"],
            "fallback": False,
        }
        good = {
            "category_id": "friendship_and_feelings",
            "confidence": "high",
            "rationale": "test fixture",
            "matched_signals": ["user_selection"],
            "fallback": False,
        }
        with patch.object(model_client, "call_model_tool", side_effect=[bad, good]) as call_mock:
            result = agents.classify_request("A gentle sleepy story with a question and a friend.", "auto_detect")

        self.assertEqual(result.category_id, "friendship_and_feelings")
        self.assertEqual(call_mock.call_args_list[0].kwargs["tool_name"], CLASSIFICATION_TOOL_NAME)
        self.assertEqual(call_mock.call_count, 2)

    def test_design_characters_calls_tool_and_retries_on_extra_field(self) -> None:
        classification = canonical_classification()
        valid_cards = [card.to_dict() for card in canonical_character_cards()]
        bad_cards = [dict(valid_cards[0], alias="Sunny"), valid_cards[1]]
        with patch.object(model_client, "call_model_tool", side_effect=[{"cast": bad_cards}, {"cast": valid_cards}]) as call_mock:
            result = agents.design_characters(classification)

        self.assertEqual([card.name for card in result], ["Sunny", "Lily"])
        self.assertEqual(call_mock.call_args_list[0].kwargs["tool_name"], CHARACTER_CARDS_TOOL_NAME)
        self.assertEqual(call_mock.call_count, 2)

    def test_plan_arc_calls_tool_and_retries_on_extra_field(self) -> None:
        classification = canonical_classification()
        scene_plan = {"scene_count": 4, "paragraphs_per_scene": 2}
        good = canonical_story_spine("friendship_and_feelings").to_dict()
        bad = dict(good, extra="not allowed")
        with patch.object(model_client, "call_model_tool", side_effect=[bad, good]) as call_mock:
            result = agents.plan_arc(classification, scene_plan, canonical_character_cards())

        self.assertEqual(result.scene_count, 4)
        self.assertEqual(call_mock.call_args_list[0].kwargs["tool_name"], STORY_SPINE_TOOL_NAME)
        self.assertEqual(call_mock.call_count, 2)

    def test_plan_scenes_calls_tool_and_retries_on_unknown_speaker(self) -> None:
        classification = canonical_classification()
        spine = canonical_story_spine("friendship_and_feelings")
        characters = canonical_character_cards()
        good_cards = [card.to_dict() for card in canonical_blueprint().scene_cards]
        bad_cards = [card.copy() for card in good_cards]
        bad_cards[0]["dialogue"] = [{"speaker": "Ghost", "purpose": "offers help"}]
        with patch.object(model_client, "call_model_tool", side_effect=[{"scene_cards": bad_cards}, {"scene_cards": good_cards}]) as call_mock:
            result = agents.plan_scenes(spine, characters, classification)

        self.assertEqual(result[0].dialogue[0].speaker, "Sunny")
        self.assertEqual(call_mock.call_args_list[0].kwargs["tool_name"], SCENE_CARDS_TOOL_NAME)
        self.assertEqual(call_mock.call_count, 2)
        self.assertIn("card_unknown_speaker", call_mock.call_args_list[1].args[0])

    def test_write_title_calls_tool_and_retries_on_missing_required_field(self) -> None:
        blueprint = canonical_blueprint()
        with patch.object(model_client, "call_model_tool", side_effect=[{}, {"title": "Sunny and the Clover Circle"}]) as call_mock:
            title = agents.write_title(blueprint)

        self.assertEqual(title, "Sunny and the Clover Circle")
        self.assertEqual(call_mock.call_args_list[0].kwargs["tool_name"], TITLE_TOOL_NAME)
        self.assertEqual(call_mock.call_count, 2)

    def test_judge_coherence_calls_tool_and_retries_on_cross_field_failure(self) -> None:
        blueprint, draft = _draft_from_blueprint()
        classification = canonical_classification()
        with patch.object(
            model_client, "call_model_tool",
            side_effect=[
                {"passed": True, "fail_codes": [{"code": "request_drift", "evidence": "x", "scene_index": None}]},
                {"passed": True, "fail_codes": []},
            ],
        ) as call_mock:
            report = agents.judge_coherence(draft, blueprint, classification, classification.request_text)

        self.assertEqual(report.verdict, "pass")
        self.assertEqual(call_mock.call_args_list[0].kwargs["tool_name"], COHERENCE_JUDGMENT_TOOL_NAME)
        self.assertEqual(call_mock.call_count, 2)

    def test_judge_safety_calls_tool_and_retries_on_cross_field_failure(self) -> None:
        blueprint, draft = _draft_from_blueprint()
        classification = canonical_classification()
        with patch.object(
            model_client, "call_model_tool",
            side_effect=[
                {"judge_name": "safety_judge", "verdict": "pass", "reason": "too much", "revision_guidance": None},
                {"judge_name": "safety_judge", "verdict": "pass", "reason": None, "revision_guidance": None},
            ],
        ) as call_mock:
            report = agents.judge_safety(draft, blueprint, classification, classification.request_text)

        self.assertEqual(report.verdict, "pass")
        self.assertEqual(call_mock.call_args_list[0].kwargs["tool_name"], SAFETY_JUDGMENT_TOOL_NAME)
        self.assertEqual(call_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
