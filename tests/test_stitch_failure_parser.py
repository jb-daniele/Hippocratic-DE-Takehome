import unittest

from _helpers import canonical_blueprint
from story_engine.prompts.scene_stitcher import build_prompt
from story_engine.agents.stitcher_failure import build_stitch_failure, parse_seam_issues


class StitchFailureParserTests(unittest.TestCase):
    def test_parse_seam_issues_maps_known_kinds(self):
        failures = parse_seam_issues(
            [
                "seam_a_1->_2: repeated sentence",
                "seam_b_2->_3: overlap tokens",
                "seam_c_3->_4: shared gram",
            ]
        )
        self.assertEqual(
            failures,
            [
                {"boundary_index": 1, "kind": "duplicate_adjacent_sentence", "evidence": "repeated sentence"},
                {"boundary_index": 2, "kind": "high_token_overlap", "evidence": "overlap tokens"},
                {"boundary_index": 3, "kind": "shared_five_gram", "evidence": "shared gram"},
            ],
        )

    def test_parse_seam_issues_skips_malformed_strings(self):
        failures = parse_seam_issues(["garbage", "seam_x_1->_2: foo", "seam_a_1->_2: kept"])
        self.assertEqual(failures, [{"boundary_index": 1, "kind": "duplicate_adjacent_sentence", "evidence": "kept"}])

    def test_build_stitch_failure_legacy_clean_seams_marks_all_boundaries(self):
        blueprint = canonical_blueprint()
        body = "\n\n".join(f"Paragraph {index}" for index in range(1, 9))
        stitch_failure = build_stitch_failure(
            {"ok": True, "severity": "none", "issues": [], "route": None},
            body,
            blueprint,
            legacy=True,
        )
        self.assertEqual(stitch_failure["boundary_indexes"], [1, 2, 3])
        self.assertTrue(all(failure["kind"] == "legacy_full_boundary_pass" for failure in stitch_failure["seam_failures"]))

    def test_build_stitch_failure_uses_actual_paragraph_count(self):
        blueprint = canonical_blueprint()
        body = "\n\n".join(f"Paragraph {index}" for index in range(1, 8))
        stitch_failure = build_stitch_failure(
            {"ok": False, "severity": "failure", "issues": ["seam_a_1->_2: x"], "route": "stitch"},
            body,
            blueprint,
        )
        self.assertEqual(stitch_failure["expected_paragraph_count"], 7)

    def test_build_prompt_rejects_mismatched_expected_paragraph_count(self):
        blueprint = canonical_blueprint()
        stitch_failure = {"boundary_indexes": [1], "seam_failures": [], "expected_paragraph_count": 7}
        with self.assertRaises(AssertionError):
            build_prompt(blueprint, "body", 4, [], stitch_failure, expected_paragraph_count=8)


if __name__ == "__main__":
    unittest.main()
