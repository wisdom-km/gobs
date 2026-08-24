import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.save import SaveError, save_note, split_paragraphs  # noqa: E402


class SaveTests(unittest.TestCase):
    def test_split_paragraphs(self) -> None:
        self.assertEqual(split_paragraphs("a\n\nb\n\n\nc"), ["a", "b", "c"])

    def test_save_with_cites(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "vault"
            vault.mkdir()
            (vault / ".obsidian").mkdir()
            (vault / "99_Archive" / "transcripts").mkdir(parents=True)
            cfg = vault / ".gobs" / "config.toml"
            cfg.parent.mkdir()
            cfg.write_text('transcripts = "99_Archive/transcripts"\n', encoding="utf-8")

            def boom() -> Path:
                raise AssertionError("should not need user config")

            with patch("gobs.config.user_config_path", lambda: vault / "nope.toml"):
                result = save_note(
                    note="30_Lessons/idea.md",
                    body="The point is this. [p2]\n",
                    chat="hello\n\nthis is the source paragraph\n\nbye",
                    vault=vault,
                    title="idea",
                    day="20260825",
                )
            self.assertTrue(result.note.is_file())
            text = result.note.read_text(encoding="utf-8")
            self.assertIn("#^gobs-20260825-2", text)
            self.assertNotIn("[p2]", text)
            self.assertEqual(result.cites, 1)
            self.assertIsNotNone(result.transcript)
            t = result.transcript.read_text(encoding="utf-8")  # type: ignore[union-attr]
            self.assertIn("^gobs-20260825-2", t)
            self.assertIn("this is the source paragraph", t)

    def test_refuses_escape(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "vault"
            vault.mkdir()
            (vault / ".obsidian").mkdir()
            with patch("gobs.config.user_config_path", lambda: vault / "nope.toml"):
                with self.assertRaises(SaveError):
                    save_note(note="../outside.md", body="x", vault=vault)


if __name__ == "__main__":
    unittest.main()
