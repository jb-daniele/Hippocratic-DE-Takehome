import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NormalizersNoConcreteActionTests(unittest.TestCase):
    def test_story_engine_has_no_concrete_action_hits(self):
        result = subprocess.run(
            ["git", "grep", "-n", "concrete_action", "--", "story_engine/**"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_strip_abstract_glue_import_raises(self):
        with self.assertRaises(ImportError):
            exec("from story_engine.text.normalizers import strip_abstract_glue", {})
