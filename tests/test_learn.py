import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.cli import main  # noqa: E402
from gobs.init_cmd import init_vault  # noqa: E402
from gobs.learn import (  # noqa: E402
    bind_session,
    create_domain,
    list_domains,
    parse_card,
    slugify,
)


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
            self.assertIn("session_id:", text)
            rel2, action2 = create_domain(vault, "Transformer")
            self.assertEqual(action2, "exists")
            cards = list_domains(vault)
            self.assertEqual(len(cards), 1)

    def test_bind_session(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
            rel, _ = create_domain(vault, "Transformer")
            bind_session(vault, rel, "abc123session")
            card = parse_card(vault / rel, vault)
            assert card is not None
            self.assertEqual(card.session_id, "abc123session")

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
                code = main(["learn", "start", " 1语", "--vault", str(vault), "--no-launch"])
            self.assertEqual(code, 0)
            self.assertTrue((vault / "15_Learn" / " 1语.md").is_file())

    def test_init_installs_learn_skills(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            with patch("gobs.config.user_config_path", self._home(tmp)):
                actions = init_vault(vault, skeleton=True, set_default=False)
            self.assertEqual(actions["15_Learn"], "created")
            agents = (vault / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("gobs:learn-protocol", agents)
            self.assertIn("/learn", agents)
            learn = vault / ".grok" / "skills" / "learn" / "SKILL.md"
            self.assertTrue(learn.is_file())
            self.assertIn("当前会话", learn.read_text(encoding="utf-8"))
            domain = vault / ".grok" / "skills" / "learn-domain" / "SKILL.md"
            self.assertTrue(domain.is_file())


if __name__ == "__main__":
    unittest.main()
