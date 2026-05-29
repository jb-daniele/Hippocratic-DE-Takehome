import unittest

from _helpers import canonical_scene_cards, canonical_story_spine, varied_scene_paragraphs
from story_engine import agents


class ExtraDialogueNarrowTests(unittest.TestCase):
    def test_no_dialogue_card_with_quote_emits_extra_dialogue_on_actual_quote(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[2]
        body = "\n\n".join(varied_scene_paragraphs(2, card)["paragraphs"]) + ' "I added a new line."'
        failures = agents.validate_written_scene(body, card)
        extra_dialogue = next(item for item in failures if item["code"] == "extra_dialogue")
        self.assertEqual(extra_dialogue["evidence"], '"I added a new line."')

    def test_dialogue_card_with_two_quotes_does_not_emit_extra_dialogue(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        body = "\n\n".join(varied_scene_paragraphs(0, card)["paragraphs"]) + ' "A second line appears."'
        failures = agents.validate_written_scene(body, card)
        self.assertNotIn("extra_dialogue", {item["code"] for item in failures})
