"""L0→L1 domain cards under 15_Learn/."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from importlib.resources import files
from pathlib import Path

from gobs.config import resolve_vault
from gobs.constants import LEARN_DIR


class LearnError(RuntimeError):
    pass


_FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)
_LEVEL = re.compile(r"^level:\s*(\S+)", re.M)
_STATUS = re.compile(r"^status:\s*(\S+)", re.M)
_TITLE = re.compile(r"^title:\s*[\"']?(.*?)[\"']?\s*$", re.M)
_DOOR = re.compile(r"^open_door:\s*(\S+)", re.M)


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


def learn_dir(vault: Path) -> Path:
    return vault / LEARN_DIR


def domain_path(vault: Path, name: str) -> Path:
    return learn_dir(vault) / f"{slugify(name)}.md"


@dataclass
class DomainCard:
    path: Path
    title: str
    level: str
    status: str
    open_door: str

    @property
    def rel(self) -> str:
        return self.path.as_posix()


def parse_card(path: Path, vault: Path) -> DomainCard | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    m = _FRONT.match(text)
    block = m.group(1) if m else ""
    if "gobs_type: domain" not in block and "gobs_type: domain" not in text:
        return None
    title = (_TITLE.search(block) or _TITLE.search(text))
    level = (_LEVEL.search(block) or _LEVEL.search(text))
    status = (_STATUS.search(block) or _STATUS.search(text))
    door = (_DOOR.search(block) or _DOOR.search(text))
    rel = path.resolve().relative_to(vault.resolve())
    return DomainCard(
        path=rel,
        title=(title.group(1).strip() if title else path.stem),
        level=(level.group(1).strip() if level else "L0"),
        status=(status.group(1).strip() if status else "active"),
        open_door=(door.group(1).strip() if door else "first"),
    )


def list_domains(vault: Path) -> list[DomainCard]:
    folder = learn_dir(vault)
    if not folder.is_dir():
        return []
    cards: list[DomainCard] = []
    for path in sorted(folder.glob("*.md")):
        card = parse_card(path, vault)
        if card:
            cards.append(card)
    return cards


def ensure_learn_dir(vault: Path) -> Path:
    folder = learn_dir(vault)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def create_domain(vault: Path, name: str) -> tuple[Path, str]:
    """Create a domain card if missing. Returns (relative path, created|exists)."""
    ensure_learn_dir(vault)
    dest = domain_path(vault, name)
    if dest.exists():
        return dest.resolve().relative_to(vault.resolve()), "exists"
    title = name.strip() or dest.stem
    body = _template_file("domain.md").replace("{{title}}", title)
    body = body.replace("updated:", f"updated: {date.today().isoformat()}")
    dest.write_text(body, encoding="utf-8")
    return dest.resolve().relative_to(vault.resolve()), "created"


def format_status(cards: list[DomainCard]) -> str:
    if not cards:
        return "15_Learn/ 里还没有领域卡。用 gobs learn start <名称> 开一张。"
    lines = []
    for card in cards:
        lines.append(
            f"{card.level:3}  {card.status:8}  door={card.open_door:12}  {card.path}  {card.title}"
        )
    return "\n".join(lines)


def boot_prompt(rel_note: str, title: str) -> str:
    return (
        f"学习模式已打开。先读领域卡 [[{rel_note.replace('.md', '')}]] "
        f"（文件 {rel_note}）和 AGENTS.md 里的学习协议。"
        f"领域：{title}。现在是 L0→L1。"
        "不要讲课，不要公式，不要一次丢超过三个新零件。"
        "先逼我写出三句定界：场景 / 够用（可检查的行为）/ 停线。"
        "我写完你只砍过大的目标。在我说「写进卡」之前不要改库。"
    )


def resolve_learn_vault(vault: Path | None) -> Path:
    return resolve_vault(vault, cwd=Path.cwd())
