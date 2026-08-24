"""Initialize a vault with gobs conventions."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from gobs.config import (
    GobsConfig,
    load_user_config,
    write_user_config,
    write_vault_config,
)
from gobs.constants import AGENTS_NAME, OBS_MARKER, SKELETON_DIRS


def _template(name: str) -> str:
    return files("gobs.templates").joinpath(name).read_text(encoding="utf-8")


def init_vault(
    vault: Path,
    *,
    skeleton: bool = False,
    force_agents: bool = False,
    set_default: bool = True,
    cli: str | None = None,
) -> dict[str, str]:
    """Create gobs files in `vault`. Never deletes user notes.

    Returns a map of relative path → action (`created`, `skipped`, `updated`).
    """
    vault = vault.expanduser().resolve()
    vault.mkdir(parents=True, exist_ok=True)
    actions: dict[str, str] = {}

    obs = vault / OBS_MARKER
    if not obs.exists():
        obs.mkdir(parents=True, exist_ok=True)
        actions[OBS_MARKER] = "created"
    else:
        actions[OBS_MARKER] = "skipped"

    if skeleton:
        for rel in SKELETON_DIRS:
            d = vault / rel
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                keep = d / ".gitkeep"
                if not keep.exists():
                    keep.write_text("", encoding="utf-8")
                actions[rel] = "created"
            else:
                actions[rel] = "skipped"
        home = vault / "README.md"
        if not home.exists():
            home.write_text(_template("HOME.md"), encoding="utf-8")
            actions["README.md"] = "created"
        else:
            actions["README.md"] = "skipped"

    agents = vault / AGENTS_NAME
    if agents.exists() and not force_agents:
        actions[AGENTS_NAME] = "skipped"
    else:
        existed = agents.exists()
        agents.write_text(_template("AGENTS.md"), encoding="utf-8")
        actions[AGENTS_NAME] = "updated" if existed else "created"

    user = load_user_config()
    cfg = GobsConfig(
        vault=vault,
        cli=cli or user.cli,
        mcp_url=user.mcp_url,
        open_obsidian=user.open_obsidian,
        mcp_timeout=user.mcp_timeout,
        transcripts=user.transcripts,
    )
    write_vault_config(vault, cfg)
    actions[".gobs/config.toml"] = "updated"

    if set_default:
        user.vault = vault
        if cli:
            user.cli = cli
        write_user_config(user)
        actions["~/.gobs/config.toml"] = "updated"

    transcripts = vault / cfg.transcripts
    if not transcripts.exists():
        transcripts.mkdir(parents=True, exist_ok=True)
        keep = transcripts / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        actions[cfg.transcripts] = "created"
    elif cfg.transcripts not in actions:
        actions[cfg.transcripts] = "skipped"

    return actions
