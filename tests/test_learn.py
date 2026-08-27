import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.cli import main  # noqa: E402
from gobs.init_cmd import init_vault  # noqa: E402
from gobs.learn import (  # noqa: E402
    LearnError,
    bind_session,
    boot_prompt,
    create_domain,
    list_domains,
    find_domain,
    parse_card,
    prepare_lecture,
    save_learn,
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
            self.assertEqual(rel.as_posix(), "22_study/00_learn/Transformer.md")
            text = (vault / rel).read_text(encoding="utf-8")
            self.assertIn("gobs_type: domain", text)
            self.assertIn("session_id:", text)
            rel2, action2 = create_domain(vault, "Transformer")
            self.assertEqual(action2, "exists")
            cards = list_domains(vault)
            self.assertEqual(len(cards), 1)

    def test_find_domain_outside_learn_dir(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
            rel, _ = create_domain(vault, "Transformer")
            dest_dir = vault / "22_study" / "10_papers" / "Attention Is All You Need"
            dest_dir.mkdir(parents=True)
            dest = dest_dir / "Transformer.md"
            (vault / rel).rename(dest)
            found = find_domain(vault, "Transformer")
            assert found is not None
            self.assertEqual(
                found.resolve().relative_to(vault.resolve()).as_posix(),
                dest.relative_to(vault).as_posix().replace("\\", "/"),
            )
            rel2, action = create_domain(vault, "Transformer")
            self.assertEqual(action, "exists")
            self.assertFalse((vault / "22_study" / "00_learn" / "Transformer.md").exists())
            body = dest.read_text(encoding="utf-8")
            result = save_learn(
                note="22_study/00_learn/Transformer.md",
                body=body,
                chat="## 盯\n\n排队取消。",
                vault=vault,
                title="Transformer",
                day="20260828",
            )
            self.assertEqual(result.note.resolve(), dest.resolve())

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
                code = main(["learn", "start", "英语", "--vault", str(vault), "--no-launch"])
            self.assertEqual(code, 0)
            self.assertTrue((vault / "22_study" / "00_learn" / "英语.md").is_file())

    def test_init_installs_learn_skills(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            with patch("gobs.config.user_config_path", self._home(tmp)):
                actions = init_vault(vault, skeleton=True, set_default=False)
            self.assertEqual(actions["22_study/00_learn"], "created")
            agents = (vault / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("gobs:learn-protocol", agents)
            self.assertIn("/learn", agents)
            self.assertIn("只认", agents)
            self.assertIn("gobs learn save", agents)
            self.assertIn("领域卡", agents)
            learn = vault / ".grok" / "skills" / "learn" / "SKILL.md"
            self.assertTrue(learn.is_file())
            learn_text = learn.read_text(encoding="utf-8")
            self.assertIn("当前会话", learn_text)
            self.assertIn("讲解", learn_text)
            self.assertIn("gobs learn save", learn_text)
            self.assertIn("零基础", learn_text)
            self.assertIn("只要记住", learn_text)
            self.assertIn("ASCII", learn_text)
            self.assertIn("不要硬画", learn_text)
            self.assertNotIn("一次新零件不超过 3 个", learn_text)
            self.assertIn("可读", learn_text)
            self.assertIn("聊天 log", learn_text)
            domain = vault / ".grok" / "skills" / "learn-domain" / "SKILL.md"
            self.assertTrue(domain.is_file())
            save_skill = vault / ".grok" / "skills" / "save-to-vault" / "SKILL.md"
            self.assertIn("gobs learn save", save_skill.read_text(encoding="utf-8"))

    def test_boot_prompt_save_and_teach(self) -> None:
        text = boot_prompt("22_study/00_learn/Transformer.md", "Transformer")
        self.assertIn("保存", text)
        self.assertIn("原文", text)
        self.assertIn("零基础", text)
        self.assertIn("只要记住", text)
        self.assertIn("讲解", text)
        self.assertIn("ASCII", text)
        self.assertIn("不要硬画", text)
        self.assertNotIn("不要讲课", text)
        self.assertNotIn("要准", text)
        self.assertNotIn("一次新零件不超过 3 个", text)
        self.assertNotIn("要不要把这一块同步", text)

    def test_save_learn_writes_card_and_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            (vault / ".obsidian").mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
                rel, _ = create_domain(vault, "Transformer")
                body = (vault / rel).read_text(encoding="utf-8")
                body = body.replace(
                    "- 场景：",
                    "- 场景：翻译时对齐词 [p1]",
                )
                result = save_learn(
                    note=rel.as_posix(),
                    body=body,
                    chat="用户：学 attention\n\n助手：它先算该看哪。",
                    vault=vault,
                    title="Transformer",
                    day="20260828",
                )
            self.assertTrue(result.note.is_file())
            card = result.note.read_text(encoding="utf-8")
            self.assertIn("gobs_type: domain", card)
            self.assertIn("#^gobs-20260828-1", card)
            self.assertIsNotNone(result.transcript)
            t = result.transcript.read_text(encoding="utf-8")  # type: ignore[union-attr]
            self.assertIn("讲解", t)
            self.assertNotIn("Transcript", t)
            self.assertNotIn("用户：", t)
            self.assertNotIn("助手：", t)
            self.assertIn("它先算该看哪", t)
            self.assertIn("^gobs-20260828-1", t)

    def test_prepare_lecture_drops_chat_log(self) -> None:
        paras = prepare_lecture(
            "/learn\n\n"
            "学哪个领域？说一个名字就行。\n\n"
            "课开了。领域卡在 22_study/00_learn/Transformer.md\n\n"
            "## 盯在修什么\n\n"
            "电脑读句子的旧办法是排队。\n\n"
            "保存"
        )
        self.assertEqual(paras, ["## 盯在修什么", "电脑读句子的旧办法是排队。"])

    def test_save_learn_requires_chat_and_learn_dir(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            (vault / ".obsidian").mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
                rel, _ = create_domain(vault, "Transformer")
                body = (vault / rel).read_text(encoding="utf-8")
                with self.assertRaises(LearnError):
                    save_learn(note=rel.as_posix(), body=body, chat="  ", vault=vault)
                with self.assertRaises(LearnError):
                    save_learn(
                        note="30_lessons/x.md",
                        body=body,
                        chat="hello",
                        vault=vault,
                    )
                with self.assertRaises(LearnError):
                    save_learn(
                        note=rel.as_posix(),
                        body="# not a card\n",
                        chat="hello",
                        vault=vault,
                    )

    def test_learn_save_cli(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            cfg = tmp / "home" / "config.toml"
            card = tmp / "card.md"
            chat = tmp / "chat.md"
            with patch("gobs.config.user_config_path", lambda: cfg):
                main(["init", str(vault), "--no-default"])
                rel, _ = create_domain(vault, "英语")
                card.write_text((vault / rel).read_text(encoding="utf-8"), encoding="utf-8")
                chat.write_text("hello\n\nworld", encoding="utf-8")
                code = main(
                    [
                        "learn",
                        "save",
                        "--note",
                        rel.as_posix(),
                        "--body-file",
                        str(card),
                        "--chat-file",
                        str(chat),
                        "--title",
                        "英语",
                        "--vault",
                        str(vault),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertTrue(any((vault / "90_archive" / "transcripts").glob("*.md")))


if __name__ == "__main__":
    unittest.main()
