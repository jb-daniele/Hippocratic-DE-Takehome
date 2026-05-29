from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from _helpers import _FakeResponse
from story_engine import model_client, trace
from story_engine.persistence import run_id_for


def _fake_client(*responses):
    create = Mock(side_effect=list(responses))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return client, create


class CallModelJsonModernSdkTests(unittest.TestCase):
    def setUp(self) -> None:
        model_client._SEQUENCES.clear()
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.logs_dir = self.root / "logs"
        self.stories_dir = self.root / "stories"
        self.patches = [
            patch("story_engine.model_client.client.LOGS_DIR", self.logs_dir),
            patch("story_engine.model_client.client.STORIES_DIR", self.stories_dir),
            patch("story_engine.trace.LOGS_DIR", self.logs_dir),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def _records(self, run_id: str) -> list[dict]:
        path = model_client.llm_log_path(run_id)
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_call_model_json_reads_content_and_usage_from_modern_sdk_response(self) -> None:
        run_id = run_id_for("json-modern-sdk")
        client, _create = _fake_client(_FakeResponse(content='{"ok": true}', prompt_tokens=9, completion_tokens=3))
        with trace.Run(run_id), patch("story_engine.model_client.client._client", return_value=client):
            parsed = model_client.call_model_json("Return JSON.", temperature=0.1, agent_name="classifier")

        self.assertEqual(parsed, {"ok": True})
        records = self._records(run_id)
        self.assertEqual(records[0]["input_tokens"], 9)
        self.assertEqual(records[0]["output_tokens"], 3)
        self.assertEqual(records[0]["response"], '{"ok": true}')

    def test_json_decode_retry_count_is_unchanged(self) -> None:
        client, create = _fake_client(
            _FakeResponse(content="not json", prompt_tokens=1, completion_tokens=1),
            _FakeResponse(content='{"ok": true}', prompt_tokens=2, completion_tokens=2),
        )
        with patch("story_engine.model_client.client._client", return_value=client):
            parsed = model_client.call_model_json("Return JSON.", temperature=0.1, agent_name="classifier")

        self.assertEqual(parsed, {"ok": True})
        self.assertEqual(create.call_count, 2)


if __name__ == "__main__":
    unittest.main()
