import unittest

from _helpers import canonical_story_spine
from story_engine.schemas import SchemaError, StorySpine


class StorySpineSchemaTests(unittest.TestCase):
    def test_constructs_and_round_trips(self):
        spine = canonical_story_spine("friendship_and_feelings")
        self.assertEqual(StorySpine(**spine.to_dict()).to_dict(), spine.to_dict())

    def test_scene_count_must_equal_four(self):
        payload = canonical_story_spine("friendship_and_feelings").to_dict()
        payload["scene_count"] = 3
        with self.assertRaises(SchemaError):
            StorySpine(**payload)

    def test_scene_steps_must_have_four_items(self):
        payload = canonical_story_spine("friendship_and_feelings").to_dict()
        payload["scene_steps"] = payload["scene_steps"][:3]
        with self.assertRaises(SchemaError):
            StorySpine(**payload)

    def test_empty_setting_raises(self):
        payload = canonical_story_spine("friendship_and_feelings").to_dict()
        payload["setting"] = ""
        with self.assertRaises(SchemaError):
            StorySpine(**payload)

    def test_empty_resolution_raises(self):
        payload = canonical_story_spine("friendship_and_feelings").to_dict()
        payload["resolution"] = ""
        with self.assertRaises(SchemaError):
            StorySpine(**payload)

    def test_empty_ending_image_raises(self):
        payload = canonical_story_spine("friendship_and_feelings").to_dict()
        payload["ending_image"] = ""
        with self.assertRaises(SchemaError):
            StorySpine(**payload)

    def test_empty_must_avoid_is_accepted(self):
        payload = canonical_story_spine("friendship_and_feelings").to_dict()
        payload["must_avoid"] = []
        self.assertEqual(StorySpine(**payload).must_avoid, [])
