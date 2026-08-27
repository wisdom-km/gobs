import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.config import (  # noqa: E402
    GobsConfig,
    dump_toml,
    find_vault,
    load_user_config,
    resolve_vault,
    write_user_config,
)


class ConfigTests(unittest.TestCase):
    def test_dump_toml_escapes(self) -> None:
        text = dump_toml({"vault": r"G:\Notes\Vault", "open_obsidian": True, "mcp_timeout": 15})
        self.assertIn('vault = "G:\\\\Notes\\\\Vault"', text)
        self.assertIn("open_obsidian = true", text)
        self.assertIn("mcp_timeout = 15", text)

    def test_find_vault_walks_up(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "Notes" / "MyVault"
            nested = vault / "20_creation" / "topic"
            nested.mkdir(parents=True)
            (vault / ".obsidian").mkdir()
            self.assertEqual(find_vault(nested), vault.resolve())
            self.assertIsNone(find_vault(root))

    def test_resolve_explicit_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "v"
            vault.mkdir()
            (vault / ".obsidian").mkdir()
            self.assertEqual(resolve_vault(str(vault)), vault.resolve())

    def test_user_config_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            cfg_path = Path(raw) / "config.toml"

            def fake_path() -> Path:
                return cfg_path

            with patch("gobs.config.user_config_path", fake_path):
                write_user_config(GobsConfig(vault=Path(raw) / "vault", cli="grok"))
                loaded = load_user_config()
            self.assertEqual(loaded.cli, "grok")
            self.assertEqual(loaded.vault, (Path(raw) / "vault").resolve())


if __name__ == "__main__":
    unittest.main()
