# Using gobs with other AI CLIs

v1 of **gobs** is tested with Grok. The vault conventions (`AGENTS.md`, optional
skeleton, transcript folder, `.gobs/config.toml`) are CLI-agnostic.

## How it works

`gobs --cli <name>` looks up `<name>` on `PATH` and runs it with:

- working directory = the vault
- `GOBS=1`, `GOBS_VAULT`, `GOBS_CLI` in the environment

Grok additionally gets `--cwd <vault>`. Other CLIs are expected to treat the
process working directory as the project root.

## Claude Code

1. `gobs init` writes `AGENTS.md`. Claude Code already loads `AGENTS.md` /
   `CLAUDE.md` from the project root.
2. Configure Obsidian MCP (or Local REST API) in Claude Code the same way you
   would for any MCP server, pointing at `http://127.0.0.1:27123/mcp/`.
3. Launch:

   ```bash
   gobs --cli claude
   ```

   or `gobs config cli claude` then `gobs`.

4. Open the vault in Obsidian first (or let gobs open it) so MCP can connect.

Optional: add a one-line `CLAUDE.md` that says “follow AGENTS.md” if you want
an explicit Claude file. gobs does not create `CLAUDE.md` so it will not fight
an existing one.

## Codex / other project-root CLIs

Same pattern: init the vault, configure MCP on that CLI, then

```bash
gobs --cli codex
gobs --cli aider
```

If the CLI has no “project rules” file besides `AGENTS.md`, paste the gobs
template (or a short pointer to it) wherever that CLI reads instructions.

## What gobs does not do yet

- A native TUI
- Bundled MCP credentials
- Automatic plugin install inside Obsidian
- Guaranteed welcome-screen filtering for CLIs that ignore working directory

If a CLI ignores cwd, pass its own “open this folder” flag after `--`:

```bash
gobs --cli some-cli -- --project .
```
