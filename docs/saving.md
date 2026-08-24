# Saving notes from a gobs session

Humans: say “save to vault” / 「写进库」 or run `/save-to-vault`.
Agents: call **`gobs save`**. Do not paste the chat into a current note.

## Distilled note

A short page. Search first; prefer editing an existing path.

Put `[pN]` after any sentence that should jump to transcript paragraph N
(1-based, blank-line separated).

## CLI

```bash
gobs save --note 30_Lessons/idea.md --body-file distilled.md
gobs save --note 30_Lessons/idea.md --body-file distilled.md --chat-file chat.md --title idea
```

`--note` is vault-relative and cannot contain `..`.

With `--chat-file`, gobs writes `99_Archive/transcripts/YYYY-MM-DD-slug.md`
(override the folder with `transcripts` in `.gobs/config.toml`), stamps
`^gobs-YYYYMMDD-N` on each paragraph, and replaces `[pN]` in the distilled
note with `[[…#^gobs-YYYYMMDD-N]]`. If there are no `[pN]` markers, it appends
a single Source link to paragraph 1.

Do not add transcript files to the home “read this today” line.
