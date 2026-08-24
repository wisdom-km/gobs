"""Check that a vault can be used with gobs."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from gobs.config import load_user_config, load_vault_config, resolve_vault
from gobs.constants import AGENTS_NAME, OBS_MARKER
from gobs.obsidian import endpoint_up, find_obsidian_executable


def doctor(vault: Path | None = None) -> int:
    errors = 0

    def ok(msg: str) -> None:
        print(f"  ok   {msg}")

    def bad(msg: str) -> None:
        nonlocal errors
        errors += 1
        print(f"  fail {msg}")

    def warn(msg: str) -> None:
        print(f"  warn {msg}")

    print("gobs doctor")
    try:
        vault_path = resolve_vault(vault, cwd=Path.cwd())
        ok(f"vault {vault_path}")
    except FileNotFoundError as exc:
        bad(str(exc))
        return 1

    if (vault_path / OBS_MARKER).is_dir():
        ok(f"{OBS_MARKER}/ present")
    else:
        bad(f"not an Obsidian vault (missing {OBS_MARKER}/). Run `gobs init`.")

    if (vault_path / AGENTS_NAME).is_file():
        ok(f"{AGENTS_NAME} present")
    else:
        warn(f"no {AGENTS_NAME} — the CLI will not see gobs conventions. Run `gobs init`.")

    cfg = load_vault_config(vault_path, load_user_config())
    transcripts = vault_path / cfg.transcripts
    if transcripts.is_dir():
        ok(f"transcripts {cfg.transcripts}")
    else:
        warn(f"transcripts dir missing ({cfg.transcripts})")

    grok = shutil.which("grok") or (shutil.which("grok.cmd") if sys.platform == "win32" else None)
    if grok:
        ok(f"grok {grok}")
    else:
        warn("grok not on PATH (required for the default CLI)")

    exe = find_obsidian_executable()
    if exe:
        ok(f"obsidian {exe}")
    else:
        warn("Obsidian executable not found; URI handler may still work")

    if endpoint_up(cfg.mcp_url) or endpoint_up("http://127.0.0.1:27123/"):
        ok(f"HTTP {cfg.mcp_url}")
    else:
        warn(f"nothing listening at {cfg.mcp_url} (open this vault in Obsidian)")

    print("gobs doctor: " + ("all good" if errors == 0 else f"{errors} error(s)"))
    return 1 if errors else 0
