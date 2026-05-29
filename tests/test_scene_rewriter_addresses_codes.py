import unittest
from unittest.mock import patch

from _helpers import canonical_character_cards, canonical_scene_cards, canonical_story_spine, varied_scene_paragraphs
from story_engine import agents, model_client


class SceneRewriterAddressesCodesTests(unittest.TestCase):
    def test_missing_requested_address_code_retries_and_surfaces_residual_failures(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        payload = varied_scene_paragraphs(0, card)
        payload["paragraphs"][0] = payload["paragraphs"][0].replace("Meadow", "Fieldless", 1)
        response = {"paragraphs": payload["paragraphs"], "addresses_codes": ["missing_planned_beat"]}
        with patch.object(model_client, "call_model_json", side_effect=[response, response, response]) as mocked_call:
            rewritten = agents.rewrite_scene(
                card,
                "broken text",
                [{"code": "missing_setting", "evidence": "x"}, {"code": "missing_planned_beat", "evidence": "y"}],
                character_cards=canonical_character_cards(),
            )
        self.assertEqual(mocked_call.call_count, 3)
        self.assertEqual(rewritten["addresses_codes"], ["missing_planned_beat"])
        self.assertEqual(rewritten["residual_failures"][0]["code"], "missing_setting")
