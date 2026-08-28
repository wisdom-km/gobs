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
                'learn = "10_projects/my_learn"\ntranscripts = "90_archive/sessions"\n',
                encoding="utf-8",
            )
            with patch("gobs.config.user_config_path", self._home(tmp)):
                actions = init_vault(vault, skeleton=False, set_default=False)
            text = (vault / ".gobs" / "config.toml").read_text(encoding="utf-8")
            self.assertIn("10_projects/my_learn", text)
            self.assertIn("90_archive/sessions", text)
            self.assertTrue((vault / "10_projects" / "my_learn").is_dir())
            self.assertNotIn("22_study/00_learn", actions)

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
            self.assertTrue((vault / "00_inbox").is_dir())
            self.assertTrue((vault / "10_projects").is_dir())
            self.assertTrue((vault / "20_creation").is_dir())
            self.assertTrue((vault / "21_metaphysics").is_dir())
            self.assertTrue((vault / "22_study" / "00_learn").is_dir())
            self.assertTrue((vault / "90_archive" / "transcripts").is_dir())
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



    def test_init_installs_viz(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                actions = init_vault(vault, skeleton=False, set_default=False)
            html = vault / "80_meta" / "gobs-viz" / "draw.html"
            note = vault / "80_meta" / "gobs-viz" / "画图.md"
            helper = vault / "80_meta" / "gobs-viz" / "draw.py"
            self.assertTrue(html.is_file())
            self.assertTrue(note.is_file())
            self.assertTrue(helper.is_file())
            self.assertEqual(actions["80_meta/gobs-viz/draw.html"], "created")
            self.assertEqual(actions["80_meta/gobs-viz/画图.md"], "created")
            self.assertEqual(actions["80_meta/gobs-viz/draw.py"], "created")
            html_text = html.read_text(encoding="utf-8")
            note_text = note.read_text(encoding="utf-8")
            self.assertIn("看谁", html_text)
            self.assertIn("印象包", html_text)
            self.assertIn("地图", html_text)
            self.assertIn("复制到笔记", html_text)
            self.assertIn("The animal didn't cross the street because it was too tired", html_text)
            self.assertIn("麻烦", html_text)
            self.assertIn("老办法", html_text)
            self.assertIn("只要它", html_text)
            self.assertIn("draw.html", note_text)
            self.assertIn("双编码", note_text)
            self.assertNotIn("四列表", html_text)
            self.assertNotIn("回教", html_text)
            self.assertNotIn("四列表", note_text)
            self.assertNotIn("回教", note_text)
            self.assertNotIn("QKV", html_text)
            self.assertNotIn("BLEU", html_text)
            self.assertNotIn("encoder", html_text)
            with patch("gobs.config.user_config_path", self._home(tmp)):
                again = init_vault(vault, skeleton=False, set_default=False)
            self.assertEqual(again["80_meta/gobs-viz/draw.html"], "updated")
            self.assertEqual(again["80_meta/gobs-viz/draw.py"], "updated")

    def test_draw_py_seq_vs_attn_writes_png(self) -> None:
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            self.skipTest("matplotlib not installed")
        import subprocess
        import sys

        helper = Path(__file__).resolve().parents[1] / "src" / "gobs" / "templates" / "viz" / "draw.py"
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "seq-vs-attn.png"
            proc = subprocess.run(
                [sys.executable, str(helper), "seq-vs-attn", "--out", str(out)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(out.is_file())
            self.assertGreater(out.stat().st_size, 1000)
            self.assertIn(str(out.resolve()), proc.stdout)

    def test_draw_py_process_writes_gif(self) -> None:
        try:
            import matplotlib  # noqa: F401
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("matplotlib/pillow not installed")
        import subprocess
        import sys

        helper = Path(__file__).resolve().parents[1] / "src" / "gobs" / "templates" / "viz" / "draw.py"
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "process.gif"
            proc = subprocess.run(
                [sys.executable, str(helper), "process", "--out", str(out)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(out.is_file())
            self.assertGreater(out.stat().st_size, 1000)
            self.assertIn(str(out.resolve()), proc.stdout)


if __name__ == "__main__":
    unittest.main()
