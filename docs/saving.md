# Saving notes from a gobs session

The model should follow `AGENTS.md` in the vault. This page is for humans.

## Distilled note (always, when you ask to save)

A short page: the judgment, the decision, the follow-up. Not the chat.

Prefer editing a page that already exists. Search first.

## Transcript (only if you ask)

Stored under `99_Archive/transcripts/` by default (override with
`transcripts` in `.gobs/config.toml`).

Give the file a dated name, for example `2026-08-25-topic.md`.

Put a **block id** on the paragraph that the distilled note should jump to:

```markdown
Original wording the human cares about. ^gobs-20260825-1
```

In the distilled note:

```markdown
See the original wording: [[99_Archive/transcripts/2026-08-25-topic#^gobs-20260825-1]]
```

Do not add transcript files to the vault home “read this today” line.
