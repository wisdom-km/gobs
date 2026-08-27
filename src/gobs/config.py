"""User-level and vault-level config."""

from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from gobs.constants import (
    DEFAULT_CLI,
    DEFAULT_MCP_TIMEOUT,
    DEFAULT_MCP_URL,
    DEFAULT_TRANSCRIPTS,
    LEARN_DIR,
    OBS_MARKER,
    user_config_path,
    vault_config_path,
)

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore


@dataclass
class GobsConfig:
    vault: Path | None = None
    cli: str = DEFAULT_CLI
    mcp_url: str = DEFAULT_MCP_URL
    open_obsidian: bool = True
    mcp_timeout: int = DEFAULT_MCP_TIMEOUT
    transcripts: str = DEFAULT_TRANSCRIPTS
    learn: str = LEARN_DIR


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    return data if isinstance(data, dict) else {}


def _apply(base: GobsConfig, data: dict[str, Any], *, relative_to: Path | None = None) -> GobsConfig:
    vault = base.vault
    raw_vault = data.get("vault")
    if isinstance(raw_vault, str) and raw_vault.strip():
        p = Path(raw_vault).expanduser()
        vault = p if p.is_absolute() else ((relative_to or Path.cwd()) / p)
        vault = vault.resolve()

    cli = str(data["cli"]).strip() if data.get("cli") else base.cli
    mcp_url = str(data["mcp_url"]).strip() if data.get("mcp_url") else base.mcp_url
    transcripts = (
        str(data["transcripts"]).strip() if data.get("transcripts") else base.transcripts
    )
    learn = str(data["learn"]).strip() if data.get("learn") else base.learn
    open_obsidian = (
        bool(data["open_obsidian"]) if "open_obsidian" in data else base.open_obsidian
    )
    timeout = data.get("mcp_timeout", base.mcp_timeout)
    try:
        mcp_timeout = int(timeout)
    except (TypeError, ValueError):
        mcp_timeout = base.mcp_timeout

    return replace(
        base,
        vault=vault,
        cli=cli or base.cli,
        mcp_url=mcp_url or base.mcp_url,
        open_obsidian=open_obsidian,
        mcp_timeout=mcp_timeout,
        transcripts=transcripts or base.transcripts,
        learn=learn or base.learn,
    )


def load_user_config() -> GobsConfig:
    return _apply(GobsConfig(), _read_toml(user_config_path()))


def load_vault_config(vault: Path, base: GobsConfig | None = None) -> GobsConfig:
    cfg = base or GobsConfig(vault=vault.resolve())
    return _apply(cfg, _read_toml(vault_config_path(vault)), relative_to=vault)


def find_vault(start: Path) -> Path | None:
    """Walk up from start looking for a `.obsidian` directory."""
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in (cur, *cur.parents):
        if (candidate / OBS_MARKER).is_dir():
            return candidate
    return None


def resolve_vault(explicit: str | Path | None, *, cwd: Path | None = None) -> Path:
    """Resolve the vault path from CLI arg, user config, or cwd walk."""
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_absolute():
            p = (cwd or Path.cwd()) / p
        p = p.resolve()
        found = find_vault(p)
        return found or p

    user = load_user_config()
    if user.vault:
        return user.vault

    found = find_vault(cwd or Path.cwd())
    if found:
        return found
    raise FileNotFoundError(
        "No vault configured. Pass a path, run `gobs init`, or set vault in ~/.gobs/config.toml."
    )


def dump_toml(values: dict[str, Any]) -> str:
    lines = ["# gobs config", ""]
    for key, value in values.items():
        if value is None:
            continue
        if isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        elif isinstance(value, int):
            lines.append(f"{key} = {value}")
        else:
            text = str(value).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key} = "{text}"')
    lines.append("")
    return "\n".join(lines)


def write_user_config(cfg: GobsConfig) -> Path:
    path = user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    values: dict[str, Any] = {
        "cli": cfg.cli,
        "mcp_url": cfg.mcp_url,
        "open_obsidian": cfg.open_obsidian,
        "mcp_timeout": cfg.mcp_timeout,
        "transcripts": cfg.transcripts,
    }
    if cfg.vault is not None:
        values["vault"] = str(cfg.vault)
    path.write_text(dump_toml(values), encoding="utf-8")
    return path


def write_vault_config(vault: Path, cfg: GobsConfig) -> Path:
    path = vault_config_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    values = {
        "cli": cfg.cli,
        "transcripts": cfg.transcripts,
        "mcp_url": cfg.mcp_url,
        "learn": cfg.learn,
    }
    path.write_text(dump_toml(values), encoding="utf-8")
    return path
