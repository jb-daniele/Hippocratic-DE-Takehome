import unittest

from story_engine import agents, pipeline
from story_engine.schemas import CoherenceFailCode, SchemaError


class CoherenceFailCodeTests(unittest.TestCase):
    def test_all_eight_codes_construct(self):
        for code in sorted(pipeline.ROUTE_BY_CODE):
            with self.subTest(code=code):
                fail_code = CoherenceFailCode(code=code, evidence="x", scene_index=None)
                self.assertEqual(fail_code.code, code)

    def test_invalid_code_raises(self):
        with self.assertRaises(SchemaError):
            CoherenceFailCode(code="not_a_code", evidence="x", scene_index=None)

    def test_route_by_code_maps_all_codes_to_scene(self):
        self.assertTrue(all(route == "scene" for route in pipeline.ROUTE_BY_CODE.values()))

    def test_whole_story_target_scene_matches_expected_mapping(self):
        self.assertEqual(
            pipeline.WHOLE_STORY_TARGET_SCENE,
            {"missing_resolution": 3, "missing_ending_image": 4, "unresolved_central_problem": 4},
        )

    def test_codes_without_explicit_mapping_default_later_in_repair(self):
        for code in {"request_drift", "ownership_drift", "continuity_break", "weak_scene_progression", "must_avoid_violation"}:
            with self.subTest(code=code):
                self.assertNotIn(code, pipeline.WHOLE_STORY_TARGET_SCENE)

    def test_coherence_parser_accepts_passing_payload(self):
        report = agents._coherence_from_response({"passed": True, "fail_codes": []})
        self.assertEqual(report.verdict, "pass")

    def test_coherence_parser_builds_failing_report(self):
        report = agents._coherence_from_response(
            {
                "passed": False,
                "fail_codes": [{"code": "request_drift", "evidence": "x", "scene_index": None}],
            }
        )
        self.assertEqual(report.fail_codes[0].code, "request_drift")
