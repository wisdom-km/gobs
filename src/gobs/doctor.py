"""Check that a vault can be used with gobs."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from gobs.config import load_user_config, load_vault_config, resolve_vault
from gobs.constants import AGENTS_NAME, OBS_MARKER, SAVE_SKILL_NAME
from gobs.obsidian import endpoint_up, find_obsidian_executable

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore


def _grok_config_path() -> Path:
    import os

    raw = os.environ.get("GROK_HOME")
    home = Path(raw).expanduser() if raw else Path.home() / ".grok"
    return home / "config.toml"


def _mcp_status() -> tuple[str, str]:
    """Return (level, message). Never prints secrets."""
    path = _grok_config_path()
    if not path.is_file():
        return "warn", f"no {_posix(path)} — add an Obsidian MCP server in Grok"
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except OSError:
        return "warn", f"could not read {path}"
    servers = data.get("mcp_servers")
    if not isinstance(servers, dict):
        return "warn", "Grok config has no [mcp_servers] — Obsidian MCP is not connected"
    hits = []
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            continue
        url = str(spec.get("url") or "")
        if "obsidian" in name.lower() or "27123" in url or "/mcp" in url:
            auth = spec.get("headers") if isinstance(spec.get("headers"), dict) else {}
            has_auth = any(
                str(k).lower() == "authorization" and str(v).strip()
                for k, v in auth.items()
            )
            enabled = spec.get("enabled", True)
            bits = [f"server {name!r}"]
            if url:
                bits.append(url.split("?")[0])
            if not enabled:
                bits.append("disabled")
            bits.append("auth set" if has_auth else "no auth header")
            hits.append(", ".join(bits))
    if not hits:
        return (
            "warn",
            "no Obsidian MCP in ~/.grok/config.toml. Example:\n"
            "         grok mcp add --transport http obsidian http://127.0.0.1:27123/mcp/ "
            '--header "Authorization: Bearer YOUR_LOCAL_REST_API_KEY"',
        )
    return "ok", "; ".join(hits)


def _plugin_status(vault: Path) -> tuple[str, str]:
    community = vault / OBS_MARKER / "community-plugins.json"
    plugin_dir = vault / OBS_MARKER / "plugins" / "obsidian-local-rest-api"
    names: list[str] = []
    if community.is_file():
        try:
            names = json.loads(community.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            names = []
    has_name = isinstance(names, list) and "obsidian-local-rest-api" in names
    has_dir = plugin_dir.is_dir()
    if has_name or has_dir:
        return "ok", "obsidian-local-rest-api plugin present"
    return (
        "warn",
        "Local REST API plugin not found. In Obsidian: Community plugins → "
        "Local REST API (MCP is at http://127.0.0.1:27123/mcp/)",
    )


def _posix(path: Path) -> str:
    return str(path)


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

    skill = vault_path / ".grok" / "skills" / SAVE_SKILL_NAME / "SKILL.md"
    if skill.is_file():
        ok(f"skill /{SAVE_SKILL_NAME}")
    else:
        warn(f"no /{SAVE_SKILL_NAME} skill — run `gobs init` (writes .grok/skills/)")

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

    level, msg = _mcp_status()
    (ok if level == "ok" else warn)(msg)

    level, msg = _plugin_status(vault_path)
    (ok if level == "ok" else warn)(msg)

    exe = find_obsidian_executable()
    if exe:
        ok(f"obsidian {exe}")
    else:
        warn("Obsidian executable not found; URI handler may still work")

    if endpoint_up(cfg.mcp_url) or endpoint_up("http://127.0.0.1:27123/"):
        ok(f"HTTP {cfg.mcp_url}")
    else:
        warn(
            f"nothing listening at {cfg.mcp_url}. Open this vault in Obsidian "
            "with Local REST API enabled."
        )

    print("gobs doctor: " + ("all good" if errors == 0 else f"{errors} error(s)"))
    return 1 if errors else 0
