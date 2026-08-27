---
name: save-to-vault
description: >
  Save a distilled vault note (and optional paragraph-linked transcript) with
  `gobs save`. In /learn mode, 保存 archives a readable lecture AND updates the
  topic’s domain card via `gobs learn save`. Use when the user says 保存,
  写进库, 记下来, save to vault, write this down, or runs /save-to-vault.
  Never dump the raw chat into a current note.
user-invocable: true
argument-hint: "[including transcript]"
---

# Save to vault

The human asked to file this conversation. You are the archivist. Do not paste
the chat into a current note yourself.

## Learn mode

If this session is in `/learn` (coach mode, `GOBS_LEARN=1`, or an active
`15_Learn/` card): **保存 / 写进库 / 记下来** means a **readable lecture**
into transcripts **and** the current block onto the domain card. The lecture
must read like a default gobs 讲解 page, not a chat log. Follow the **learn**
skill and run `gobs learn save`. Do not write a separate Lessons page. Do not
ask twice.

## Steps (not in learn mode)

1. Confirm they want a save. If they also said "including transcript" / 连同原文 /
   `原文`, set `WITH_TRANSCRIPT=1`. Otherwise distilled only. Use **`gobs save`**.
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
