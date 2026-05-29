from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from _helpers import _FakeResponse, _FakeToolCall
from story_engine import model_client, trace
from story_engine.errors import RunFailed
from story_engine.persistence import run_id_for


def _fake_client(*responses):
    create = Mock(side_effect=list(responses))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return client, create


class CallModelToolTests(unittest.TestCase):
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

    def test_happy_path_sends_forced_tool_payload_and_logs_tool_name(self) -> None:
        run_id = run_id_for("tool-call-happy")
        client, create = _fake_client(
            _FakeResponse(
                tool_calls=[_FakeToolCall("submit_title", '{"title": "Quiet Pebble"}')],
                prompt_tokens=7,
                completion_tokens=4,
            )
        )
        with trace.Run(run_id), patch("story_engine.model_client.client._client", return_value=client):
            parsed = model_client.call_model_tool(
                "Pick a title.",
                tool_name="submit_title",
                tool_schema={"type": "object"},
                temperature=0.2,
                agent_name="title_writer",
            )

        self.assertEqual(parsed, {"title": "Quiet Pebble"})
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["messages"], [{"role": "user", "content": "Pick a title."}])
        self.assertEqual(kwargs["tool_choice"], {"type": "function", "function": {"name": "submit_title"}})
        self.assertFalse(kwargs["parallel_tool_calls"])
        self.assertEqual(kwargs["tools"][0]["type"], "function")
        self.assertEqual(kwargs["tools"][0]["function"]["name"], "submit_title")
        self.assertEqual(kwargs["tools"][0]["function"]["parameters"], {"type": "object"})
        self.assertNotIn("strict", kwargs["tools"][0]["function"])

        records = self._records(run_id)
        self.assertEqual(records[0]["tool_name"], "submit_title")
        self.assertEqual(records[0]["response"], '{"title": "Quiet Pebble"}')
        self.assertEqual(records[0]["parsed_response"], {"title": "Quiet Pebble"})
        self.assertEqual(records[0]["input_tokens"], 7)
        self.assertEqual(records[0]["output_tokens"], 4)

    def test_retries_when_tool_calls_missing(self) -> None:
        client, create = _fake_client(
            _FakeResponse(content="plain text", tool_calls=None),
            _FakeResponse(tool_calls=[_FakeToolCall("submit_title", '{"title": "Quiet Pebble"}')]),
        )
        with patch("story_engine.model_client.client._client", return_value=client):
            parsed = model_client.call_model_tool(
                "Pick a title.",
                tool_name="submit_title",
                tool_schema={"type": "object"},
                temperature=0.2,
            )

        self.assertEqual(parsed, {"title": "Quiet Pebble"})
        self.assertEqual(create.call_count, 2)
        self.assertIn(
            "Your previous response did not invoke the submit_title function with valid JSON arguments. Retry.",
            create.call_args_list[1].kwargs["messages"][0]["content"],
        )

    def test_retries_when_wrong_function_name(self) -> None:
        client, create = _fake_client(
            _FakeResponse(tool_calls=[_FakeToolCall("wrong_name", '{"title": "Quiet Pebble"}')]),
            _FakeResponse(tool_calls=[_FakeToolCall("submit_title", '{"title": "Quiet Pebble"}')]),
        )
        with patch("story_engine.model_client.client._client", return_value=client):
            parsed = model_client.call_model_tool(
                "Pick a title.",
                tool_name="submit_title",
                tool_schema={"type": "object"},
                temperature=0.2,
            )

        self.assertEqual(parsed["title"], "Quiet Pebble")
        self.assertEqual(create.call_count, 2)

    def test_retries_when_arguments_json_is_malformed(self) -> None:
        client, create = _fake_client(
            _FakeResponse(tool_calls=[_FakeToolCall("submit_title", '{"title":')]),
            _FakeResponse(tool_calls=[_FakeToolCall("submit_title", '{"title": "Quiet Pebble"}')]),
        )
        with patch("story_engine.model_client.client._client", return_value=client):
            parsed = model_client.call_model_tool(
                "Pick a title.",
                tool_name="submit_title",
                tool_schema={"type": "object"},
                temperature=0.2,
            )

        self.assertEqual(parsed["title"], "Quiet Pebble")
        self.assertEqual(create.call_count, 2)

    def test_retries_when_arguments_json_is_not_an_object(self) -> None:
        client, create = _fake_client(
            _FakeResponse(tool_calls=[_FakeToolCall("submit_title", '["Quiet Pebble"]')]),
            _FakeResponse(tool_calls=[_FakeToolCall("submit_title", '{"title": "Quiet Pebble"}')]),
        )
        with patch("story_engine.model_client.client._client", return_value=client):
            parsed = model_client.call_model_tool(
                "Pick a title.",
                tool_name="submit_title",
                tool_schema={"type": "object"},
                temperature=0.2,
            )

        self.assertEqual(parsed["title"], "Quiet Pebble")
        self.assertEqual(create.call_count, 2)

    def test_raises_run_failed_after_three_parse_failures(self) -> None:
        client, create = _fake_client(
            _FakeResponse(tool_calls=[_FakeToolCall("submit_title", '["Quiet Pebble"]')]),
            _FakeResponse(tool_calls=[_FakeToolCall("submit_title", '["Quiet Pebble"]')]),
            _FakeResponse(tool_calls=[_FakeToolCall("submit_title", '["Quiet Pebble"]')]),
        )
        with patch("story_engine.model_client.client._client", return_value=client):
            with self.assertRaises(RunFailed) as ctx:
                model_client.call_model_tool(
                    "Pick a title.",
                    tool_name="submit_title",
                    tool_schema={"type": "object"},
                    temperature=0.2,
                    agent_name="title_writer",
                )

        self.assertEqual(create.call_count, 3)
        self.assertEqual(ctx.exception.failure_category, "unparseable_json")


if __name__ == "__main__":
    unittest.main()
