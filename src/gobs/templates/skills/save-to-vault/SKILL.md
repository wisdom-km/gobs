---
name: save-to-vault
description: >
  Save a distilled vault note (and optional paragraph-linked transcript) with
  `gobs save`. Use when the user says 写进库, 记下来, save to vault, write this
  down, or runs /save-to-vault. Never dump the raw chat into a current note.
user-invocable: true
argument-hint: "[including transcript]"
---

# Save to vault

The human asked to file this conversation. You are the archivist. Use **`gobs save`**;
do not paste the chat into a current note yourself.

## Steps

1. Confirm they want a save. If they also said "including transcript" / 连同原文 /
   `原文`, set `WITH_TRANSCRIPT=1`. Otherwise distilled only.
2. Search the vault for an existing page on this topic. Prefer editing that path.
   If none, pick a path using the vault's taxonomy (or the gobs skeleton table in
   `AGENTS.md`). File automatically when sure; ask only when unsure, offering
   one or two concrete paths.
3. Write a short distilled markdown file in a temp path (one judgment, match the
   vault's language and frontmatter). Put `[pN]` immediately after any sentence
   that should jump to transcript paragraph N (1-based).
4. If `WITH_TRANSCRIPT=1`, write the relevant chat (user + assistant, skip tool
   noise) to a second temp file. Separate paragraphs with blank lines. Paragraph
   1 is `[p1]`.
5. Run, from the vault:

   ```bash
   gobs save --note RELATIVE/PATH.md --body-file DISTILLED.md
   ```

   With transcript:

   ```bash
   gobs save --note RELATIVE/PATH.md --body-file DISTILLED.md --chat-file CHAT.md --title "short title"
   ```

6. Tell the human the note path (and transcript path if any). Do not update a
   home "read this today" line unless they asked.

## Do not

- Dump the full chat into `README.md`, daily notes, or Lessons.
- Create empty folders "for completeness".
- Invent a new taxonomy when the vault already has one.
