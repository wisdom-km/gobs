import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.init_cmd import init_vault  # noqa: E402


class InitTests(unittest.TestCase):
    def _home(self, tmp: Path):
        cfg = tmp / "home" / ".gobs" / "config.toml"

        def fake() -> Path:
            return cfg

        return fake

    def test_init_preserves_custom_learn_dir(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            (vault / ".obsidian").mkdir()
            gobs = vault / ".gobs"
            gobs.mkdir()
            gobs.joinpath("config.toml").write_text(
                'learn = "22_study/00_learn"\ntranscripts = "90_archive/transcripts"\n',
                encoding="utf-8",
            )
            with patch("gobs.config.user_config_path", self._home(tmp)):
                actions = init_vault(vault, skeleton=False, set_default=False)
            text = (vault / ".gobs" / "config.toml").read_text(encoding="utf-8")
            self.assertIn("22_study/00_learn", text)
            self.assertIn("90_archive/transcripts", text)
            self.assertTrue((vault / "22_study" / "00_learn").is_dir())
            self.assertNotIn("15_Learn", actions)

    def test_init_does_not_overwrite_agents(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            (vault / "AGENTS.md").write_text("keep me", encoding="utf-8")
            with patch("gobs.config.user_config_path", self._home(tmp)):
                actions = init_vault(vault, skeleton=False, set_default=True)
            self.assertEqual(actions["AGENTS.md"], "updated")
            text = (vault / "AGENTS.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("keep me"))
            self.assertIn("gobs:save-protocol", text)
            self.assertIn("gobs save", text)
            self.assertTrue((vault / ".gobs" / "config.toml").is_file())
            self.assertTrue((vault / ".obsidian").is_dir())

    def test_init_skeleton_creates_folders_not_readme_if_present(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            (vault / "README.md").write_text("# mine\n", encoding="utf-8")
            with patch("gobs.config.user_config_path", self._home(tmp)):
                actions = init_vault(vault, skeleton=True, set_default=False)
            self.assertEqual(actions["README.md"], "skipped")
            self.assertTrue((vault / "00_Inbox").is_dir())
            self.assertTrue((vault / "10_Projects").is_dir())
            self.assertTrue((vault / "99_Archive" / "transcripts").is_dir())
            self.assertTrue((vault / "AGENTS.md").is_file())
            text = (vault / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("scribe and archivist", text)
            self.assertIn("gobs:save-protocol", text)
            self.assertNotIn("孔明", text)
            skill = vault / ".grok" / "skills" / "save-to-vault" / "SKILL.md"
            self.assertTrue(skill.is_file())
            self.assertIn("gobs save", skill.read_text(encoding="utf-8"))

    def test_force_agents_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            (vault / "AGENTS.md").write_text("old", encoding="utf-8")
            with patch("gobs.config.user_config_path", self._home(tmp)):
                actions = init_vault(vault, force_agents=True, set_default=False)
            self.assertEqual(actions["AGENTS.md"], "updated")
            self.assertIn("gobs vault conventions", (vault / "AGENTS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
