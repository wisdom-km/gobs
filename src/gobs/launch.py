"""Launch the configured AI CLI inside a vault."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from gobs.config import GobsConfig, load_user_config, load_vault_config, resolve_vault
from gobs.obsidian import open_vault, wait_for_mcp


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


def launch(
    vault: Path | None = None,
    *,
    cli: str | None = None,
    open_obsidian: bool | None = None,
    extra_args: list[str] | None = None,
    wait: bool = True,
) -> int:
    cwd = Path.cwd()
    vault_path = resolve_vault(vault, cwd=cwd) if vault is not None else resolve_vault(None, cwd=cwd)
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

    command = _cli_command(cli_name)
    env = os.environ.copy()
    env["GOBS"] = "1"
    env["GOBS_VAULT"] = str(vault_path)
    env["GOBS_CLI"] = cli_name
    argv = [command, "--cwd", str(vault_path)] if cli_name == "grok" else [command]
    if extra_args:
        argv.extend(extra_args)

    print(f"gobs: exec  {' '.join(argv)}")
    if wait:
        return subprocess.call(argv, cwd=str(vault_path), env=env)
    subprocess.Popen(argv, cwd=str(vault_path), env=env)
    return 0
