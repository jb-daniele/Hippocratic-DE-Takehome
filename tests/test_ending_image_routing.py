import unittest

from story_engine import pipeline
from story_engine.schemas import JudgeReport, PostDraftReport


def _ending_image_failure_report() -> PostDraftReport:
    return PostDraftReport(
        word_count=42,
        checks={
            "phrase_repetition": {"ok": True, "severity": "none", "issues": []},
            "ending_image": {
                "ok": False,
                "severity": "failure",
                "issues": ["final paragraph lacks ending image substance"],
                "revision_guidance": "Scene 4 must show the substance of story_spine.ending_image.",
            },
        },
        ok=False,
    )


class EndingImageRoutingTests(unittest.TestCase):
    def test_route_failure_buckets_maps_ending_image_to_scene_four(self):
        report = JudgeReport(judge_name="coherence_judge", verdict="pass", reason=None, revision_guidance=None, fail_codes=[])
        buckets = pipeline._route_failure_buckets([report], _ending_image_failure_report())
        self.assertEqual(len(buckets["scene"]), 1)
        self.assertEqual(buckets["scene"][0]["code"], "missing_ending_image")
        self.assertEqual(buckets["scene"][0]["scene_index"], 4)

    def test_aggregate_and_decide_blocks_approval_for_ending_image_only(self):
        report = JudgeReport(judge_name="coherence_judge", verdict="pass", reason=None, revision_guidance=None, fail_codes=[])
        decision = pipeline.aggregate_and_decide([report], _ending_image_failure_report())
        self.assertTrue(decision.all_pass)
        self.assertFalse(decision.approved)
