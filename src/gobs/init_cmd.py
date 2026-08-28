"""Initialize a vault with gobs conventions."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from gobs.config import (
    GobsConfig,
    load_user_config,
    load_vault_config,
    write_user_config,
    write_vault_config,
)
from gobs.constants import (
    AGENTS_NAME,
    LEARN_DIR,
    LEARN_DOMAIN_SKILL_NAME,
    LEARN_PROTOCOL_BEGIN,
    LEARN_PROTOCOL_END,
    LEARN_SKILL_NAME,
    OBS_MARKER,
    PROTOCOL_BEGIN,
    PROTOCOL_END,
    SAVE_SKILL_NAME,
    SKELETON_DIRS,
    VIZ_DIR,
    VIZ_FILES,
)
from gobs.learn import learn_dir as resolve_learn_dir


def _templates_root() -> Path:
    return Path(__file__).resolve().parent / "templates"


def _template_bytes(*parts: str) -> bytes:
    """Read package data as bytes (html + md). importlib.files first, else disk."""
    try:
        return files("gobs.templates").joinpath(*parts).read_bytes()
    except (FileNotFoundError, ModuleNotFoundError, TypeError, AttributeError, IsADirectoryError):
        return _templates_root().joinpath(*parts).read_bytes()


def _template_file(*parts: str) -> str:
    return _template_bytes(*parts).decode("utf-8")


def _template(name: str) -> str:
    return _template_file(name)


def upsert_marked_block(existing: str, block: str, begin: str, end: str) -> str:
    block = block.strip() + "\n"
    start = existing.find(begin)
    stop = existing.find(end)
    if start != -1 and stop != -1 and stop > start:
        stop += len(end)
        return existing[:start].rstrip() + "\n\n" + block + existing[stop:].lstrip("\n")
    if existing.strip():
        return existing.rstrip() + "\n\n" + block
    return block


def upsert_protocol_block(existing: str, block: str) -> str:
    return upsert_marked_block(existing, block, PROTOCOL_BEGIN, PROTOCOL_END)


def install_skill(vault: Path, name: str) -> str:
    dest_dir = vault / ".grok" / "skills" / name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"
    text = _template_file("skills", name, "SKILL.md")
    existed = dest.exists()
    dest.write_text(text, encoding="utf-8")
    return "updated" if existed else "created"



def install_viz(vault: Path) -> dict[str, str]:
    """Copy viz templates (draw.html, process.html, figure.json, 画图.md, draw.py) into 80_meta/gobs-viz/."""
    dest_dir = vault / VIZ_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    actions: dict[str, str] = {}
    for name in VIZ_FILES:
        dest = dest_dir / name
        data = _template_bytes("viz", name)
        existed = dest.exists()
        dest.write_bytes(data)
        actions[f"{VIZ_DIR}/{name}"] = "updated" if existed else "created"
    return actions


def install_save_skill(vault: Path) -> str:
    return install_skill(vault, SAVE_SKILL_NAME)


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

    learn = resolve_learn_dir(vault)
    learn_rel = learn.resolve().relative_to(vault.resolve()).as_posix()
    if not learn.exists():
        learn.mkdir(parents=True, exist_ok=True)
        keep = learn / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        actions[learn_rel] = "created"
    else:
        actions[learn_rel] = "skipped"

    if skeleton:
        for rel in SKELETON_DIRS:
            d = vault / rel
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                keep = d / ".gitkeep"
                if not keep.exists():
                    keep.write_text("", encoding="utf-8")
                actions[rel] = "created"
            elif rel not in actions:
                actions[rel] = "skipped"
        home = vault / "README.md"
        if not home.exists():
            home.write_text(_template("HOME.md"), encoding="utf-8")
            actions["README.md"] = "created"
        else:
            actions["README.md"] = "skipped"

    protocol = _template("save_protocol.md")
    learn_protocol = _template("learn_protocol.md")
    agents = vault / AGENTS_NAME
    if force_agents or not agents.exists():
        existed = agents.exists()
        full = (
            _template("AGENTS.md").rstrip()
            + "\n\n"
            + protocol.strip()
            + "\n\n"
            + learn_protocol.strip()
            + "\n"
        )
        agents.write_text(full, encoding="utf-8")
        actions[AGENTS_NAME] = "updated" if existed else "created"
    else:
        before = agents.read_text(encoding="utf-8")
        after = upsert_protocol_block(before, protocol)
        after = upsert_marked_block(
            after, learn_protocol, LEARN_PROTOCOL_BEGIN, LEARN_PROTOCOL_END
        )
        if after != before:
            agents.write_text(after, encoding="utf-8")
            actions[AGENTS_NAME] = "updated"
        else:
            actions[AGENTS_NAME] = "skipped"

    actions[f".grok/skills/{SAVE_SKILL_NAME}/SKILL.md"] = install_save_skill(vault)
    actions[f".grok/skills/{LEARN_SKILL_NAME}/SKILL.md"] = install_skill(
        vault, LEARN_SKILL_NAME
    )
    actions[f".grok/skills/{LEARN_DOMAIN_SKILL_NAME}/SKILL.md"] = install_skill(
        vault, LEARN_DOMAIN_SKILL_NAME
    )

    actions.update(install_viz(vault))

    user = load_user_config()
    existing = load_vault_config(vault, user)
    cfg = GobsConfig(
        vault=vault,
        cli=cli or user.cli,
        mcp_url=user.mcp_url,
        open_obsidian=user.open_obsidian,
        mcp_timeout=user.mcp_timeout,
        transcripts=existing.transcripts,
        learn=existing.learn,
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
