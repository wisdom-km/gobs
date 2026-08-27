"""Write a distilled note and an optional paragraph-linked transcript."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from gobs.config import load_user_config, load_vault_config, resolve_vault

CITE_RE = re.compile(r"\[p(\d+)\]", re.IGNORECASE)


class SaveError(ValueError):
    pass


@dataclass
class SaveResult:
    note: Path
    transcript: Path | None
    cites: int


def _safe_rel(vault: Path, rel: str) -> Path:
    raw = rel.replace("\\", "/").lstrip("/")
    dest = (vault / raw).resolve()
    try:
        dest.relative_to(vault.resolve())
    except ValueError as exc:
        raise SaveError(f"note path escapes the vault: {rel}") from exc
    if dest == vault.resolve():
        raise SaveError("note path must be a file inside the vault")
    return dest


def split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in parts if p.strip()]


def slugify(title: str, limit: int = 40) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title.strip(), flags=re.UNICODE)
    s = s.strip("-") or "session"
    return s[:limit].rstrip("-")


def stamp_transcript(
    paragraphs: list[str],
    day: str,
    *,
    id_on_own_line: bool = False,
) -> tuple[str, list[str]]:
    """Return (markdown, list of block ids)."""
    ids: list[str] = []
    chunks: list[str] = []
    for i, para in enumerate(paragraphs, start=1):
        bid = f"gobs-{day}-{i}"
        ids.append(bid)
        if id_on_own_line:
            chunks.append(f"{para}\n\n^{bid}")
        else:
            chunks.append(f"{para} ^{bid}")
    body = "\n\n".join(chunks) + "\n"
    return body, ids


def replace_cites(body: str, ids: list[str], wiki_base: str) -> tuple[str, int]:
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        n = int(match.group(1))
        if n < 1 or n > len(ids):
            return match.group(0)
        count += 1
        return f"[[{wiki_base}#^{ids[n - 1]}]]"

    return CITE_RE.sub(repl, body), count


def save_note(
    *,
    note: str,
    body: str,
    chat: str | None = None,
    vault: Path | None = None,
    title: str | None = None,
    day: str | None = None,
    lecture: bool = False,
) -> SaveResult:
    vault_path = resolve_vault(vault)
    cfg = load_vault_config(vault_path, load_user_config())
    dest = _safe_rel(vault_path, note)
    dest.parent.mkdir(parents=True, exist_ok=True)

    day = day or date.today().isoformat().replace("-", "")
    iso = date.today().isoformat()
    transcript_path: Path | None = None
    cites = 0
    text = body

    if chat and chat.strip():
        paragraphs = split_paragraphs(chat)
        if not paragraphs:
            raise SaveError("transcript is empty")
        md, ids = stamp_transcript(
            paragraphs, day, id_on_own_line=lecture
        )
        slug = slugify(title or dest.stem)
        tdir = vault_path / cfg.transcripts
        tdir.mkdir(parents=True, exist_ok=True)
        transcript_path = tdir / f"{iso}-{slug}.md"
        if lecture:
            header = f"# {title or dest.stem} · {iso} 讲解\n\n"
        else:
            header = f"# Transcript {iso} — {title or dest.stem}\n\n"
        transcript_path.write_text(header + md, encoding="utf-8")
        wiki = f"{cfg.transcripts}/{transcript_path.stem}".replace("\\", "/")
        text, cites = replace_cites(text, ids, wiki)
        if cites == 0:
            text = text.rstrip() + f"\n\nSource: [[{wiki}#^{ids[0]}]]\n"

    dest.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return SaveResult(note=dest, transcript=transcript_path, cites=cites)
