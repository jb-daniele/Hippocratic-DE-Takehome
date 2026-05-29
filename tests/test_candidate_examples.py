import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from story_engine.persistence import candidate_examples, store


class CandidateExamplesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stories_dir = self.root / "stories"
        self.candidates_dir = self.root / "data" / "prompt_example_candidates"
        self.index_jsonl = self.stories_dir / "index.jsonl"
        self.index_html = self.stories_dir / "index.html"
        self.patchers = [
            patch("story_engine.config.STORIES_DIR", self.stories_dir),
            patch("story_engine.config.PROMPT_EXAMPLE_CANDIDATES_DIR", self.candidates_dir),
            patch("story_engine.persistence.store.STORIES_DIR", self.stories_dir),
            patch("story_engine.persistence.store.INDEX_JSONL", self.index_jsonl),
            patch("story_engine.persistence.store.INDEX_HTML", self.index_html),
            patch("story_engine.persistence.candidate_examples.STORIES_DIR", self.stories_dir),
            patch("story_engine.persistence.candidate_examples.PROMPT_EXAMPLE_CANDIDATES_DIR", self.candidates_dir),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.tmp.cleanup()

    def _write_story_json(
        self,
        run_id="20260528T010203000000Z-gentle-test",
        *,
        title="The Lantern Path",
        body="A warm beginning.\nA brave ending.",
        blueprint=None,
        request_text="Tell a gentle adventure.",
        category_id="gentle_adventure",
    ):
        if blueprint is None:
            blueprint = {
                "story_spine": {"central_problem": "The path is hard to find."},
                "scene_cards": [
                    {"scene_id": "scene-1", "summary": "A lantern glows."},
                    {"scene_id": "scene-2", "summary": "Friends arrive."},
                ],
            }
        payload = {
            "run_id": run_id,
            "created_at": "2026-05-28T01:02:03Z",
            "request_options": {"age": 6},
            "classification": {
                "category_id": category_id,
                "category_display_name": "Gentle Adventure",
                "request_text": request_text,
            },
            "blueprint": blueprint,
            "final_package": {
                "request": {"age": 6},
                "blueprint": blueprint,
                "story": {"title": title, "body": body},
                "actual_word_count": len(body.split()),
                "pages": [],
                "page_break_suggestions": [],
            },
            "index_entry": {
                "run_id": run_id,
                "id": run_id,
                "created_at": "2026-05-28T01:02:03Z",
                "title": title,
                "category_display_name": "Gentle Adventure",
                "category_id": category_id,
                "actual_word_count": len(body.split()),
                "characters": [],
                "body": body,
                "pages": [],
                "user_rating": None,
                "rating_recorded_at": None,
            },
        }
        story_dir = self.stories_dir / run_id
        story_dir.mkdir(parents=True, exist_ok=True)
        (story_dir / "story.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return run_id

    def _candidate_path(self, run_id):
        return self.candidates_dir / "gentle_adventure" / f"{run_id}.json"

    def _read_story_payload(self, run_id):
        return json.loads((self.stories_dir / run_id / "story.json").read_text(encoding="utf-8"))

    def test_rating_5_creates_candidate_json(self):
        run_id = self._write_story_json()

        store.record_user_rating(run_id, 5)

        candidate = json.loads(self._candidate_path(run_id).read_text(encoding="utf-8"))
        self.assertEqual(candidate["rating"], 5)
        self.assertEqual(candidate["promotion_status"], "candidate")
        self.assertEqual(candidate["story_spine"]["central_problem"], "The path is hard to find.")
        self.assertEqual(len(candidate["scene_cards"]), 2)
        self.assertEqual(candidate["final_story_body"], "A warm beginning.\nA brave ending.")

    def test_rating_below_5_does_not_create_candidate(self):
        run_id = self._write_story_json()

        store.record_user_rating(run_id, 4)

        self.assertFalse(self.candidates_dir.exists())

    def test_rating_drop_removes_existing_candidate(self):
        run_id = self._write_story_json()

        store.record_user_rating(run_id, 5)
        store.record_user_rating(run_id, 3)

        self.assertFalse(self._candidate_path(run_id).exists())

    def test_repeat_rating_5_overwrites_deterministically(self):
        run_id = self._write_story_json(body="First body.")
        store.record_user_rating(run_id, 5)
        first_paths = list((self.candidates_dir / "gentle_adventure").glob(f"{run_id}.json"))

        self._write_story_json(run_id=run_id, body="Second body.")
        store.record_user_rating(run_id, 5)

        second_paths = list((self.candidates_dir / "gentle_adventure").glob(f"{run_id}.json"))
        candidate = json.loads(self._candidate_path(run_id).read_text(encoding="utf-8"))
        self.assertEqual(len(first_paths), 1)
        self.assertEqual(len(second_paths), 1)
        self.assertEqual(candidate["final_story_body"], "Second body.")

    def test_missing_blueprint_does_not_crash_rating_save(self):
        run_id = self._write_story_json(blueprint={})

        store.record_user_rating(run_id, 5)

        story_payload = self._read_story_payload(run_id)
        candidate = json.loads(self._candidate_path(run_id).read_text(encoding="utf-8"))
        self.assertEqual(story_payload["index_entry"]["user_rating"], 5)
        self.assertFalse(candidate["validation"]["story_spine_present"])
        self.assertFalse(candidate["validation"]["scene_cards_present"])
        self.assertEqual(candidate["validation"]["scene_count"], 0)

    def test_candidate_export_failure_does_not_break_rating(self):
        run_id = self._write_story_json()

        with (
            patch("story_engine.persistence.store.candidate_examples.export_candidate_if_eligible", side_effect=RuntimeError("boom")),
            patch("story_engine.persistence.store.trace_event") as trace_event,
        ):
            store.record_user_rating(run_id, 5)

        story_payload = self._read_story_payload(run_id)
        self.assertEqual(story_payload["index_entry"]["user_rating"], 5)
        export_events = [
            call
            for call in trace_event.call_args_list
            if call.args and call.args[0] == "prompt_example_candidate.export_failed"
        ]
        self.assertEqual(len(export_events), 1)

    def test_empty_category_id_skips_with_reason(self):
        run_id = self._write_story_json(category_id="")

        with patch("story_engine.persistence.candidate_examples.trace_event") as trace_event:
            store.record_user_rating(run_id, 5)

        story_payload = self._read_story_payload(run_id)
        skipped_events = [
            call
            for call in trace_event.call_args_list
            if call.args
            and call.args[0] == "prompt_example_candidate.skipped"
            and call.kwargs.get("reason") == "missing_category_id"
        ]
        self.assertFalse(self.candidates_dir.exists())
        self.assertEqual(story_payload["index_entry"]["user_rating"], 5)
        self.assertEqual(len(skipped_events), 1)

    def test_invalid_category_id_skips_with_reason(self):
        run_id = self._write_story_json(category_id="../escape")

        with patch("story_engine.persistence.candidate_examples.trace_event") as trace_event:
            store.record_user_rating(run_id, 5)

        story_payload = self._read_story_payload(run_id)
        skipped_events = [
            call
            for call in trace_event.call_args_list
            if call.args
            and call.args[0] == "prompt_example_candidate.skipped"
            and call.kwargs.get("reason") == "invalid_category_id"
        ]
        self.assertFalse(self.candidates_dir.exists())
        self.assertFalse((self.candidates_dir.parent / "escape").exists())
        self.assertFalse((self.candidates_dir.parent.parent / "escape").exists())
        self.assertEqual(story_payload["index_entry"]["user_rating"], 5)
        self.assertEqual(len(skipped_events), 1)

    def test_prompt_builders_do_not_reference_candidate_dir(self):
        prompts_dir = Path(__file__).resolve().parents[1] / "story_engine" / "prompts"

        matches = []
        for path in prompts_dir.rglob("*.py"):
            if "prompt_example_candidates" in path.read_text(encoding="utf-8"):
                matches.append(path)

        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
