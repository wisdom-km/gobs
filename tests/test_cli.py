import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.cli import main  # noqa: E402


class CliTests(unittest.TestCase):
    def test_init_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "v"
            cfg = tmp / "home" / "config.toml"

            def fake() -> Path:
                return cfg

            with patch("gobs.config.user_config_path", fake):
                code = main(["init", str(vault), "--skeleton", "--no-default"])
            self.assertEqual(code, 0)
            self.assertTrue((vault / "00_inbox").is_dir())
            self.assertTrue((vault / "AGENTS.md").is_file())

    def test_help(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
