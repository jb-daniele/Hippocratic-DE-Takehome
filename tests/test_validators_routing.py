import unittest

from _helpers import canonical_scene_cards, canonical_story_spine, varied_scene_paragraphs
from story_engine import agents
from story_engine.schemas import SCENE_FAIL_CODES


def _scene_body(scene_index, card):
    return "\n\n".join(varied_scene_paragraphs(scene_index, card)["paragraphs"])


class ValidateWrittenSceneTests(unittest.TestCase):
    def test_valid_scene_body_passes(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        self.assertEqual(agents.validate_written_scene(_scene_body(0, card), card), [])

    def test_missing_setting_yields_missing_setting_code(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        body = _scene_body(0, card).replace("Meadow", "Fieldless", 1)
        self.assertEqual(agents.validate_written_scene(body, card)[0]["code"], "missing_setting")

    def test_missing_first_paragraph_beat_includes_beat_text(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        body = _scene_body(0, card).replace("Ring", "Orbit", 1)
        failures = agents.validate_written_scene(body, card)
        self.assertEqual(failures[0]["evidence"], "ring-tag whirls around clover stones")

    def test_missing_dialogue_speaker_yields_missing_dialogue(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        body = _scene_body(0, card).replace("Sunny said", "He said")
        self.assertEqual(agents.validate_written_scene(body, card)[0]["code"], "missing_dialogue")

    def test_missing_end_with_tokens_yields_end_with_missing(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[3]
        body = _scene_body(3, card).rsplit(".", 1)[0] + "."
        body = body.replace("Sunny rests beside Lily in the clover while his gray pebble sits in the quiet game circle.", "The evening stayed quiet.")
        self.assertEqual(agents.validate_written_scene(body, card)[0]["code"], "end_with_missing")

    def test_extra_dialogue_yields_extra_dialogue(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[2]
        self.assertEqual(card.dialogue, [])
        body = _scene_body(2, card) + ' "I added a new line."'
        failures = agents.validate_written_scene(body, card)
        self.assertEqual(failures[0]["code"], "extra_dialogue")

    def test_emitted_codes_are_subset_of_scene_fail_codes(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        body = _scene_body(0, card).replace("Meadow", "Fieldless", 1).replace("Sunny said", "He said") + ' "Bonus line."'
        failures = agents.validate_written_scene(body, card)
        self.assertTrue({item["code"] for item in failures} <= SCENE_FAIL_CODES)
