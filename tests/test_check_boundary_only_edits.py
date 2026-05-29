import unittest

from story_engine.checks import check_boundary_only_edits


SCENE_BOUNDARIES = [
    {"scene_number": 1, "start_paragraph": 1, "end_paragraph": 2},
    {"scene_number": 2, "start_paragraph": 3, "end_paragraph": 4},
    {"scene_number": 3, "start_paragraph": 5, "end_paragraph": 6},
    {"scene_number": 4, "start_paragraph": 7, "end_paragraph": 8},
]


def _body() -> str:
    return "\n\n".join(f"Paragraph {index} has stable words." for index in range(1, 9))


def _mutated_body(*indexes: int) -> str:
    paragraphs = _body().split("\n\n")
    for index in indexes:
        paragraphs[index - 1] = f"Paragraph {index} has changed words."
    return "\n\n".join(paragraphs)


class CheckBoundaryOnlyEditsTests(unittest.TestCase):
    def test_boundary_1_allows_paragraphs_2_and_3(self):
        self.assertTrue(check_boundary_only_edits(_body(), _mutated_body(2), [1], SCENE_BOUNDARIES)["ok"])
        self.assertTrue(check_boundary_only_edits(_body(), _mutated_body(3), [1], SCENE_BOUNDARIES)["ok"])
        result = check_boundary_only_edits(_body(), _mutated_body(4), [1], SCENE_BOUNDARIES)
        self.assertFalse(result["ok"])
        self.assertIn("non_boundary_paragraph_changed:4", result["issues"])

    def test_boundary_2_allows_paragraphs_4_and_5(self):
        self.assertTrue(check_boundary_only_edits(_body(), _mutated_body(4), [2], SCENE_BOUNDARIES)["ok"])
        self.assertTrue(check_boundary_only_edits(_body(), _mutated_body(5), [2], SCENE_BOUNDARIES)["ok"])
        for index in (3, 6):
            result = check_boundary_only_edits(_body(), _mutated_body(index), [2], SCENE_BOUNDARIES)
            self.assertFalse(result["ok"])
            self.assertIn(f"non_boundary_paragraph_changed:{index}", result["issues"])

    def test_boundary_3_allows_paragraphs_6_and_7(self):
        self.assertTrue(check_boundary_only_edits(_body(), _mutated_body(6), [3], SCENE_BOUNDARIES)["ok"])
        self.assertTrue(check_boundary_only_edits(_body(), _mutated_body(7), [3], SCENE_BOUNDARIES)["ok"])
        for index in (5, 8):
            result = check_boundary_only_edits(_body(), _mutated_body(index), [3], SCENE_BOUNDARIES)
            self.assertFalse(result["ok"])
            self.assertIn(f"non_boundary_paragraph_changed:{index}", result["issues"])

    def test_multiple_failed_boundaries_union_allowed_set(self):
        for index in (2, 3, 6, 7):
            self.assertTrue(check_boundary_only_edits(_body(), _mutated_body(index), [1, 3], SCENE_BOUNDARIES)["ok"])
        result = check_boundary_only_edits(_body(), _mutated_body(4), [1, 3], SCENE_BOUNDARIES)
        self.assertFalse(result["ok"])
        self.assertIn("non_boundary_paragraph_changed:4", result["issues"])

    def test_paragraph_count_mismatch_short_circuits(self):
        stitched = "\n\n".join(_body().split("\n\n")[:-1])
        result = check_boundary_only_edits(_body(), stitched, [1], SCENE_BOUNDARIES)
        self.assertEqual(result["issues"], ["paragraph_count_mismatch"])

    def test_whitespace_only_diff_in_non_boundary_paragraph_is_equal(self):
        paragraphs = _body().split("\n\n")
        paragraphs[3] = "Paragraph 4   has\nstable   words."
        result = check_boundary_only_edits(_body(), "\n\n".join(paragraphs), [1], SCENE_BOUNDARIES)
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
