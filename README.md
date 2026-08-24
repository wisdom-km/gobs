# gobs

**gobs** launches an AI CLI against **your own [Obsidian](https://obsidian.md) vault**.

The human reads. The model writes and files — and only when you ask it to save.

v1 is a **launcher**, not a new chat UI. The default CLI is [Grok](https://github.com/xai-org/grok). Other CLIs can use the same vault files; see [docs/other-clis.md](docs/other-clis.md).

## What it does

```text
gobs              # open the vault in Obsidian, wait for MCP, start grok there
gobs init         # add conventions to an existing vault (does not rewrite your folders)
gobs init --skeleton   # optional 00_Inbox / 10_Projects / … layout for empty vaults
gobs doctor       # check vault, grok, Obsidian
```

Sessions started from `gobs` use the vault as the working directory, so the CLI welcome / resume list is **that vault’s** conversations. A little coding inside a gobs session still counts as a gobs session.

## Install

Python 3.10+:

```bash
pip install git+https://github.com/wisdom-km/gobs.git
```

From a clone:

```bash
pip install -e .
```

You also need:

- [Obsidian](https://obsidian.md)
- The [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) community plugin (MCP at `http://127.0.0.1:27123/` by default)
- `grok` on `PATH` (or another CLI via `--cli`)

Point Grok at the same MCP URL in `~/.grok/config.toml` — gobs does not copy API keys.

## Quick start

Existing vault (keeps your folders and `AGENTS.md`):

```bash
gobs init "/path/to/your/vault"
gobs doctor
gobs
```

New / empty folder, with the optional skeleton:

```bash
gobs init ~/Notes/Vault --skeleton
```

That creates, only if missing:

```text
00_Inbox/   10_Projects/   20_Areas/   30_Lessons/
40_Prompts/ 50_Resources/  90_Meta/    99_Archive/transcripts/
README.md   AGENTS.md      .gobs/config.toml
```

Existing files are never overwritten unless you pass `--force-agents`.

## Saving to the vault

Nothing is written until you say so, for example:

- “save to vault”
- “write this down”
- “save to vault including transcript”

**Current notes** get a distilled page (conclusions, decisions, follow-ups).  
**Full chat** (optional) goes under `99_Archive/transcripts/` and is not daily reading.  
Key sentences in the distilled note should link to the **matching paragraph** in the transcript (`#^block-id`).

Filing: if you use the skeleton, the model follows the table in `AGENTS.md`. If you already have a taxonomy, it follows **yours**. It files on its own when the path is obvious, and asks only when it is not.

## Config

User defaults: `~/.gobs/config.toml`

```toml
vault = "/path/to/your/vault"
cli = "grok"
mcp_url = "http://127.0.0.1:27123/mcp/"
open_obsidian = true
mcp_timeout = 30
transcripts = "99_Archive/transcripts"
```

Per-vault overrides: `<vault>/.gobs/config.toml`

```bash
gobs config vault /path/to/your/vault
gobs --cli grok
gobs --no-open          # skip launching Obsidian
gobs -- --continue      # extra args go to the CLI (Grok: resume last session)
```

Environment set on the child process: `GOBS=1`, `GOBS_VAULT`, `GOBS_CLI`.

## What gobs is not

- Not a new TUI (later).
- Not a binder to one vendor’s model.
- Not your private vault rules. Put calendar IDs, language, “don’t touch this folder” in **your** `AGENTS.md`. The template only encodes: *human reads, AI writes, save on request, distilled notes plus optional paragraph-linked transcripts*.

## License

MIT. See [LICENSE](LICENSE).

中文说明：[README.zh.md](README.zh.md)
