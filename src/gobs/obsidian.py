"""Open Obsidian and wait until the local HTTP/MCP endpoint answers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

from gobs.constants import DEFAULT_MCP_URL, DEFAULT_REST_URL

WINDOWS_EXE_CANDIDATES = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "Obsidian" / "Obsidian.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "obsidian" / "Obsidian.exe",
    Path(r"G:\BaseWare\Obsidian\Obsidian.exe"),
    Path(r"C:\Program Files\Obsidian\Obsidian.exe"),
)


def vault_uri(vault: Path) -> str:
    # Obsidian wants an encoded absolute path; slashes as %2F work on all OSes.
    posix = vault.resolve().as_posix()
    if sys.platform == "win32" and len(posix) >= 2 and posix[1] == ":":
        # D:/Notes/Vault → D:%2FNotes%2FVault
        posix = posix[0] + ":" + posix[2:]
    return "obsidian://open?path=" + quote(posix, safe=":")


def _open_uri(uri: str) -> bool:
    try:
        if sys.platform == "win32":
            os.startfile(uri)  # type: ignore[attr-defined]
            return True
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        if shutil.which(opener):
            subprocess.Popen([opener, uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    except OSError:
        return False
    return False


def find_obsidian_executable() -> Path | None:
    which = shutil.which("obsidian") or shutil.which("Obsidian")
    if which:
        return Path(which)
    if sys.platform == "darwin":
        app = Path("/Applications/Obsidian.app")
        if app.exists():
            return app
    for candidate in WINDOWS_EXE_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def open_vault(vault: Path) -> str:
    """Open `vault` in Obsidian. Returns a short description of how it was opened."""
    uri = vault_uri(vault)
    if _open_uri(uri):
        return f"uri {uri}"

    exe = find_obsidian_executable()
    if exe is None:
        raise FileNotFoundError(
            "Could not open Obsidian. Install it, or start the vault yourself, then retry."
        )
    if sys.platform == "darwin" and exe.suffix == ".app":
        subprocess.Popen(["open", "-a", str(exe), str(vault)])
        return f"open -a {exe}"
    subprocess.Popen([str(exe), str(vault)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"exe {exe}"


def endpoint_up(url: str, timeout: float = 1.5) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read(64)
        return True
    except urllib.error.HTTPError:
        # Server spoke HTTP (401/404 still means Obsidian is up).
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_for_mcp(
    mcp_url: str = DEFAULT_MCP_URL,
    *,
    timeout: float = 30,
    rest_url: str = DEFAULT_REST_URL,
) -> tuple[bool, str]:
    """Poll Local REST API / MCP until something answers.

    Returns (ok, which_url).
    """
    deadline = time.monotonic() + timeout
    urls = []
    for u in (mcp_url, rest_url):
        if u and u not in urls:
            urls.append(u)
    last = urls[0] if urls else mcp_url
    while time.monotonic() < deadline:
        for url in urls:
            if endpoint_up(url):
                return True, url
            last = url
        time.sleep(0.4)
    return False, last
