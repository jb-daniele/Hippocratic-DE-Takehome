import unittest

from _helpers import canonical_scene_cards, canonical_story_spine
from story_engine.schemas import DialogueItem, ParagraphBeat, SceneCard, SchemaError


class SceneCardSchemaTests(unittest.TestCase):
    def test_constructs_with_required_fields(self):
        card = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0]
        self.assertIsInstance(card, SceneCard)

    def test_paragraphs_reject_one_item(self):
        payload = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0].to_dict()
        payload["paragraphs"] = [1]
        with self.assertRaises(SchemaError):
            SceneCard(**payload)

    def test_paragraphs_reject_three_items(self):
        payload = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0].to_dict()
        payload["paragraphs"] = [1, 2, 3]
        with self.assertRaises(SchemaError):
            SceneCard(**payload)

    def test_paragraph_beats_reject_one_item(self):
        payload = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0].to_dict()
        payload["paragraph_beats"] = payload["paragraph_beats"][:1]
        with self.assertRaises(SchemaError):
            SceneCard(**payload)

    def test_paragraph_beats_reject_three_items(self):
        payload = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0].to_dict()
        payload["paragraph_beats"] = payload["paragraph_beats"] + [payload["paragraph_beats"][0]]
        with self.assertRaises(SchemaError):
            SceneCard(**payload)

    def test_dialogue_rejects_more_than_two_items(self):
        payload = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0].to_dict()
        payload["dialogue"] = [
            {"speaker": "Sunny", "purpose": "one"},
            {"speaker": "Lily", "purpose": "two"},
            {"speaker": "Sunny", "purpose": "three"},
        ]
        with self.assertRaises(SchemaError):
            SceneCard(**payload)

    def test_dialogue_empty_list_is_accepted(self):
        payload = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0].to_dict()
        payload["dialogue"] = []
        self.assertEqual(SceneCard(**payload).dialogue, [])

    def test_dialogue_defaults_to_empty_list(self):
        payload = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0].to_dict()
        del payload["dialogue"]
        self.assertEqual(SceneCard(**payload).dialogue, [])

    def test_end_with_defaults_to_none(self):
        payload = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0].to_dict()
        del payload["end_with"]
        self.assertIsNone(SceneCard(**payload).end_with)

    def test_end_with_accepts_none(self):
        payload = canonical_scene_cards("friendship_and_feelings", canonical_story_spine("friendship_and_feelings"))[0].to_dict()
        payload["end_with"] = None
        self.assertIsNone(SceneCard(**payload).end_with)

    def test_paragraph_beat_requires_two_or_three_must_show_items(self):
        with self.assertRaises(SchemaError):
            ParagraphBeat(paragraph=1, function="Social Setup", must_show=["only one"])

    def test_paragraph_beat_rejects_four_must_show_items(self):
        with self.assertRaises(SchemaError):
            ParagraphBeat(paragraph=1, function="Social Setup", must_show=["one", "two", "three", "four"])

    def test_dialogue_item_requires_speaker(self):
        with self.assertRaises(SchemaError):
            DialogueItem(purpose="offers an easy first turn")

    def test_dialogue_item_requires_purpose(self):
        with self.assertRaises(SchemaError):
            DialogueItem(speaker="Lily")
