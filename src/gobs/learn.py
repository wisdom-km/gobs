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
    r")"
)
_ASSIST = re.compile(r"^(?:助手|助理|Assistant|Grok)\s*[：:]\s*", re.I)
_USER = re.compile(r"^(?:用户|User|孔明)\s*[：:]\s*", re.I)
_DIRTY_LABEL = re.compile(
    r"^(?:用户|助手|孔明)\s*[：:]|^/learn(?:\s|$)",
    re.M,
)
_FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)
_H2 = re.compile(r"^##[ \t]+(.+?)\s*$", re.M)
_FM_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")
_ARTIFACT_PATH = re.compile(
    r"\[\[([^\]|#]+)(?:[#|].*)?\]\]|((?:[\w.\u4e00-\u9fff-]+/)+[\w.\u4e00-\u9fff-]+\.md)"
)
_PRINCIPLE_ITEM = re.compile(r"^(?:\d+\.|[-*])\s+\S")

BLOOM_OK = ("understand", "apply", "analyze")
PHASES = (
    "enough",
    "map",
    "principles",
    "encode",
    "retrieve",
    "feynman",
    "artifact",
    "review",
)
PHASE_SECTION = {
    "enough": "定界",
    "map": "领域地图",
    "principles": "第一性原理",
    "encode": "当前组块",
    "retrieve": "提取队列",
    "feynman": "费曼",
    "artifact": "最小产物",
    "review": "已知 / 未知 / 下一步",
}
FM_ORDER = (
    "gobs_type",
    "title",
    "level",
    "status",
    "enough",
    "enough_who",
    "enough_scene",
    "stop",
    "phase",
    "bloom",
    "map_ready",
    "principles_n",
    "last_review",
    "next_review",
    "interval_days",
    "artifact",
    "known",
    "unknown",
    "next_move",
    "open_door",
    "session_id",
    "doors",
    "updated",
)


class LearnError(RuntimeError):
    pass


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


def _unquote(val: str) -> str:
    s = (val or "").strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1]
    return s


def _empty(val: str | None) -> bool:
    s = _unquote(val or "")
    return s in {"", "~", "null", "None"}


def clamp_bloom(value: str) -> str:
    v = _unquote(value or "")
    if v == "create":
        return "analyze"
    if v in BLOOM_OK:
        return v
    return v or "understand"


def lecture_is_dirty(text: str) -> bool:
    """True when the payload still has chat/skill labels (refuse, do not wash)."""
    return bool(_DIRTY_LABEL.search(text or ""))


def _fm_get(block: str, key: str, default: str = "") -> str:
    m = re.search(
        rf"""^{re.escape(key)}:\s*(?:"([^"]*)"|'([^']*)'|(.*?))\s*$""",
        block,
        re.M,
    )
    if not m:
        return default
    if m.group(1) is not None:
        return m.group(1)
    if m.group(2) is not None:
        return m.group(2)
    return (m.group(3) or "").strip()


def parse_front_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal key, buf
        if key is not None:
            fields[key] = "\n".join(buf).strip("\n")
        key = None
        buf = []

    for line in (block or "").splitlines():
        if line.startswith((" ", "\t")) and key is not None:
            buf.append(line)
            continue
        m = _FM_LINE.match(line)
        if m:
            flush()
            key = m.group(1)
            rest = m.group(2)
            buf = [rest] if rest != "" else []
            continue
        if key is not None:
            buf.append(line)
    flush()
    return fields


def split_front(text: str) -> tuple[str, str]:
    m = _FRONT.match(text or "")
    if not m:
        return "", text or ""
    return m.group(1), text[m.end() :]


def split_sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    matches = list(_H2.finditer(body or ""))
    if not matches:
        return body or "", []
    preamble = body[: matches[0].start()]
    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections.append((m.group(1).strip(), body[start:end]))
    return preamble, sections


def _fmt_field(key: str, val: str) -> str:
    if key == "open_door":
        return f'{key}: "{_unquote(val)}"'
    if key == "bloom":
        return f"{key}: {clamp_bloom(val)}"
    if key == "scene":
        return ""
    text = val if isinstance(val, str) else str(val)
    if "\n" in text:
        body = text if text.startswith("\n") else "\n" + text
        return f"{key}:{body}" if text.startswith("\n") or text.lstrip().startswith("-") else f"{key}:{body}"
    return f"{key}: {text}"


def format_front(fields: dict[str, str]) -> str:
    cleaned = dict(fields)
    cleaned.pop("scene", None)
    if "bloom" in cleaned:
        cleaned["bloom"] = clamp_bloom(cleaned["bloom"])
    if "open_door" in cleaned:
        cleaned["open_door"] = _unquote(cleaned["open_door"])
    lines: list[str] = []
    seen: set[str] = set()
    for key in FM_ORDER:
        if key not in cleaned:
            continue
        line = _fmt_field(key, cleaned[key])
        if line:
            lines.append(line)
        seen.add(key)
    for key, val in cleaned.items():
        if key in seen or key == "scene":
            continue
        line = _fmt_field(key, val)
        if line:
            lines.append(line)
    return "\n".join(lines)


def migrate_scene(fields: dict[str, str]) -> dict[str, str]:
    """Old cards: copy scene → enough_scene once, then drop scene."""
    out = dict(fields)
    scene = out.get("scene")
    if _empty(out.get("enough_scene")) and not _empty(scene):
        out["enough_scene"] = _unquote(scene or "")
    out.pop("scene", None)
    return out


def _count_principles(text: str) -> int:
    n = 0
    for line in (text or "").splitlines():
        if _PRINCIPLE_ITEM.match(line.strip()):
            n += 1
    return n


def _section_has_content(text: str) -> bool:
    for line in (text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("（") or s.startswith("("):
            continue
        if s in {"门 = 地图节点。最多 5 个。`open_door` 指向当前节点。"}:
            continue
        if re.match(r"^[-*]\s+\S", s) or re.match(r"^\d+\.\s+\S", s):
            rest = re.sub(r"^[-*\d.]+\s+", "", s).strip().rstrip("：:")
            if rest and rest not in {"first", "first：", "first:"}:
                return True
        elif len(s) >= 8:
            return True
    return False


def _find_artifact_path(text: str) -> str:
    m = _ARTIFACT_PATH.search(text or "")
    if not m:
        return ""
    return (m.group(1) or m.group(2) or "").strip()


FROZEN_HEADINGS = frozenset({"四列表", "回教"})
KEEP_NONEMPTY = frozenset(
    {
        "enough",
        "enough_who",
        "enough_scene",
        "stop",
        "artifact",
        "open_door",
        "level",
    }
)


def _principle_key(line: str) -> str:
    return re.sub(r"^(?:\d+\.|[-*])\s+", "", line.strip())


def _principle_lines(text: str) -> list[str]:
    return [ln.strip() for ln in (text or "").splitlines() if _PRINCIPLE_ITEM.match(ln.strip())]


def merge_principles_section(old: str, new: str) -> str:
    """Append new principle items. Never drop existing ones."""
    old_items = _principle_lines(old)
    seen = {_principle_key(x) for x in old_items}
    added: list[str] = []
    for ln in _principle_lines(new):
        key = _principle_key(ln)
        if key and key not in seen:
            seen.add(key)
            added.append(key)
    if len(added) > 4:
        raise LearnError("principles lesson can add at most 4 items")
    if not added:
        return old if (old or "").strip() else new
    body = (old or "").rstrip()
    if body and not body.endswith("\n"):
        body += "\n"
    start = len(old_items)
    for i, item in enumerate(added, start=start + 1):
        body += f"{i}. {item}\n"
    if not body.startswith("\n"):
        body = "\n" + body
    if not body.endswith("\n"):
        body += "\n"
    return body


def merge_front_fields(old: dict[str, str], incoming: dict[str, str]) -> dict[str, str]:
    """Empty incoming values must not wipe protected fields."""
    out = dict(old)
    for key, val in incoming.items():
        if key in KEEP_NONEMPTY and _empty(val) and not _empty(old.get(key)):
            continue
        out[key] = val
    return out


def merge_sections(old_body: str, new_body: str) -> tuple[str, list[str]]:
    """Merge by ## heading. Unnamed old sections stay. Returns (body, incoming headings)."""
    old_pre, old_secs = split_sections(old_body)
    new_pre, new_secs = split_sections(new_body)
    incoming = {h: c for h, c in new_secs}
    frozen = [h for h in incoming if h in FROZEN_HEADINGS]
    if frozen:
        raise LearnError("patch must not touch " + " / ".join(frozen))
    old_map = {h: c for h, c in old_secs}
    if "第一性原理" in incoming:
        if _count_principles(incoming["第一性原理"]) == 0:
            incoming.pop("第一性原理")
        else:
            incoming["第一性原理"] = merge_principles_section(
                old_map.get("第一性原理", ""), incoming["第一性原理"]
            )
            new_n = _count_principles(incoming["第一性原理"])
            old_n = _count_principles(old_map.get("第一性原理", ""))
            if new_n < old_n:
                raise LearnError("principles section cannot shrink")
            if new_n - old_n > 4:
                raise LearnError("principles lesson can add at most 4 items")
    order = [h for h, _ in old_secs]
    for h, _ in new_secs:
        if h not in order and h in incoming:
            order.append(h)
    pre = new_pre if new_pre.strip() else old_pre
    parts: list[str] = []
    if pre.strip():
        parts.append(pre.rstrip() + "\n\n")
    for h in order:
        content = incoming[h] if h in incoming else old_map.get(h, "\n")
        if not content.startswith("\n"):
            content = "\n" + content
        parts.append(f"## {h}{content}")
    text = "".join(parts)
    if text and not text.endswith("\n"):
        text += "\n"
    return text, list(incoming)


def apply_derived(
    fields: dict[str, str],
    incoming_headings: list[str],
    body: str,
) -> dict[str, str]:
    _, secs = split_sections(body)
    smap = {h: c for h, c in secs}
    out = dict(fields)
    if "领域地图" in incoming_headings:
        out["map_ready"] = "true" if _section_has_content(smap.get("领域地图", "")) else "false"
    if "第一性原理" in incoming_headings:
        out["principles_n"] = str(_count_principles(smap.get("第一性原理", "")))
    if "最小产物" in incoming_headings:
        path = _find_artifact_path(smap.get("最小产物", ""))
        if path:
            out["artifact"] = path
    return out


def merge_card(existing: str, patch: str) -> str:
    """Section-patch merge: named ## replace, everything else kept."""
    old_fm, old_body = split_front(existing)
    new_fm, new_body = split_front(patch)
    fields = parse_front_fields(old_fm)
    if new_fm.strip():
        incoming = parse_front_fields(new_fm)
        fields = merge_front_fields(fields, incoming)
    fields = migrate_scene(fields)
    merged_body, headings = merge_sections(old_body, new_body)
    fields = apply_derived(fields, headings, merged_body)
    if "bloom" in fields:
        fields["bloom"] = clamp_bloom(fields["bloom"])
    if "open_door" in fields:
        fields["open_door"] = _unquote(fields["open_door"])
    level = _unquote(fields.get("level", "L0"))
    artifact = _unquote(fields.get("artifact", ""))
    if level == "L1" and _empty(artifact):
        raise LearnError("cannot set level L1 without artifact")
    fields["updated"] = date.today().isoformat()
    front = format_front(fields)
    return f"---\n{front}\n---\n{merged_body if merged_body.startswith(chr(10)) else chr(10) + merged_body.lstrip(chr(10))}"


def card_phase(fields: dict[str, str] | str) -> str:
    if isinstance(fields, str):
        block, _ = split_front(fields)
        fields = parse_front_fields(block)
    p = _unquote(fields.get("phase", "") or "")
    return p or "enough"


@dataclass
class DomainCard:
    path: Path
    title: str
    level: str
    status: str
    open_door: str
    session_id: str = ""
    phase: str = "enough"
    next_review: str = ""
    artifact: str = ""

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
    sid = _fm_get(block, "session_id")
    if sid in {"\"\"", "''", "~", "null", "None"}:
        sid = ""
    rel = path.resolve().relative_to(vault.resolve())
    return DomainCard(
        path=rel,
        title=_fm_get(block, "title") or path.stem,
        level=_fm_get(block, "level", "L0") or "L0",
        status=_fm_get(block, "status", "active") or "active",
        open_door=_fm_get(block, "open_door", "first") or "first",
        session_id=sid,
        phase=_fm_get(block, "phase", "enough") or "enough",
        next_review=_fm_get(block, "next_review"),
        artifact=_fm_get(block, "artifact"),
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
    if re.search(r"^session_id:", block, re.M):
        block2 = re.sub(
            r"^session_id:.*$",
            f"session_id: {session_id}",
            block,
            count=1,
            flags=re.M,
        )
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
        nxt = card.next_review or "-"
        art = card.artifact or "-"
        lines.append(
            f"{card.level:3}  {card.status:8}  "
            f"phase={card.phase:12}  "
            f"door={card.open_door:12}  "
            f"next_review={nxt:10}  "
            f"artifact={art:12}  "
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

    Drops slash-command / 保存 / 开课 protocol lines. Dirty speaker labels
    are refused by save_learn, not washed here.
    """
    out: list[str] = []
    for para in split_paragraphs(text):
        if _ASSIST.match(para) or _USER.match(para):
            continue
        if is_protocol_noise(para):
            continue
        if para:
            out.append(para)
    return out


def resolve_learn_note(vault: Path, note: str) -> str:
    """--note must be the real existing domain-card path. No stem fallback."""
    rel = note.replace("\\", "/").lstrip("/")
    dest = vault / rel
    if dest.is_file() and parse_card(dest, vault) is not None:
        return dest.resolve().relative_to(vault.resolve()).as_posix()
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
    """Archive a readable lecture and section-patch the domain card."""
    if not (chat or "").strip():
        raise LearnError("learn save requires the lecture text (原文)")
    if lecture_is_dirty(chat):
        raise LearnError(
            "dirty lecture refused (用户：/助手：/孔明：/ /learn); "
            "do not wash a chat log and treat it as 讲解"
        )
    if "gobs_type: domain" not in body:
        raise LearnError("learn save body must be a domain card (gobs_type: domain)")
    lecture = "\n\n".join(prepare_lecture(chat))
    if not lecture.strip():
        raise LearnError("learn save 原文 is empty after removing protocol lines")
    vault_path = resolve_learn_vault(vault)
    rel = resolve_learn_note(vault_path, note)
    existing = (vault_path / rel).read_text(encoding="utf-8")
    merged = merge_card(existing, body)
    phase = card_phase(merged)
    try:
        return save_note(
            note=rel,
            body=merged,
            chat=lecture,
            vault=vault_path,
            title=title,
            day=day,
            lecture=True,
            phase=phase,
        )
    except SaveError as exc:
        raise LearnError(str(exc)) from exc


def boot_prompt(
    rel_note: str,
    title: str,
    *,
    resume: bool = False,
    level: str = "L0",
    phase: str = "enough",
) -> str:
    section = PHASE_SECTION.get(phase, PHASE_SECTION["enough"])
    wiki = rel_note.replace(".md", "")
    base = (
        f"先读领域卡 [[{wiki}]]（文件 {rel_note}）的当前 phase 那一节，不要整张卡。"
        f"领域：{title}。档位：{level}。phase：{phase} → 只打开 ## {section}。"
        "一课 = 一个 phase。8 个 phase 是一门课的阶段，不是一课里的课序。"
    )
    retrieve = (
        "先提取再讲（retrieve-first）：上课先让对方从记忆里取已有地图/原理/组块，"
        "不要先复述卡、不要先开讲。"
    )
    teach = (
        "对零基础讲，像默认 gobs 讲解，不像考卷。"
        "encode 课只打 ## 当前组块 里标 current 的那 1 个组块："
        "人话 + 图 + 类比 + 反例 = 四路编码，算 1 个组块。"
        "旧 L0（麻烦 → 例子 → 没有它画糊 → 「只要记住」2～3 句）只用于这 1 个组块。"
        "principles 课最多新上 4 条；卡上总额 3–7，不够 3 就下次 principles 再补。"
        "有论文/原文：概念用原文的词，旁边跟一句这个语境的人话；不要另造正名。"
        "过程课必须 ASCII 画出「有它 / 没有它」；排队课要把印象包被挤画出来，不能只画箭头。定界、判断不要硬画。"
        "论文第一课只吃摘要+引言。配件 vs 整台写进只要记住。"
        "讲完先停：2～3 个图上能指的卡住点，补上再课间确认。不要问 LLM。"
        "L1 只在旧图上贴名字，禁止换故事。"
    )
    sync = (
        "我说「保存」时：把这次课写成一篇可读讲解进归档（像默认 gobs 讲解，不要聊天 log），"
        "同时按 ## 做章节补丁写进领域卡：只交这一 phase 改过的章节，未点名的原样保留。禁止整卡重写。"
        "脏讲义（用户：/助手：/孔明：/ /learn）拒绝，不要洗完当合格。"
        "提取答案只进归档，不进卡。无 artifact 不得把 level 写成 L1。"
    )
    if resume:
        return (
            f"续学模式已打开。{base}{retrieve}"
            f"不要从头讲。先看卡上 phase / open_door，只续当前这一节。"
            f"{teach}{sync}"
        )
    return (
        f"学习模式已打开。{base}{retrieve}"
        "现在是 L0→L1。新课若 phase 是 enough：记下 enough / enough_who / enough_scene / stop；"
        "已经说清就开这一 phase，不要空问。"
        f"{teach}{sync}"
    )


def resolve_learn_vault(vault: Path | None) -> Path:
    return resolve_vault(vault, cwd=Path.cwd())
