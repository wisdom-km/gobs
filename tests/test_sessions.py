import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.sessions import encode_cwd, pick_session  # noqa: E402


class SessionTests(unittest.TestCase):
    def test_encode_matches_grok_windows_style(self) -> None:
        # URL-encode the native path, including backslashes on Windows.
        encoded = encode_cwd(Path("C:/tmp"))
        self.assertNotIn(":", encoded)
        self.assertNotIn("\\", encoded)
        self.assertTrue(encoded)

    def test_picker_new_and_index(self) -> None:
        rows = [{"id": "aaa", "title": "One", "recap": ""}]
        self.assertIsNone(pick_session(rows, input_fn=lambda _: "n"))
        self.assertEqual(pick_session(rows, input_fn=lambda _: "1"), "aaa")
        with self.assertRaises(SystemExit):
            pick_session(rows, input_fn=lambda _: "q")


if __name__ == "__main__":
    unittest.main()
