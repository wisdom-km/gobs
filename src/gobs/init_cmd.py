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
from gobs.constants import (
    AGENTS_NAME,
    OBS_MARKER,
    PROTOCOL_BEGIN,
    PROTOCOL_END,
    SAVE_SKILL_NAME,
    SKELETON_DIRS,
)


def _template_file(*parts: str) -> str:
    try:
        return files("gobs.templates").joinpath(*parts).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        root = Path(__file__).resolve().parent / "templates"
        return root.joinpath(*parts).read_text(encoding="utf-8")


def _template(name: str) -> str:
    return _template_file(name)


def upsert_protocol_block(existing: str, block: str) -> str:
    block = block.strip() + "\n"
    start = existing.find(PROTOCOL_BEGIN)
    end = existing.find(PROTOCOL_END)
    if start != -1 and end != -1 and end > start:
        end += len(PROTOCOL_END)
        return existing[:start].rstrip() + "\n\n" + block + existing[end:].lstrip("\n")
    if existing.strip():
        return existing.rstrip() + "\n\n" + block
    return block


def install_save_skill(vault: Path) -> str:
    dest_dir = vault / ".grok" / "skills" / SAVE_SKILL_NAME
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"
    text = _template_file("skills", "save-to-vault", "SKILL.md")
    existed = dest.exists()
    dest.write_text(text, encoding="utf-8")
    return "updated" if existed else "created"


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

    protocol = _template("save_protocol.md")
    agents = vault / AGENTS_NAME
    if force_agents or not agents.exists():
        existed = agents.exists()
        full = _template("AGENTS.md").rstrip() + "\n\n" + protocol.strip() + "\n"
        agents.write_text(full, encoding="utf-8")
        actions[AGENTS_NAME] = "updated" if existed else "created"
    else:
        before = agents.read_text(encoding="utf-8")
        after = upsert_protocol_block(before, protocol)
        if after != before:
            agents.write_text(after, encoding="utf-8")
            actions[AGENTS_NAME] = "updated"
        else:
            actions[AGENTS_NAME] = "skipped"

    actions[f".grok/skills/{SAVE_SKILL_NAME}/SKILL.md"] = install_save_skill(vault)

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
