"""L0→L1 domain cards (topic folder, or 22_study/00_learn/ as fallback)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from importlib.resources import files
from pathlib import Path

from gobs.config import load_user_config, load_vault_config, resolve_vault
from gobs.constants import LEARN_DIR
from gobs.save import SaveError, SaveResult, save_note, split_paragraphs

_NOISE_EXACT = re.compile(
    r"^(?:"
    r"/[\w-]+(?:\s+\S+)*"
    r"|保存|写进库|记下来|save(?:\s+to\s+vault)?"
    r"|/save-to-vault(?:\s+\S+)*"
    r")\s*$",
    re.I,
)
_NOISE_START = re.compile(
    r"^(?:"
    r"学哪个领域"
    r"|课开了"
    r"|领域卡在"
    r"|学习模式已打开"
    r"|续学模式已打开"
    r")",
)
_ASSIST = re.compile(r"^(?:助手|助理|Assistant|Grok)\s*[：:]\s*", re.I)
_USER = re.compile(r"^(?:用户|User|孔明)\s*[：:]\s*", re.I)


class LearnError(RuntimeError):
    pass


_FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)
_LEVEL = re.compile(r"^level:\s*(\S+)", re.M)
_STATUS = re.compile(r"^status:\s*(\S+)", re.M)
_TITLE = re.compile(r"^title:\s*[\"']?(.*?)[\"']?\s*$", re.M)
_DOOR = re.compile(r"^open_door:\s*(\S+)", re.M)
_SESSION = re.compile(r"^session_id:\s*(\S+)", re.M)


def _template_file(*parts: str) -> str:
    try:
        return files("gobs.templates").joinpath(*parts).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        root = Path(__file__).resolve().parent / "templates"
        return root.joinpath(*parts).read_text(encoding="utf-8")


def slugify(name: str) -> str:
    text = name.strip()
    text = re.sub(r'[\\/:*?"<>|]+', "-", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-.")
    return text or "domain"


_SKIP_DIR_NAMES = {".obsidian", ".git", ".grok", ".trash", "node_modules"}


def learn_dir(vault: Path) -> Path:
    cfg = load_vault_config(vault, load_user_config())
    rel = (cfg.learn or LEARN_DIR).replace("\\", "/").strip("/")
    return vault / rel


def domain_path(vault: Path, name: str) -> Path:
    return learn_dir(vault) / f"{slugify(name)}.md"


def _iter_md(vault: Path):
    root = vault.resolve()
    for path in root.rglob("*.md"):
        if any(part in _SKIP_DIR_NAMES for part in path.relative_to(root).parts):
            continue
        yield path


@dataclass
class DomainCard:
    path: Path
    title: str
    level: str
    status: str
    open_door: str
    session_id: str = ""

    @property
    def rel(self) -> str:
        return self.path.as_posix()


def parse_card(path: Path, vault: Path) -> DomainCard | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    m = _FRONT.match(text)
    block = m.group(1) if m else ""
    if "gobs_type: domain" not in block:
        return None
    title = _TITLE.search(block) or _TITLE.search(text)
    level = _LEVEL.search(block) or _LEVEL.search(text)
    status = _STATUS.search(block) or _STATUS.search(text)
    door = _DOOR.search(block) or _DOOR.search(text)
    session = _SESSION.search(block) or _SESSION.search(text)
    rel = path.resolve().relative_to(vault.resolve())
    sid = session.group(1).strip() if session else ""
    if sid in {"\"\"", "''", "~", "null", "None"}:
        sid = ""
    return DomainCard(
        path=rel,
        title=(title.group(1).strip() if title else path.stem),
        level=(level.group(1).strip() if level else "L0"),
        status=(status.group(1).strip() if status else "active"),
        open_door=(door.group(1).strip() if door else "first"),
        session_id=sid,
    )


def list_domains(vault: Path) -> list[DomainCard]:
    cards: list[DomainCard] = []
    seen: set[Path] = set()
    for path in _iter_md(vault):
        card = parse_card(path, vault)
        if not card:
            continue
        key = (vault / card.path).resolve()
        if key in seen:
            continue
        seen.add(key)
        cards.append(card)
    cards.sort(key=lambda c: c.path.as_posix())
    return cards


def find_domain(vault: Path, name: str) -> Path | None:
    """Locate a domain card by title or filename, anywhere in the vault."""
    slug = slugify(name)
    preferred = domain_path(vault, name)
    if preferred.is_file() and parse_card(preferred, vault):
        return preferred
    want = name.strip()
    for path in _iter_md(vault):
        card = parse_card(path, vault)
        if not card:
            continue
        if card.title == want or path.stem == slug:
            return path
    return None


def ensure_learn_dir(vault: Path) -> Path:
    folder = learn_dir(vault)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def create_domain(vault: Path, name: str) -> tuple[Path, str]:
    """Create a domain card if missing. Returns (relative path, created|exists).

    New cards still land in 22_study/00_learn/. If a card with this title already
    lives next to a topic (e.g. a paper folder), reuse that file.
    """
    existing = find_domain(vault, name)
    if existing is not None:
        return existing.resolve().relative_to(vault.resolve()), "exists"
    ensure_learn_dir(vault)
    dest = domain_path(vault, name)
    title = name.strip() or dest.stem
    body = _template_file("domain.md").replace("{{title}}", title)
    body = body.replace("updated:", f"updated: {date.today().isoformat()}")
    dest.write_text(body, encoding="utf-8")
    return dest.resolve().relative_to(vault.resolve()), "created"


def bind_session(vault: Path, rel: Path | str, session_id: str) -> None:
    """Write session_id into the domain card frontmatter."""
    path = vault / Path(rel)
    if not path.is_file():
        raise LearnError(f"domain card missing: {rel}")
    text = path.read_text(encoding="utf-8")
    m = _FRONT.match(text)
    if not m:
        raise LearnError(f"no frontmatter on {rel}")
    block = m.group(1)
    if _SESSION.search(block):
        block2 = _SESSION.sub(f"session_id: {session_id}", block, count=1)
    else:
        block2 = block.rstrip() + f"\nsession_id: {session_id}\n"
    if "updated:" in block2:
        block2 = re.sub(
            r"^updated:.*$",
            f"updated: {date.today().isoformat()}",
            block2,
            count=1,
            flags=re.M,
        )
    else:
        block2 = block2.rstrip() + f"\nupdated: {date.today().isoformat()}\n"
    new_text = f"---\n{block2.rstrip()}\n---\n" + text[m.end() :]
    path.write_text(new_text, encoding="utf-8")


def format_status(cards: list[DomainCard]) -> str:
    if not cards:
        return "还没有领域卡。用 gobs learn start <名称> 开一张。"
    lines = []
    for card in cards:
        sid = card.session_id or "-"
        lines.append(
            f"{card.level:3}  {card.status:8}  door={card.open_door:12}  "
            f"session={sid[:12]:12}  {card.path}  {card.title}"
        )
    return "\n".join(lines)


def is_protocol_noise(text: str) -> bool:
    line = text.strip()
    if not line:
        return True
    if _NOISE_EXACT.match(line):
        return True
    return bool(_NOISE_START.match(line))


def prepare_lecture(text: str) -> list[str]:
    """Turn a learn-save payload into readable 讲解 paragraphs.

    Drops slash-command / 保存 / 开课 protocol lines. Strips 助手： labels.
    A well-written 讲解 passes through unchanged.
    """
    out: list[str] = []
    for para in split_paragraphs(text):
        if _ASSIST.match(para):
            para = _ASSIST.sub("", para).strip()
        elif _USER.match(para):
            rest = _USER.sub("", para).strip()
            if is_protocol_noise(rest) or len(rest) < 8:
                continue
            para = f"> {rest}"
        if is_protocol_noise(para):
            continue
        if para:
            out.append(para)
    return out


def resolve_learn_note(vault: Path, note: str) -> str:
    """Accept 22_study/00_learn/Name.md or a moved card found by title/filename."""
    rel = note.replace("\\", "/").lstrip("/")
    dest = vault / rel
    if dest.is_file() and parse_card(dest, vault) is not None:
        return dest.resolve().relative_to(vault.resolve()).as_posix()
    found = find_domain(vault, Path(rel).stem)
    if found is not None:
        return found.resolve().relative_to(vault.resolve()).as_posix()
    raise LearnError(f"learn save must target an existing domain card, got {note}")


def save_learn(
    *,
    note: str,
    body: str,
    chat: str,
    vault: Path | None = None,
    title: str | None = None,
    day: str | None = None,
) -> SaveResult:
    """Archive a readable lecture and write the domain card in one step."""
    if not (chat or "").strip():
        raise LearnError("learn save requires the lecture text (原文)")
    if "gobs_type: domain" not in body:
        raise LearnError("learn save body must be a domain card (gobs_type: domain)")
    lecture = "\n\n".join(prepare_lecture(chat))
    if not lecture.strip():
        raise LearnError("learn save 原文 is empty after removing protocol lines")
    vault_path = resolve_learn_vault(vault)
    rel = resolve_learn_note(vault_path, note)
    try:
        return save_note(
            note=rel,
            body=body,
            chat=lecture,
            vault=vault_path,
            title=title,
            day=day,
            lecture=True,
        )
    except SaveError as exc:
        raise LearnError(str(exc)) from exc


def boot_prompt(
    rel_note: str,
    title: str,
    *,
    resume: bool = False,
    level: str = "L0",
) -> str:
    base = (
        f"先读领域卡 [[{rel_note.replace('.md', '')}]]（文件 {rel_note}）"
        f"和 AGENTS.md 里的学习协议。领域：{title}。档位：{level}。"
    )
    teach = (
        "对零基础讲，像默认 gobs 讲解，不像考卷。"
        "每一课：一件具体麻烦 → 一个能看见的例子演完 → 用同一例子演没有它会怎样"
        " → 「这一课只要记住」2～3 句大白话 → 再让对方用这个例子说一遍。"
        "过程课（怎么走 / 谁连谁 / 有无对比）必须用 ASCII 画出「有它 / 没有它」，写进讲解；"
        "定界、判断、贴纸课不要硬画。L1 只在旧图上贴名字，禁止换故事。"
        "课堂上不要念四列表，不要先甩术语或公式，不要先考四问。"
    )
    sync = (
        "我说「保存」时：把这次课写成一篇可读讲解进归档（像默认 gobs 讲解，不要聊天 log），"
        "同时把这一块写进领域卡。一次完成。禁止把对话 log 写进领域卡或原文。"
    )
    if resume:
        return (
            f"续学模式已打开。{base}"
            "不要从头讲。先看卡上已有内容和 open_door，从缺的那一块继续。"
            f"{teach}{sync}"
        )
    return (
        f"学习模式已打开。{base} 现在是 L0→L1。"
        "新课先定界（场景 / 够用 / 停线）；已经说清这三句就开讲，不要空问。"
        f"{teach}{sync}"
    )


def resolve_learn_vault(vault: Path | None) -> Path:
    return resolve_vault(vault, cwd=Path.cwd())
