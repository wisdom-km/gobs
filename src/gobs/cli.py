"""Command-line entry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gobs import __version__
from gobs.config import load_user_config, write_user_config
from gobs.doctor import doctor
from gobs.init_cmd import init_vault
from gobs.launch import LaunchError, launch
from gobs.learn import (
    LearnError,
    bind_session,
    boot_prompt,
    create_domain,
    format_status,
    list_domains,
    parse_card,
    resolve_learn_vault,
    save_learn,
)
from gobs.save import SaveError, save_note
from gobs.sessions import listed_gobs_sessions, new_or_updated, pick_session, snapshot


COMMANDS = {"init", "config", "launch", "doctor", "save", "sessions", "learn"}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gobs",
        description="Launch an AI CLI against your own Obsidian vault.",
    )
    p.add_argument("-V", "--version", action="version", version=f"gobs {__version__}")
    sub = p.add_subparsers(dest="command")

    launch_p = sub.add_parser("launch", help="Open the vault and start the AI CLI (default)")
    launch_p.add_argument("vault", nargs="?", help="Vault path (default: configured vault)")
    launch_p.add_argument("--cli", help="CLI to spawn (default: grok)")
    launch_p.add_argument("--no-open", action="store_true", help="Do not start Obsidian")
    launch_p.add_argument("--new", action="store_true", help="Skip the session picker and start new")
    launch_p.add_argument("-r", "--resume", metavar="ID", help="Resume a gobs/Grok session id")
    launch_p.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the CLI; prefix with --",
    )

    init_p = sub.add_parser("init", help="Add gobs conventions to a vault")
    init_p.add_argument("vault", nargs="?", help="Vault path (default: current directory)")
    init_p.add_argument(
        "--skeleton",
        action="store_true",
        help="Create the optional 00_Inbox / 15_Learn / 10_Projects / … folders if missing",
    )
    init_p.add_argument(
        "--force-agents",
        action="store_true",
        help="Overwrite AGENTS.md with the gobs template",
    )
    init_p.add_argument(
        "--no-default",
        action="store_true",
        help="Do not record this vault as the default in ~/.gobs/config.toml",
    )
    init_p.add_argument("--cli", help="Default CLI name to record")

    cfg_p = sub.add_parser("config", help="Show or set user config")
    cfg_p.add_argument("key", nargs="?", help="vault | cli | mcp_url")
    cfg_p.add_argument("value", nargs="?", help="New value")

    doc_p = sub.add_parser("doctor", help="Check vault, CLI, and Obsidian MCP")
    doc_p.add_argument("vault", nargs="?", help="Vault path")

    save_p = sub.add_parser("save", help="Write a distilled note and optional transcript")
    save_p.add_argument("--note", required=True, help="Vault-relative note path")
    save_p.add_argument("--body-file", help="Distilled markdown (default: stdin)")
    save_p.add_argument("--chat-file", help="Raw conversation; stored as a linked transcript")
    save_p.add_argument("--title", help="Short title used in the transcript filename")
    save_p.add_argument("--vault", help="Vault path (default: configured vault)")

    sess_p = sub.add_parser("sessions", help="List gobs-tagged sessions for the vault")
    sess_p.add_argument("vault", nargs="?", help="Vault path")

    learn_p = sub.add_parser("learn", help="L0→L1 coach mode against a domain card")
    learn_sub = learn_p.add_subparsers(dest="learn_cmd")
    start_p = learn_sub.add_parser("start", help="Open or create a domain card, then launch")
    start_p.add_argument("name", help="Domain name, e.g. Transformer or 英语")
    start_p.add_argument("--vault", help="Vault path")
    start_p.add_argument("--cli", help="CLI to spawn")
    start_p.add_argument("--no-open", action="store_true")
    start_p.add_argument("--no-launch", action="store_true", help="Only create/print the card")
    start_p.add_argument(
        "--new",
        action="store_true",
        help="Force a new chat session (ignore card session_id and picker)",
    )
    start_p.add_argument(
        "-r",
        "--resume",
        metavar="ID",
        help="Resume this gobs/Grok session under learn mode",
    )
    stat_p = learn_sub.add_parser("status", help="List domain cards in 15_Learn/")
    stat_p.add_argument("--vault", help="Vault path")
    learn_save = learn_sub.add_parser(
        "save",
        help="In learn mode: archive original chat and write the domain card",
    )
    learn_save.add_argument(
        "--note",
        required=True,
        help="Vault-relative domain card, e.g. 15_Learn/Transformer.md",
    )
    learn_save.add_argument("--body-file", required=True, help="Full updated domain card")
    learn_save.add_argument(
        "--chat-file",
        required=True,
        help="Original conversation; required so 保存 always files 原文",
    )
    learn_save.add_argument("--title", help="Short title used in the transcript filename")
    learn_save.add_argument("--vault", help="Vault path")
    return p


def _normalize_argv(argv: list[str] | None) -> list[str]:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return ["launch"]
    head = args[0]
    if head in COMMANDS or head in {"-h", "--help", "-V", "--version"}:
        return args
    return ["launch", *args]


def _cmd_config(key: str | None, value: str | None) -> int:
    cfg = load_user_config()
    if key is None:
        print(f"vault     = {cfg.vault or '(unset)'}")
        print(f"cli       = {cfg.cli}")
        print(f"mcp_url   = {cfg.mcp_url}")
        print(f"open      = {cfg.open_obsidian}")
        print(f"timeout   = {cfg.mcp_timeout}")
        print(f"transcripts = {cfg.transcripts}")
        return 0
    if value is None:
        print("usage: gobs config <vault|cli|mcp_url> <value>", file=sys.stderr)
        return 2
    if key == "vault":
        cfg.vault = Path(value).expanduser().resolve()
    elif key == "cli":
        cfg.cli = value
    elif key == "mcp_url":
        cfg.mcp_url = value
    else:
        print(f"unknown key {key!r}", file=sys.stderr)
        return 2
    path = write_user_config(cfg)
    print(f"wrote {path}")
    return 0


def _read_text(path: Path | None) -> str:
    if path is None:
        return sys.stdin.read()
    return path.read_text(encoding="utf-8")


def _cmd_save(ns: argparse.Namespace) -> int:
    body = _read_text(Path(ns.body_file) if ns.body_file else None)
    chat = Path(ns.chat_file).read_text(encoding="utf-8") if ns.chat_file else None
    result = save_note(
        note=ns.note,
        body=body,
        chat=chat,
        vault=Path(ns.vault) if ns.vault else None,
        title=ns.title,
    )
    print(f"gobs: wrote {result.note}")
    if result.transcript:
        print(f"gobs: transcript {result.transcript} ({result.cites} paragraph links)")
    return 0


def _cmd_sessions(vault: Path | None) -> int:
    from gobs.config import resolve_vault

    vault_path = resolve_vault(vault, cwd=Path.cwd())
    rows = listed_gobs_sessions(vault_path)
    if not rows:
        print("no gobs sessions tagged for this vault yet")
        return 0
    for row in rows:
        recap = (row.get("recap") or "").replace("\n", " ").strip()
        extra = f"  {recap[:60]}" if recap else ""
        print(f"{row['id']}  {row['title']}{extra}")
    return 0


def _pick_learn_session(
    vault: Path,
    *,
    card_session: str,
    resume_id: str | None,
    force_new: bool,
    cli_name: str,
) -> tuple[str | None, bool]:
    """Return (session_id_or_None, is_resume)."""
    if force_new:
        return None, False
    if resume_id:
        return resume_id, True
    if card_session:
        print(f"gobs learn: card bound to session {card_session}")
        return card_session, True
    if cli_name != "grok":
        return None, False
    rows = listed_gobs_sessions(vault)
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    if not interactive or not rows:
        return None, False
    print("gobs learn: pick a prior session to continue under coach mode, or n for new")
    picked = pick_session(rows)
    if picked:
        return picked, True
    return None, False


def _cmd_learn_save(ns: argparse.Namespace) -> int:
    body = Path(ns.body_file).read_text(encoding="utf-8")
    chat = Path(ns.chat_file).read_text(encoding="utf-8")
    result = save_learn(
        note=ns.note,
        body=body,
        chat=chat,
        vault=Path(ns.vault) if ns.vault else None,
        title=ns.title,
    )
    print(f"gobs: wrote {result.note}")
    if result.transcript:
        print(f"gobs: transcript {result.transcript} ({result.cites} paragraph links)")
    return 0


def _cmd_learn(ns: argparse.Namespace) -> int:
    if ns.learn_cmd == "status":
        vault = resolve_learn_vault(Path(ns.vault) if ns.vault else None)
        print(format_status(list_domains(vault)))
        return 0
    if ns.learn_cmd == "save":
        return _cmd_learn_save(ns)
    if ns.learn_cmd != "start":
        print(
            "usage: gobs learn start <名称> | gobs learn status | "
            "gobs learn save --note 15_Learn/NAME.md --body-file CARD.md --chat-file CHAT.md",
            file=sys.stderr,
        )
        return 2
    vault = resolve_learn_vault(Path(ns.vault) if ns.vault else None)
    rel, action = create_domain(vault, ns.name)
    print(f"gobs learn: {action:8} {rel}")
    card = parse_card(vault / rel, vault)
    title = card.title if card else ns.name
    level = card.level if card else "L0"
    card_session = (card.session_id if card else "") or ""
    if ns.no_launch:
        return 0

    from gobs.config import load_user_config, load_vault_config

    user = load_user_config()
    cfg = load_vault_config(vault, user)
    cli_name = ns.cli or cfg.cli
    resume_id, is_resume = _pick_learn_session(
        vault,
        card_session=card_session,
        resume_id=ns.resume,
        force_new=ns.new,
        cli_name=cli_name,
    )
    if resume_id:
        bind_session(vault, rel, resume_id)
        print(f"gobs learn: bound session {resume_id} → {rel}")

    before = snapshot(vault) if cli_name == "grok" else {}
    code = launch(
        vault,
        cli=ns.cli,
        open_obsidian=False if ns.no_open else None,
        new_session=not is_resume,
        resume_id=resume_id,
        boot_prompt=boot_prompt(
            rel.as_posix(), title, resume=is_resume, level=level
        ),
        learn_note=rel.as_posix(),
    )
    if cli_name == "grok":
        for sid in new_or_updated(vault, before):
            bind_session(vault, rel, sid)
            print(f"gobs learn: bound session {sid} → {rel}")
        if resume_id:
            bind_session(vault, rel, resume_id)
    return code


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    ns = parser.parse_args(_normalize_argv(argv))
    try:
        if ns.command == "init":
            target = Path(ns.vault) if ns.vault else Path.cwd()
            actions = init_vault(
                target,
                skeleton=ns.skeleton,
                force_agents=ns.force_agents,
                set_default=not ns.no_default,
                cli=ns.cli,
            )
            print(f"gobs init {target.resolve()}")
            for rel, action in actions.items():
                print(f"  {action:8} {rel}")
            if actions.get(".obsidian") == "created":
                print("Open this folder in Obsidian once: File → Open folder as vault.")
            return 0
        if ns.command == "config":
            return _cmd_config(ns.key, ns.value)
        if ns.command == "doctor":
            return doctor(Path(ns.vault) if ns.vault else None)
        if ns.command == "save":
            return _cmd_save(ns)
        if ns.command == "sessions":
            return _cmd_sessions(Path(ns.vault) if ns.vault else None)
        if ns.command == "learn":
            return _cmd_learn(ns)
        extra = list(ns.extra or [])
        if extra and extra[0] == "--":
            extra = extra[1:]
        return launch(
            Path(ns.vault) if ns.vault else None,
            cli=ns.cli,
            open_obsidian=False if ns.no_open else None,
            extra_args=extra or None,
            new_session=ns.new,
            resume_id=ns.resume,
        )
    except (LaunchError, FileNotFoundError, SaveError, LearnError) as exc:
        print(f"gobs: {exc}", file=sys.stderr)
        return 1
