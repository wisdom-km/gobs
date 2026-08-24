# gobs

**gobs** launches an AI CLI against **your own [Obsidian](https://obsidian.md) vault**.

The human reads. The model writes and files — **only when you ask**, and through `gobs save`, not by dumping the chat into a note.

The default CLI is [Grok](https://github.com/xai-org/grok). Other CLIs can use the same vault files; see [docs/other-clis.md](docs/other-clis.md).

## Install

Python 3.10+. One of:

```bash
# pip
pip install git+https://github.com/wisdom-km/gobs.git

# uv
uv tool install git+https://github.com/wisdom-km/gobs.git

# Windows
irm https://raw.githubusercontent.com/wisdom-km/gobs/main/install.ps1 | iex

# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/wisdom-km/gobs/main/install.sh | bash
```

You also need Obsidian, the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) community plugin (MCP at `http://127.0.0.1:27123/mcp/`), and `grok` on `PATH`. gobs does not copy API keys; `gobs doctor` tells you if Grok’s Obsidian MCP is missing.

## Commands

```text
gobs                 # open Obsidian (detached), start grok; picker only if prior gobs sessions exist
gobs --new           # skip the picker, start a new session
gobs --resume ID     # resume a tagged session
gobs init            # conventions + /save-to-vault skill; does not rewrite your folders
gobs init --skeleton # optional 00_Inbox / 10_Projects / … layout for empty vaults
gobs save --note PATH.md --body-file note.md [--chat-file chat.md]
gobs sessions        # list gobs-tagged sessions
gobs doctor          # vault, skill, plugin, Grok MCP, HTTP
```

Sessions launched from `gobs` are tagged. The next `gobs` lists **those** sessions (plus “new”). Coding a little inside a gobs session still counts.

## Quick start

```bash
gobs init "/path/to/your/vault"
gobs doctor
gobs
```

`gobs init` on an existing vault:

- Does **not** replace your `AGENTS.md`. It upserts a marked `gobs:save-protocol` block.
- Installs `.grok/skills/save-to-vault/SKILL.md` (slash command `/save-to-vault`).
- Creates `99_Archive/transcripts/` if missing.

`--force-agents` is the only way to overwrite `AGENTS.md`.

## Saving

Say **「写进库」**, **save to vault**, or run **`/save-to-vault`**.

The skill must call `gobs save`. In the distilled note, mark a citation as `[pN]` to point at transcript paragraph N:

```bash
gobs save --note 30_Lessons/idea.md --body-file distilled.md --chat-file chat.md --title idea
```

`[p2]` becomes `[[99_Archive/transcripts/2026-08-25-idea#^gobs-20260825-2]]`.

Raw chat never belongs in a current note. See [docs/saving.md](docs/saving.md).

## Config

`~/.gobs/config.toml` (user) and `<vault>/.gobs/config.toml` (vault):

```toml
vault = "/path/to/your/vault"
cli = "grok"
mcp_url = "http://127.0.0.1:27123/mcp/"
```

```bash
gobs config vault /path/to/your/vault
gobs --no-open
gobs -- --continue      # extra args after -- go to the CLI
```

Child env: `GOBS=1`, `GOBS_VAULT`, `GOBS_CLI`.

## License

MIT. See [LICENSE](LICENSE).

中文说明：[README.zh.md](README.zh.md)
