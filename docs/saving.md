# Save and archive

This is the protocol behind 「写进库」. Humans usually only **say** the
phrases below inside a gobs session. The model (via `/save-to-vault`) must
call `gobs save`. It must not paste the chat into a current note.

How this fits the rest of the app: [usage.md](usage.md) ·
[中文](usage.zh.md).

---

## Two products, one command

| Intent | What you say | What is written |
| --- | --- | --- |
| Distilled only | 写进库, 记下来, save to vault, `/save-to-vault` | One **current** note |
| Distilled + original wording | 写进库，连同原文, `/save-to-vault including transcript` | Current note **and** a transcript under `99_Archive/transcripts/` |

The current note is for reading. The transcript is lookup-only. Do not put
transcript files on a home “read this today” line.

### Learn mode

Inside `/learn`, saying **保存** / 写进库 / 记下来 is **both** rows at once:
a **readable lecture** (same bar as a default gobs 讲解 page, not a chat
log) goes to transcripts, and the distilled block goes onto the topic’s
domain card. The skill must call:

```bash
gobs learn save --note CARD.md --body-file CARD.md --chat-file LECTURE.md --title NAME
```

`--chat-file` is required and must be lecture markdown (`##` headings +
body), not `/learn` / `用户：` / `助手：` turns. `--note` is an existing
domain card (a `15_Learn/NAME.md` argument still finds a moved card). See
[learn.zh.md](learn.zh.md).

---

## Distilled note

- Short: conclusions, decisions, follow-ups. One judgment per page when that
  matches the vault.
- Search first. Prefer editing an existing page.
- Match the vault’s language and frontmatter.
- After a sentence that should jump to transcript paragraph N, write `[pN]`
  (1-based, paragraphs split on blank lines).

---

## `gobs save`

`--note` is vault-relative. It cannot contain `..` or land outside the vault.

```bash
gobs save --note 30_Lessons/idea.md --body-file distilled.md
gobs save --note 30_Lessons/idea.md --body-file distilled.md --chat-file chat.md --title idea
```

With `--chat-file`:

1. Write `99_Archive/transcripts/YYYY-MM-DD-slug.md` (folder overridable via
   `transcripts` in `.gobs/config.toml`).
2. Stamp each paragraph with `^gobs-YYYYMMDD-N`.
3. Replace `[pN]` in the distilled note with
   `[[99_Archive/transcripts/YYYY-MM-DD-slug#^gobs-YYYYMMDD-N]]`.
4. If there is no `[pN]`, append `Source: [[…#^gobs-YYYYMMDD-1]]`.

---

## What the skill does

`.grok/skills/save-to-vault/SKILL.md` is installed by `gobs init`. Triggers:
写进库, 记下来, save to vault, write this down, `/save-to-vault`.

It searches, chooses a path, writes temp files, runs `gobs save`, and reports
the path. It does not update a home page or calendar unless **your**
`AGENTS.md` says so and the human asked.

---

## Filing

If the vault used `gobs init --skeleton`, use the table in `AGENTS.md`
(`00_Inbox` … `99_Archive`). Otherwise follow the vault’s own taxonomy.
File automatically when the path is obvious; ask only when it is not, with
one or two concrete paths — never “please pick a folder from the tree”.
