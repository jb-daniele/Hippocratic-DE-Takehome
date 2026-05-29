from __future__ import annotations

import os
import unittest

from story_engine import model_client


@unittest.skipUnless(os.getenv("STORYNEST_RUN_LIVE_SMOKE") == "1", "live smoke disabled")
class LiveSmokeTests(unittest.TestCase):
    def test_call_model_tool_live_smoke(self) -> None:
        parsed = model_client.call_model_tool(
            "Return a title for a calm story about a pebble.",
            tool_name="submit_title",
            tool_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["title"],
                "properties": {"title": {"type": "string", "minLength": 1, "maxLength": 80}},
            },
            temperature=0.0,
            agent_name="live_smoke",
        )
        self.assertIn("title", parsed)


if __name__ == "__main__":
    unittest.main()
