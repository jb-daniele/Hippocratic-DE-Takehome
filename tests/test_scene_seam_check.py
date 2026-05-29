import unittest

from story_engine import checks


class SceneSeamCheckTests(unittest.TestCase):
    def test_detector_a_passes_when_adjacent_sentences_differ(self):
        result = checks.check_scene_seams([["Lantern light stayed low."], ["Morning birds began softly."]], blueprint=None)
        self.assertTrue(result["ok"])

    def test_detector_a_fails_on_exact_duplicate_adjacent_sentence(self):
        result = checks.check_scene_seams([["Lantern light stayed low. Quiet steps followed."], ["Quiet steps followed! Morning birds began softly."]], blueprint=None)
        self.assertFalse(result["ok"])
        self.assertIn("seam_a_1->_2", result["issues"][0])

    def test_detector_b_passes_below_overlap_threshold(self):
        result = checks.check_scene_seams([["Sunny carried a smooth stone toward the gate."], ["Lily opened a bright basket near the hedge."]], blueprint=None)
        self.assertTrue(result["ok"])

    def test_detector_b_fails_on_high_overlap_sentence(self):
        result = checks.check_scene_seams([["Sunny carried the smooth stone beside the hedge path."], ["Sunny carried smooth stone beside hedge path today."]], blueprint=None)
        self.assertFalse(result["ok"])
        self.assertTrue(any(issue.startswith("seam_b_1->_2:") for issue in result["issues"]))

    def test_detector_c_passes_without_shared_five_gram(self):
        result = checks.check_scene_seams([["Sunny counted soft clover leaves beside the warm fence post."], ["Lily stacked bright teacups near the shaded garden bench."]], blueprint=None)
        self.assertTrue(result["ok"])

    def test_detector_c_fails_on_shared_five_gram_across_seam(self):
        result = checks.check_scene_seams(
            [
                ["Sunny counted soft clover leaves beside the warm fence post before supper."],
                ["Soft clover leaves beside the warm fence shimmered after supper."],
            ],
            blueprint=None,
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any(issue.startswith("seam_c_1->_2:") for issue in result["issues"]))
