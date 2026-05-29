import unittest
from unittest.mock import patch

from _helpers import canonical_blueprint, varied_scene_paragraphs
from story_engine import agents, model_client
from story_engine.checks import calculate_word_count
from story_engine.schemas import DraftStory


def _stitch_failure(draft: DraftStory) -> dict:
    return {
        "boundary_indexes": [1],
        "seam_failures": [{"boundary_index": 1, "kind": "duplicate_adjacent_sentence", "evidence": "x"}],
        "expected_paragraph_count": len([paragraph for paragraph in draft.body.split("\n\n") if paragraph.strip()]),
    }


class StitcherTests(unittest.TestCase):
    def test_stitch_scenes_preserves_eight_paragraph_body_and_clears_scenes(self):
        blueprint = canonical_blueprint()
        scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
        body = "\n\n".join(scenes)
        draft = DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)
        with patch.object(model_client, "call_model_json", return_value={"body": draft.body}):
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(len([paragraph for paragraph in stitched.body.split("\n\n") if paragraph.strip()]), 8)
        self.assertEqual(stitched.scenes, [])

    def test_stitch_scenes_falls_back_to_original_body_when_too_short(self):
        blueprint = canonical_blueprint()
        scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
        body = "\n\n".join(scenes)
        draft = DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)
        with patch.object(model_client, "call_model_json", return_value={"body": "Only one paragraph."}):
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(stitched.body, draft.body)
        self.assertEqual(stitched.scenes, [])
