import unittest

from _helpers import canonical_blueprint, varied_scene_paragraphs
from story_engine import checks
from story_engine.checks import calculate_word_count
from story_engine.schemas import DraftStory


class CheckEndingImageTests(unittest.TestCase):
    def test_absent_tokens_fail(self):
        blueprint = canonical_blueprint()
        scenes = [varied_scene_paragraphs(index, card)["paragraphs"][:] for index, card in enumerate(blueprint.scene_cards)]
        scenes[-1][-1] = "The evening stayed quiet and plain."
        flattened = ["\n\n".join(scene) for scene in scenes]
        body = "\n\n".join(flattened)
        draft = DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=flattened)
        result = checks.check_ending_image(draft, blueprint)
        self.assertFalse(result["ok"])

    def test_present_tokens_pass(self):
        blueprint = canonical_blueprint()
        scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
        body = "\n\n".join(scenes)
        draft = DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)
        result = checks.check_ending_image(draft, blueprint)
        self.assertTrue(result["ok"])
