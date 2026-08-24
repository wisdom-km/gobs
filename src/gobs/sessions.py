"""Tag and list sessions launched through gobs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

from gobs.constants import user_sessions_path


def grok_home() -> Path:
    import os

    raw = os.environ.get("GROK_HOME")
    return Path(raw).expanduser() if raw else Path.home() / ".grok"


def encode_cwd(cwd: Path) -> str:
    return quote(str(cwd.resolve()), safe="")


def session_group_dir(cwd: Path) -> Path:
    return grok_home() / "sessions" / encode_cwd(cwd)


def _load_registry() -> dict:
    path = user_sessions_path()
    if not path.is_file():
        return {"sessions": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"sessions": {}}
    if not isinstance(data, dict) or "sessions" not in data:
        return {"sessions": {}}
    return data


def _save_registry(data: dict) -> None:
    path = user_sessions_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tag_session(session_id: str, vault: Path) -> None:
    data = _load_registry()
    data["sessions"][session_id] = {
        "vault": str(vault.resolve()),
        "tagged_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_registry(data)


def tagged_ids_for_vault(vault: Path) -> set[str]:
    want = str(vault.resolve())
    data = _load_registry()
    out: set[str] = set()
    for sid, meta in data.get("sessions", {}).items():
        if isinstance(meta, dict) and meta.get("vault") == want:
            out.add(sid)
    return out


def list_session_dirs(cwd: Path) -> list[Path]:
    group = session_group_dir(cwd)
    if not group.is_dir():
        return []
    return [p for p in group.iterdir() if p.is_dir() and (p / "summary.json").is_file()]


def read_summary(session_dir: Path) -> dict:
    path = session_dir / "summary.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def session_mtime(session_dir: Path) -> float:
    summary = session_dir / "summary.json"
    updates = session_dir / "updates.jsonl"
    times = []
    for p in (summary, updates):
        try:
            times.append(p.stat().st_mtime)
        except OSError:
            pass
    return max(times) if times else 0.0


def snapshot(cwd: Path) -> dict[str, float]:
    return {p.name: session_mtime(p) for p in list_session_dirs(cwd)}


def new_or_updated(cwd: Path, before: dict[str, float]) -> list[str]:
    after = snapshot(cwd)
    found: list[str] = []
    for sid, mtime in after.items():
        if sid not in before or mtime > before[sid] + 0.05:
            found.append(sid)
    return found


def listed_gobs_sessions(vault: Path) -> list[dict]:
    """Tagged sessions for this vault, newest first, with titles from Grok."""
    tagged = tagged_ids_for_vault(vault)
    rows: list[dict] = []
    for d in list_session_dirs(vault):
        if d.name not in tagged:
            continue
        summary = read_summary(d)
        info = summary.get("info") or {}
        title = (
            summary.get("generated_title")
            or summary.get("session_summary")
            or d.name[:8]
        )
        recap = summary.get("last_recap") or summary.get("last_turn_summary") or ""
        rows.append(
            {
                "id": d.name,
                "title": title,
                "recap": recap if isinstance(recap, str) else "",
                "updated": summary.get("updated_at") or summary.get("last_active_at") or "",
                "mtime": session_mtime(d),
                "cwd": info.get("cwd"),
            }
        )
    rows.sort(key=lambda r: r["mtime"], reverse=True)
    return rows


def decode_group_name(name: str) -> str:
    return unquote(name)


def pick_session(rows: list[dict], *, input_fn=input) -> str | None:
    """Interactive picker. None = new session. Raises SystemExit on quit."""
    print()
    print("  n   new session")
    if not rows:
        print("  (no previous gobs sessions for this vault)")
    for i, row in enumerate(rows, start=1):
        recap = (row.get("recap") or "").replace("\n", " ").strip()
        extra = f"  — {recap[:72]}" if recap else ""
        print(f"  {i:<3} {row['title']}{extra}")
    print("  q   quit")
    print()
    while True:
        choice = input_fn("gobs> ").strip().lower()
        if choice in {"n", "new"} or (choice == "" and not rows):
            return None
        if choice in {"q", "quit"}:
            raise SystemExit(0)
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(rows):
                return str(rows[idx - 1]["id"])
        print("type n, q, or a number from the list")
