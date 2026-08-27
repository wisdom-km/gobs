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
    clamp_bloom,
    create_domain,
    format_status,
    list_domains,
    find_domain,
    lecture_is_dirty,
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

    def _vault(self, tmp: Path) -> Path:
        vault = tmp / "vault"
        vault.mkdir()
        with patch("gobs.config.user_config_path", self._home(tmp)):
            init_vault(vault, skeleton=False, set_default=False)
        return vault

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
            self.assertIn("enough_scene:", text)
            self.assertIn("principles_n:", text)
            self.assertIn("当前组块", text)
            self.assertIn("第一性原理", text)
            self.assertIn("领域地图", text)
            self.assertNotIn("## 四列表", text)
            self.assertNotIn("## 回教", text)
            self.assertNotRegex(text, r"(?m)^scene:")
            rel2, action2 = create_domain(vault, "Transformer")
            self.assertEqual(action2, "exists")
            cards = list_domains(vault)
            self.assertEqual(len(cards), 1)
            status = format_status(cards)
            self.assertIn("phase=", status)
            self.assertIn("next_review=", status)
            self.assertIn("artifact=", status)

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
            with self.assertRaises(LearnError):
                save_learn(
                    note="22_study/00_learn/Transformer.md",
                    body=body,
                    chat="排队取消。",
                    vault=vault,
                    title="Transformer",
                    day="20260828",
                )
            result = save_learn(
                note=dest.relative_to(vault).as_posix().replace("\\", "/"),
                body=body,
                chat="排队取消。",
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
            self.assertEqual(card.open_door, "first")
            self.assertEqual(card.phase, "enough")

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
            self.assertIn("gobs learn save", agents)
            self.assertIn("领域卡", agents)
            self.assertIn("一课 = 一个 phase", agents)
            self.assertNotIn("今天看哪篇只认库根", agents)
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
            self.assertIn("原文", learn_text)
            self.assertIn("懂没懂", learn_text)
            self.assertIn("印象包", learn_text)
            self.assertIn("摘要", learn_text)
            self.assertIn("这一课够用", learn_text)
            self.assertNotIn("一次新零件不超过 3 个", learn_text)
            self.assertIn("可读", learn_text)
            self.assertIn("聊天 log", learn_text)
            self.assertIn("章节补丁", learn_text)
            self.assertIn("最多新上 4 条", learn_text)
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
        self.assertIn("卡住", text)
        self.assertIn("印象包", text)
        self.assertIn("摘要", text)
        self.assertIn("一个 phase", text)
        self.assertIn("只打开", text)
        self.assertIn("先提取", text)
        self.assertIn("补丁", text)
        self.assertNotIn("不要讲课", text)
        self.assertNotIn("要准", text)
        self.assertNotIn("一次新零件不超过 3 个", text)
        self.assertNotIn("要不要把这一块同步", text)
        encode = boot_prompt(
            "22_study/00_learn/Transformer.md",
            "Transformer",
            phase="encode",
        )
        self.assertIn("## 当前组块", encode)
        self.assertIn("phase：encode", encode)

    def test_save_learn_writes_card_and_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            (vault / ".obsidian").mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
                rel, _ = create_domain(vault, "Transformer")
                body = (
                    "---\n"
                    "gobs_type: domain\n"
                    "title: Transformer\n"
                    "phase: encode\n"
                    "---\n\n"
                    "## 当前组块\n\n"
                    "- [current] attention 对齐 [p1]\n"
                )
                result = save_learn(
                    note=rel.as_posix(),
                    body=body,
                    chat="## 盯\n\n它先算该看哪。",
                    vault=vault,
                    title="Transformer",
                    day="20260828",
                )
            self.assertTrue(result.note.is_file())
            card = result.note.read_text(encoding="utf-8")
            self.assertIn("gobs_type: domain", card)
            self.assertIn("#^gobs-20260828-1", card)
            self.assertIn("## 定界", card)
            self.assertIn("## 第一性原理", card)
            self.assertIsNotNone(result.transcript)
            t = result.transcript.read_text(encoding="utf-8")  # type: ignore[union-attr]
            self.assertIn("讲解", t)
            self.assertNotIn("Transcript", t)
            self.assertNotIn("用户：", t)
            self.assertNotIn("助手：", t)
            self.assertIn("它先算该看哪", t)
            self.assertIn("^gobs-20260828-1", t)
            self.assertTrue(result.transcript.name.endswith("-encode.md"))  # type: ignore[union-attr]

    def test_prepare_lecture_drops_protocol_noise(self) -> None:
        paras = prepare_lecture(
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

    def test_patch_keeps_other_sections(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
                rel, _ = create_domain(vault, "Transformer")
                original = (vault / rel).read_text(encoding="utf-8")
                self.assertIn("## 定界", original)
                self.assertIn("## 费曼", original)
                patch_body = (
                    "---\n"
                    "gobs_type: domain\n"
                    "phase: principles\n"
                    "---\n\n"
                    "## 第一性原理\n\n"
                    "1. attention 是按相关程度看全班\n"
                    "2. 排队会把早先的印象包挤糊\n"
                )
                save_learn(
                    note=rel.as_posix(),
                    body=patch_body,
                    chat="两条原理：看全班，不要排队。",
                    vault=vault,
                    title="Transformer",
                    day="20260828",
                )
            text = (vault / rel).read_text(encoding="utf-8")
            self.assertIn("## 定界", text)
            self.assertIn("## 费曼", text)
            self.assertIn("## 当前组块", text)
            self.assertIn("## 提取队列", text)
            self.assertIn("attention 是按相关程度看全班", text)
            self.assertIn("principles_n: 2", text)
            self.assertIn("phase: principles", text)
            self.assertNotIn("## 四列表", text)

    def test_dirty_chat_raises(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
                rel, _ = create_domain(vault, "Transformer")
                body = (vault / rel).read_text(encoding="utf-8")
                for chat in (
                    "用户：学 attention\n\n助手：它先算该看哪。",
                    "孔明：保存\n\n正文还在。",
                    "/learn Transformer\n\n排队取消。",
                ):
                    with self.assertRaises(LearnError) as ctx:
                        save_learn(
                            note=rel.as_posix(),
                            body=body,
                            chat=chat,
                            vault=vault,
                        )
                    self.assertIn("dirty", str(ctx.exception))
        self.assertTrue(lecture_is_dirty("用户：hello"))
        self.assertTrue(lecture_is_dirty("助手：world"))
        self.assertTrue(lecture_is_dirty("/learn"))
        self.assertFalse(lecture_is_dirty("它先算该看哪。"))

    def test_wrong_note_path_raises(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
                rel, _ = create_domain(vault, "Transformer")
                body = (vault / rel).read_text(encoding="utf-8")
                with self.assertRaises(LearnError) as ctx:
                    save_learn(
                        note="22_study/00_learn/Other.md",
                        body=body,
                        chat="排队取消。",
                        vault=vault,
                    )
                self.assertIn("existing domain card", str(ctx.exception))
                with self.assertRaises(LearnError):
                    save_learn(
                        note="22_study/00_learn/Transformer",
                        body=body,
                        chat="排队取消。",
                        vault=vault,
                    )

    def test_same_day_second_lecture_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
                rel, _ = create_domain(vault, "Transformer")
                body = (
                    "---\n"
                    "gobs_type: domain\n"
                    "phase: encode\n"
                    "---\n"
                )
                first = save_learn(
                    note=rel.as_posix(),
                    body=body,
                    chat="第一篇讲解。",
                    vault=vault,
                    title="Transformer",
                    day="20260828",
                )
                second = save_learn(
                    note=rel.as_posix(),
                    body=body,
                    chat="第二篇讲解。",
                    vault=vault,
                    title="Transformer",
                    day="20260828",
                )
            self.assertIsNotNone(first.transcript)
            self.assertIsNotNone(second.transcript)
            self.assertNotEqual(first.transcript, second.transcript)
            self.assertTrue(first.transcript.is_file())  # type: ignore[union-attr]
            self.assertTrue(second.transcript.is_file())  # type: ignore[union-attr]
            self.assertIn("第一篇讲解", first.transcript.read_text(encoding="utf-8"))  # type: ignore[union-attr]
            self.assertIn("第二篇讲解", second.transcript.read_text(encoding="utf-8"))  # type: ignore[union-attr]
            names = sorted(p.name for p in (vault / "90_archive" / "transcripts").glob("*.md"))
            self.assertEqual(len(names), 2)
            self.assertTrue(any(n.endswith("-encode.md") for n in names))
            self.assertTrue(any("-encode-2.md" in n or n.endswith("-encode-2.md") for n in names))

    def test_bloom_create_clamped(self) -> None:
        self.assertEqual(clamp_bloom("create"), "analyze")
        self.assertEqual(clamp_bloom("understand"), "understand")
        self.assertEqual(clamp_bloom("apply"), "apply")
        self.assertEqual(clamp_bloom('"create"'), "analyze")
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
                rel, _ = create_domain(vault, "Transformer")
                old = (vault / rel).read_text(encoding="utf-8")
                # old-card scene migrates on first save
                old = old.replace('enough_scene: ""', 'enough_scene: ""\nscene: "翻译时对齐"')
                (vault / rel).write_text(old, encoding="utf-8")
                body = (
                    "---\n"
                    "gobs_type: domain\n"
                    "bloom: create\n"
                    'open_door: "second door"\n'
                    "---\n"
                )
                save_learn(
                    note=rel.as_posix(),
                    body=body,
                    chat="夹住 bloom。",
                    vault=vault,
                    title="Transformer",
                    day="20260828",
                )
            text = (vault / rel).read_text(encoding="utf-8")
            self.assertIn("bloom: analyze", text)
            self.assertNotIn("bloom: create", text)
            self.assertIn('open_door: "second door"', text)
            self.assertIn("enough_scene:", text)
            self.assertIn("翻译时对齐", text)
            self.assertNotRegex(text, r"(?m)^scene:")
            card = parse_card(vault / rel, vault)
            assert card is not None
            self.assertEqual(card.open_door, "second door")

    def test_source_links_do_not_stack(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            vault = tmp / "vault"
            vault.mkdir()
            with patch("gobs.config.user_config_path", self._home(tmp)):
                init_vault(vault, skeleton=False, set_default=False)
                rel, _ = create_domain(vault, "Transformer")
                body = "---\ngobs_type: domain\nphase: encode\n---\n"
                save_learn(
                    note=rel.as_posix(),
                    body=body,
                    chat="第一篇。",
                    vault=vault,
                    title="Transformer",
                    day="20260828",
                )
                save_learn(
                    note=rel.as_posix(),
                    body=body,
                    chat="第二篇。",
                    vault=vault,
                    title="Transformer",
                    day="20260828",
                )
            text = (vault / rel).read_text(encoding="utf-8")
            self.assertEqual(text.count("Source:"), 1)


if __name__ == "__main__":
    unittest.main()
