import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.launch import launch  # noqa: E402


class LaunchTests(unittest.TestCase):
    def test_extra_env_reaches_child(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            (vault / ".obsidian").mkdir()
            captured: dict = {}

            def fake_call(argv, cwd=None, env=None):
                captured["argv"] = argv
                captured["cwd"] = cwd
                captured["env"] = env
                return 0

            with patch("gobs.launch._cli_command", return_value="grok"), patch(
                "gobs.launch.subprocess.call", side_effect=fake_call
            ), patch("gobs.launch.listed_gobs_sessions", return_value=[]), patch(
                "gobs.launch.snapshot", return_value={}
            ), patch(
                "gobs.launch.new_or_updated", return_value=[]
            ), patch(
                "gobs.config.user_config_path", lambda: vault / "nope.toml"
            ):
                code = launch(
                    vault,
                    open_obsidian=False,
                    new_session=True,
                    extra_env={"GOBS_LEARN": "1", "GOBS_LEARN_NOTE": "x.md"},
                    extra_args=["boot text"],
                )
            self.assertEqual(code, 0)
            self.assertEqual(captured["env"]["GOBS_LEARN"], "1")
            self.assertEqual(captured["env"]["GOBS_LEARN_NOTE"], "x.md")
            self.assertEqual(captured["env"]["GOBS_VAULT"], str(vault.resolve()))
            self.assertIn("boot text", captured["argv"])


if __name__ == "__main__":
    unittest.main()
