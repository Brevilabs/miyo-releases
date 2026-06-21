# `miyo search` — semantic search

Hybrid semantic + keyword search over the user's indexed material, fused with
Reciprocal Rank Fusion. Returns the passages most relevant to a natural-language
query, grouped by source file.

```
miyo search [options] <query>
```

`<query>` is everything not consumed by a flag, joined with spaces — quoting is
optional but recommended. A query is required.

## Options

| Flag | Default | Meaning |
|---|---|---|
| `-n, --limit <n>` | `20` | Max file results. Clamped to `1`–`1000`. |
| `--source <documents\|chats>` | `documents` | Which corpus to search (see below). |
| `--path <text>` | — | Keep only results whose path contains `<text>` (partial, case-insensitive). **Repeatable** — multiple `--path` flags OR together. |
| `--mtime-after <date>` | — | Only files modified on/after the date. |
| `--mtime-before <date>` | — | Only files modified on/before the date. |
| `--json` | off | Emit JSON instead of formatted text. |
| `--url <url>` | service discovery | Override the service URL (else `MIYO_URL`, else the running app, else `http://127.0.0.1:8742`). |
| `-h, --help` | — | Print usage. |

Dates accept `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS` (a `T` separator also works).
Invalid dates error out with exit code `1`.

## Sources: documents vs chats

The two corpora live in separate collections and are **never** searched together.

- `documents` — the user's own notes and files (the default, the primary corpus).
- `chats` — conversations the user saved from ChatGPT (`chatgpt.com`) and Claude
  (`claude.ai`).

Choose `chats` whenever the user points at a past AI conversation: "what did I ask
ChatGPT about…", "find the Claude chat where we…", "in an earlier conversation the
assistant suggested…". Otherwise use `documents`. When unsure, run both.

## Output

**Human-readable (default):** results grouped by file.

```
Found 2 file result(s) from 5 chunk hit(s) (142ms):

1. notes/infra/kubernetes.md
   ...ingress controllers terminate TLS at the edge; we standardized on...

2. archive/2025/ops-runbook.md
   ...the ingress class must be set explicitly or the controller ignores...
```

No matches prints `No results found.` (exit code still `0` — an empty result is a
valid answer, not an error).

**JSON (`--json`):**

```json
{
  "results": [
    { "path": "notes/infra/kubernetes.md", "content": "...excerpt..." },
    { "path": "archive/2025/ops-runbook.md", "content": "...excerpt..." }
  ],
  "count": 2,
  "chunk_count": 5,
  "execution_time_ms": 142
}
```

Parse `results[]`; each entry is `{ path, content }`. `count` is files returned,
`chunk_count` is the number of underlying chunk hits before grouping.

## The `content` field is a snippet, not the file

Each result's `content` is the matching excerpt(s), not the whole document. To get
full text:

- **Read it off disk** (the local-agent path). Results are the user's real files.
  Resolve the folder's `absolute_path` from `miyo folders`, join it with the result
  `path`, and read the file directly.
- **Use the remote MCP `read_file` tool** if you're a cloud client driving Miyo over
  the relay — it takes a path and returns full content (text, or base64 for images).
  See [remote-mcp.md](remote-mcp.md). (The CLI itself has no read command.)

## Recipes

```bash
# Top 5, scoped to a subtree, recent only
miyo search -n 5 --path "work/" --mtime-after 2026-01-01 "migration plan"

# OR across two subtrees
miyo search --path "notes/" --path "archive/" "postmortem"

# A past ChatGPT conversation, parsed
miyo search --source chats --json "the prompt we wrote for the classifier"

# Against a non-default service (e.g. a dev instance)
miyo search --url http://127.0.0.1:9999 "test query"
```

## Tips

- Phrase queries by **intent**, not keywords — semantic search rewards
  natural-language descriptions of what you're looking for.
- Narrow with `--path` / `--mtime-*` rather than overloading the query string.
- Raise `-n` when you need recall (feeding many candidates to a summarizer); keep
  it low when you want the single best hit.
