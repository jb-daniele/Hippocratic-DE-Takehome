import unittest
from unittest.mock import patch

from _helpers import canonical_character_cards, canonical_scene_cards, canonical_story_spine, varied_scene_paragraphs
from story_engine import agents, model_client


class SceneRewriterTests(unittest.TestCase):
    def test_rewrite_scene_returns_body_and_requested_codes(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        payload = varied_scene_paragraphs(0, card)
        with patch.object(
            model_client, "call_model_json",
            return_value={
                "paragraphs": payload["paragraphs"],
                "addresses_codes": ["missing_setting", "missing_planned_beat"],
            },
        ):
            rewritten = agents.rewrite_scene(
                card,
                "broken text",
                [{"code": "missing_setting", "evidence": "x"}, {"code": "missing_planned_beat", "evidence": "y"}],
                character_cards=canonical_character_cards(),
            )
        self.assertEqual(len([paragraph for paragraph in rewritten["body"].split("\n\n") if paragraph.strip()]), 2)
        self.assertEqual(rewritten["addresses_codes"], ["missing_setting", "missing_planned_beat"])
        self.assertEqual(rewritten["residual_failures"], [])

    def test_rewrite_scene_falls_back_to_requested_codes_when_missing(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        payload = varied_scene_paragraphs(0, card)
        with patch.object(model_client, "call_model_json", return_value={"paragraphs": payload["paragraphs"]}):
            rewritten = agents.rewrite_scene(
                card,
                "broken text",
                [{"code": "missing_setting", "evidence": "x"}, {"code": "missing_planned_beat", "evidence": "y"}],
                character_cards=canonical_character_cards(),
            )
        self.assertEqual(rewritten["addresses_codes"], ["missing_setting", "missing_planned_beat"])
        self.assertEqual(rewritten["residual_failures"], [])
