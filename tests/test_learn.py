import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.cli import main  # noqa: E402
from gobs.init_cmd import init_vault  # noqa: E402
from gobs.learn import create_domain, list_domains, slugify  # noqa: E402


class LearnTests(unittest.TestCase):
    def _home(self, tmp: Path):
        cfg = tmp / "home" / ".gobs" / "config.toml"

        def fake() -> Path:
            return cfg

        return fake

    def test_slugify(self) -> None:
        self.assertEqual(slugify("Transformer"), "Transformer")
        self.assertEqual(slugify("英语 口语"), "英语-口语")
        self.assertEqual(slugify("a/b"), "a-b")

    def test_create_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=True, set_default=False)
            rel, action = create_domain(vault, "Transformer")
            self.assertEqual(action, "created")
            self.assertEqual(rel.as_posix(), "15_Learn/Transformer.md")
            text = (vault / rel).read_text(encoding="utf-8")
            self.assertIn("gobs_type: domain", text)
            self.assertIn("level: L0", text)
            self.assertIn("先不要讲课", text)
            rel2, action2 = create_domain(vault, "Transformer")
            self.assertEqual(action2, "exists")
            self.assertEqual(rel2, rel)
            cards = list_domains(vault)
            self.assertEqual(len(cards), 1)
            self.assertEqual(cards[0].level, "L0")

    def test_learn_start_no_launch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            cfg = tmp / "home" / "config.toml"

            def fake() -> Path:
                return cfg

            with patch("gobs.config.user_config_path", fake):
                main(["init", str(vault), "--no-default"])
                code = main(["learn", "start", "英语", "--vault", str(vault), "--no-launch"])
            self.assertEqual(code, 0)
            self.assertTrue((vault / "15_Learn" / "英语.md").is_file())

    def test_init_installs_learn_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            with patch("gobs.config.user_config_path", self._home(tmp)):
                actions = init_vault(vault, skeleton=True, set_default=False)
            self.assertEqual(actions["15_Learn"], "created")
            agents = (vault / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("gobs:learn-protocol", agents)
            self.assertIn("15_Learn", agents)
            skill = vault / ".grok" / "skills" / "learn-domain" / "SKILL.md"
            self.assertTrue(skill.is_file())
            self.assertIn("不要讲课", skill.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
