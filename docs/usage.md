# How to use gobs

gobs is a **launcher**, not a chat app. You run `gobs` in a terminal. It opens
your Obsidian vault, waits for MCP, then starts **Grok** (or another CLI) with
that vault as the working directory. You talk to Grok. Grok reads and writes
the vault. You only file notes when you ask.

The human **reads**. The model **writes and files**.

A longer save/archive spec is in [saving.md](saving.md). Other CLIs:
[other-clis.md](other-clis.md).

---

## 1. One-time setup

### Need

- Python 3.10+
- [Obsidian](https://obsidian.md) desktop
- Community plugin [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)
  (MCP at `http://127.0.0.1:27123/mcp/`)
- `grok` on `PATH` (default CLI)

### Install gobs

```bash
pip install git+https://github.com/wisdom-km/gobs.git
# or: uv tool install git+https://github.com/wisdom-km/gobs.git
```

Windows:

```powershell
irm https://raw.githubusercontent.com/wisdom-km/gobs/main/install.ps1 | iex
```

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/wisdom-km/gobs/main/install.sh | bash
```

Open a **new** terminal after install so `PATH` picks up `gobs`.

### Point it at your vault

Existing vault (keeps your folders; does not replace `AGENTS.md`):

```bash
gobs init "/path/to/your/vault"
gobs doctor
```

Empty folder, optional skeleton (`00_inbox`, `10_projects`, …):

```bash
gobs init ~/Notes/Vault --skeleton
```

`gobs init` will:

- Upsert a `<!-- gobs:save-protocol -->` block into `AGENTS.md` (full overwrite
  only with `--force-agents`)
- Install `.grok/skills/save-to-vault/SKILL.md` → slash command `/save-to-vault`
- Create `90_archive/transcripts/` if missing
- Remember the vault in `~/.gobs/config.toml`

Put **your** rules (language, calendar, “don’t touch this folder”) in
**your** `AGENTS.md`. gobs does not ship those.

Wire Grok to the same MCP URL in `~/.grok/config.toml`. gobs never copies API
keys. `gobs doctor` reports whether the plugin, HTTP port, and Grok MCP exist
(it will not print the token).

---

## 2. Every day: talk

```bash
gobs
```

What happens:

1. Obsidian opens this vault in the background (not attached to the terminal).
2. gobs waits until `http://127.0.0.1:27123/mcp/` answers.
3. If you have **no** previous gobs sessions → Grok starts immediately
   (“open it and you’re in the conversation”).
4. If you **do** → a short picker: `n` new, a number to resume, `q` quit.

Also:

```text
gobs --new              # always a new session
gobs --resume <id>      # resume a tagged id
gobs sessions           # list tagged sessions
gobs --no-open          # skip launching Obsidian
```

A little coding inside a gobs session still counts as a gobs session.

In the conversation you read notes together, ask questions, and let the model
draft explanations **in the vault** when that is the work (for example a
paper explainer page). That is reading and writing current notes — not
“save/archive”. Save is a separate, explicit step.

---

## 3. Save (distilled note)

When a judgment should still be findable in three days, **say so in the
Grok session** — you do not normally run `gobs save` yourself:

| You say | Effect |
| --- | --- |
| 写进库 / 记下来 / save to vault | Distilled current note only |
| `/save-to-vault` | Same (slash command) |

The model should:

1. Search for an existing page; prefer editing it.
2. File with **your** taxonomy if you have one, otherwise the optional
   skeleton (see below).
3. Write a short page (conclusions, decisions, follow-ups) via `gobs save`.
4. **Not** paste the chat into README, daily notes, or Lessons.

You then open the path it reports in Obsidian.

### Optional skeleton (only if you used `--skeleton`)

| Situation | Folder |
| --- | --- |
| Unclear | `00_inbox/` |
| It will end | `10_projects/` |
| Creation | `20_creation/` |
| Metaphysics | `21_metaphysics/` |
| Study | `22_study/` |
| Learn fallback | `22_study/00_learn/` |
| Insights | `23_insights/` |
| Self | `24_self/` |
| Still true across projects | `30_lessons/` |
| Reusable prompt | `40_prompts/` |
| PDFs / originals | `50_resources/` |
| Vault mechanics | `80_meta/` |
| Transcripts / cold notes | `90_archive/` |

If the vault already has a taxonomy, the model follows **yours**.

---

## 4. Archive (optional full transcript)

When you also want the original wording, add that in the same breath:

| You say | Effect |
| --- | --- |
| 写进库，连同原文 | Distilled note **plus** archived transcript |
| `/save-to-vault including transcript` | Same |

Two files:

| File | Where | Role |
| --- | --- | --- |
| Distilled note | A current page in your taxonomy | What you read |
| Transcript | `90_archive/transcripts/YYYY-MM-DD-title.md` | Lookup only — not “read this today” |

Key sentences in the distilled note link to the **matching paragraph** in the
transcript (`[p2]` → `[[90_archive/transcripts/…#^gobs-YYYYMMDD-2]]`). In
Obsidian, click the link to jump to the original wording.

Archive is **not** a calendar event and is **not** the home-page “read this
today” line. Those stay your own vault rules.

---

## 5. CLI (power users / debugging)

You can run the writer yourself. `--note` is vault-relative and cannot
contain `..`.

Distilled only:

```bash
gobs save --note 30_lessons/idea.md --body-file distilled.md
```

With transcript. Paragraphs in `chat.md` are separated by blank lines.
`[p2]` in the distilled file becomes a wikilink to paragraph 2:

```bash
gobs save --note 30_lessons/idea.md --body-file distilled.md --chat-file chat.md --title idea
```

If there are no `[pN]` markers, gobs appends a single Source link to
paragraph 1.

---

## 6. Command list

```text
gobs                      launch (picker only if tagged sessions exist)
gobs --new
gobs --resume ID
gobs init [vault] [--skeleton] [--force-agents]
gobs save --note REL.md --body-file FILE [--chat-file FILE] [--title NAME]
gobs sessions
gobs doctor
gobs config
gobs config vault PATH
```

---

## 7. If something’s off

| Symptom | What to try |
| --- | --- |
| `gobs` not found | New terminal; `python -m gobs -V` |
| Opens Obsidian but not Grok | Update gobs (≥ the detach / skip-empty-picker fix). First launch should print `gobs: new session — starting grok` |
| Obsidian installer logs in the terminal | Old gobs used `os.startfile`; current build detaches the process |
| Model pastes the whole chat into a note | Remind it: 写进库 must use `/save-to-vault` / `gobs save` |
| `gobs doctor` warns about MCP | Enable Local REST API, open this vault, add Grok MCP with your own bearer token |
| Wrong vault | `gobs config vault /path/to/vault` |

`gobs doctor` should look like: vault ok, `AGENTS.md` ok, skill `/save-to-vault`
ok, transcripts dir ok, grok on PATH, Obsidian MCP auth set (no token printed),
plugin present, HTTP up.
