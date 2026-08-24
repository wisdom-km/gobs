"""Paths and optional vault skeleton."""

from pathlib import Path

APP_DIRNAME = ".gobs"
USER_CONFIG_NAME = "config.toml"
VAULT_CONFIG_NAME = "config.toml"
OBS_MARKER = ".obsidian"
AGENTS_NAME = "AGENTS.md"
DEFAULT_CLI = "grok"
DEFAULT_MCP_URL = "http://127.0.0.1:27123/mcp/"
DEFAULT_REST_URL = "http://127.0.0.1:27123/"
DEFAULT_MCP_TIMEOUT = 30

SKELETON_DIRS = (
    "00_Inbox",
    "10_Projects",
    "20_Areas",
    "30_Lessons",
    "40_Prompts",
    "50_Resources",
    "90_Meta",
    "99_Archive",
    "99_Archive/transcripts",
)

DEFAULT_TRANSCRIPTS = "99_Archive/transcripts"


def user_config_path() -> Path:
    return Path.home() / APP_DIRNAME / USER_CONFIG_NAME


def vault_config_path(vault: Path) -> Path:
    return vault / APP_DIRNAME / VAULT_CONFIG_NAME
