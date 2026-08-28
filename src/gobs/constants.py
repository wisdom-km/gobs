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

LEARN_DIR = "22_study/00_learn"
LEARN_SKILL_NAME = "learn"
LEARN_DOMAIN_SKILL_NAME = "learn-domain"

# Johnny Decimal, English, lowercase. 20–24 are standing areas.
SKELETON_DIRS = (
    "00_inbox",
    "10_projects",
    "20_creation",
    "21_metaphysics",
    "22_study",
    LEARN_DIR,
    "23_insights",
    "24_self",
    "30_lessons",
    "40_prompts",
    "50_resources",
    "80_meta",
    "90_archive",
    "90_archive/transcripts",
)

DEFAULT_TRANSCRIPTS = "90_archive/transcripts"
SAVE_SKILL_NAME = "save-to-vault"
VIZ_DIR = "80_meta/gobs-viz"
VIZ_FILES = ("draw.html", "画图.md", "draw.py", "process.html")
PROTOCOL_BEGIN = "<!-- gobs:save-protocol -->"
PROTOCOL_END = "<!-- /gobs:save-protocol -->"
LEARN_PROTOCOL_BEGIN = "<!-- gobs:learn-protocol -->"
LEARN_PROTOCOL_END = "<!-- /gobs:learn-protocol -->"


def user_config_path() -> Path:
    return Path.home() / APP_DIRNAME / USER_CONFIG_NAME


def vault_config_path(vault: Path) -> Path:
    return vault / APP_DIRNAME / VAULT_CONFIG_NAME


def user_sessions_path() -> Path:
    return Path.home() / APP_DIRNAME / "sessions.json"
