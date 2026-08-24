"""Launch the configured AI CLI inside a vault."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from gobs.config import GobsConfig, load_user_config, load_vault_config, resolve_vault
from gobs.obsidian import open_vault, wait_for_mcp
from gobs.sessions import listed_gobs_sessions, new_or_updated, pick_session, snapshot, tag_session


class LaunchError(RuntimeError):
    pass


def _cli_command(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    if sys.platform == "win32":
        for extra in (f"{name}.cmd", f"{name}.exe", f"{name}.bat"):
            path = shutil.which(extra)
            if path:
                return path
    raise LaunchError(
        f"CLI {name!r} not found on PATH. Install it, or pass --cli <command>."
    )


def _resume_already(extra: list[str] | None) -> bool:
    args = extra or []
    flags = {"--resume", "-r", "--continue", "-c"}
    return any(a in flags or a.startswith("--resume=") for a in args)


def launch(
    vault: Path | None = None,
    *,
    cli: str | None = None,
    open_obsidian: bool | None = None,
    extra_args: list[str] | None = None,
    wait: bool = True,
    new_session: bool = False,
    resume_id: str | None = None,
) -> int:
    cwd = Path.cwd()
    vault_path = resolve_vault(vault, cwd=cwd)
    if not vault_path.exists():
        raise LaunchError(f"Vault does not exist: {vault_path}")

    user = load_user_config()
    cfg: GobsConfig = load_vault_config(vault_path, user)
    cfg.vault = vault_path
    cli_name = cli or cfg.cli
    should_open = cfg.open_obsidian if open_obsidian is None else open_obsidian

    print(f"gobs: vault {vault_path}")
    print(f"gobs: cli   {cli_name}")

    if should_open:
        try:
            how = open_vault(vault_path)
            print(f"gobs: opened Obsidian ({how})")
        except FileNotFoundError as exc:
            print(f"gobs: {exc}", file=sys.stderr)

        ok, url = wait_for_mcp(cfg.mcp_url, timeout=cfg.mcp_timeout)
        if ok:
            print(f"gobs: endpoint ready {url}")
        else:
            print(
                f"gobs: timed out waiting for {url}. "
                "Start Obsidian with this vault (Local REST API / MCP plugin). Continuing anyway.",
                file=sys.stderr,
            )

    extra = list(extra_args or [])
    picked: str | None = resume_id
    if (
        picked is None
        and not new_session
        and not _resume_already(extra)
        and cli_name == "grok"
        and sys.stdin.isatty()
        and sys.stdout.isatty()
    ):
        rows = listed_gobs_sessions(vault_path)
        picked = pick_session(rows)

    command = _cli_command(cli_name)
    env = os.environ.copy()
    env["GOBS"] = "1"
    env["GOBS_VAULT"] = str(vault_path)
    env["GOBS_CLI"] = cli_name
    argv = [command, "--cwd", str(vault_path)] if cli_name == "grok" else [command]
    if picked and cli_name == "grok":
        argv.extend(["--resume", picked])
    if extra:
        argv.extend(extra)

    print(f"gobs: exec  {' '.join(argv)}")
    before = snapshot(vault_path) if cli_name == "grok" else {}
    if wait:
        code = subprocess.call(argv, cwd=str(vault_path), env=env)
    else:
        subprocess.Popen(argv, cwd=str(vault_path), env=env)
        return 0

    if cli_name == "grok":
        for sid in new_or_updated(vault_path, before):
            tag_session(sid, vault_path)
        if picked:
            tag_session(picked, vault_path)
    return code
