# gobs

**gobs** launches an AI CLI against **your own [Obsidian](https://obsidian.md) vault**.

It is a thin Obsidian bridge: open the vault, start Grok, save an explainer or
translation when you ask. Paper work is ordinary notes (`讲解`, bilingual md).
gobs does **not** keep task cards, domain cards, or a lesson tracker in the vault.

You read. The model writes and files — **only when you ask**, and only through
`gobs save`. The chat itself is never dumped into a current note.

Default CLI: [Grok](https://x.ai). gobs is a launcher, not a new chat UI.

Coaching / L0→L1 lessons live in a separate app:
[gobs-learn](https://github.com/wisdom-km/gobs-learn).

**How to use (full walkthrough):** [docs/usage.md](docs/usage.md) ·
[中文](docs/usage.zh.md)

---

## Install

Python 3.10+. Obsidian desktop, [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)
(MCP `http://127.0.0.1:27123/mcp/`), and `grok` on `PATH`.

```bash
pip install git+https://github.com/wisdom-km/gobs.git
# uv tool install git+https://github.com/wisdom-km/gobs.git
```

```powershell
irm https://raw.githubusercontent.com/wisdom-km/gobs/main/install.ps1 | iex
```

```bash
curl -fsSL https://raw.githubusercontent.com/wisdom-km/gobs/main/install.sh | bash
```

Open a **new** terminal after install.

```bash
gobs init "/path/to/your/vault"    # keeps your folders; does not replace AGENTS.md
gobs doctor
gobs                               # open vault, start Grok
```

Empty vault, optional PARA-like skeleton: `gobs init ~/Notes/Vault --skeleton`.

`gobs init` upserts a save-protocol block in `AGENTS.md`, installs
`/save-to-vault`, and creates `99_Archive/transcripts/` if needed.
`--force-agents` is the only way to overwrite `AGENTS.md`.

Private rules (calendar, language, “don’t touch this folder”) stay in **your**
`AGENTS.md`. gobs does not copy API keys; `gobs doctor` checks MCP without
printing tokens.

---

## Daily use

```text
gobs                 # first time: straight into Grok. later: pick n / a number / q
gobs --new           # always new
gobs --resume ID
gobs sessions
```

Talk in Grok with the vault open. Reading and drafting an explainer page is
normal conversation. **Saving** is a separate sentence.

### Save (current note)

In the Grok session say **写进库**, **记下来**, **save to vault**, or
**`/save-to-vault`**.

You get a short current page (conclusions, decisions, follow-ups). The model
searches first, prefers editing an existing note, and files using your
taxonomy (or the optional skeleton). It must call `gobs save`, not paste the
chat.

### Archive (optional original wording)

Say **写进库，连同原文** or **`/save-to-vault including transcript`**.

| File | Where | For |
| --- | --- | --- |
| Distilled note | A current page | You read this |
| Transcript | `99_Archive/transcripts/YYYY-MM-DD-title.md` | Lookup; not “read this today” |

Sentences marked `[pN]` in the distilled note become wikilinks to **that
paragraph** in the transcript. Click in Obsidian to jump back to the original
wording.

Archive is not a calendar event. Home-page “read this today” stays your vault’s
rule.

Power-user CLI and paragraph-id details: [docs/saving.md](docs/saving.md).

---

## Commands

```text
gobs
gobs --new
gobs --resume ID
gobs --no-open
gobs init [vault] [--skeleton] [--force-agents]
gobs save --note REL.md --body-file FILE [--chat-file FILE] [--title NAME]
gobs sessions
gobs doctor
gobs config vault PATH
```

```bash
gobs save --note 30_Lessons/idea.md --body-file distilled.md
gobs save --note 30_Lessons/idea.md --body-file distilled.md --chat-file chat.md --title idea
```

`--note` is vault-relative and cannot contain `..`.

---

## More

- [docs/usage.md](docs/usage.md) — full how-to (setup, talk, save, archive, troubleshooting)
- [docs/usage.zh.md](docs/usage.zh.md) — 中文用法
- [docs/saving.md](docs/saving.md) — save/archive protocol
- [docs/other-clis.md](docs/other-clis.md) — Claude Code, Codex, …

Config: `~/.gobs/config.toml` and `<vault>/.gobs/config.toml`.
Child env: `GOBS=1`, `GOBS_VAULT`, `GOBS_CLI`.

## License

MIT. See [LICENSE](LICENSE).
