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


class StitcherSingleAttemptTests(unittest.TestCase):
    def test_single_failure_returns_original_assembled_body(self):
        blueprint = canonical_blueprint()
        scenes = ["\n\n".join(varied_scene_paragraphs(index, card)["paragraphs"]) for index, card in enumerate(blueprint.scene_cards)]
        body = "\n\n".join(scenes)
        draft = DraftStory(title=blueprint.title, body=body, actual_word_count=calculate_word_count(body), scenes=scenes)
        with patch.object(model_client, "call_model_json", side_effect=RuntimeError("boom")) as mocked:
            stitched = agents.stitch_scenes(blueprint, draft, _stitch_failure(draft))
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(stitched.body, draft.body)
