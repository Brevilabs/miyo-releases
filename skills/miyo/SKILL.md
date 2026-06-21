---
name: miyo
description: >-
  Search the user's personal knowledge base from the command line with the local
  `miyo` CLI — their own notes and documents, and their saved ChatGPT / Claude
  conversations. Use whenever a request could be answered from something the user
  wrote, saved, or discussed before: "what did I note about X", "find my doc on
  Y", "what did I ask ChatGPT about Z", "summarize my notes on …", or when they
  want to list or inspect their indexed files and folders. Commands: `miyo
  search`, `miyo files`, `miyo folders`.
---

# Miyo CLI

Miyo is a local-first knowledge tool. It indexes the user's notes, documents, and
saved AI chats into a local vector database and exposes **hybrid semantic search**
(dense + sparse, fused with RRF) over them. The `miyo` CLI is a thin client over a
local HTTP service — everything stays on the user's machine.

Reach for it when the answer likely lives in the user's *own* material rather than
your training data or the open web.

Miyo has **two** agent interfaces. This skill is about the first; use whichever fits
where you run:

- **The local CLI** (`miyo …`) — for an agent on the **same machine** as the Miyo
  app. Read-only, no auth, lowest latency. *This is the one you almost always want.*
- **The remote MCP** (via the hosted relay) — for **cloud** AI clients (ChatGPT,
  claude.ai) that aren't on the user's machine; it also adds write tools. See
  [references/remote-mcp.md](references/remote-mcp.md).

> The old local stdio MCP server (`miyo mcp`) is **deprecated** — don't use or
> recommend it. On-machine, call the CLI; off-machine, use the remote MCP.

## Prerequisites (check once)

The CLI talks to a local service that the **Miyo desktop app** runs. Confirm both
the binary and the service before relying on results:

```bash
command -v miyo                                   # binary on PATH?
curl -s --max-time 2 http://127.0.0.1:8742/v0/health   # service up? expect {"status":"ok",...}
```

- The app installs `miyo` to `~/.miyo/bin/miyo` (macOS/Linux) or
  `%LOCALAPPDATA%\Miyo\bin\miyo.exe` (Windows) on first launch and adds it to PATH;
  a brand-new install needs one terminal restart.
- If `curl` fails or `miyo` prints **"Cannot connect to Miyo service / Is the Miyo
  app running?"**, the desktop app isn't running. Ask the user to open it — don't
  treat an empty result as "the user has no notes about this." See
  [references/troubleshooting.md](references/troubleshooting.md).

## Commands at a glance

| Command | Purpose |
|---|---|
| `miyo search <query>` | Semantic search over documents or saved chats |
| `miyo files` | List indexed files, with filters |
| `miyo folders` | List indexed folders + indexing status |

(`miyo mcp` also exists but is **deprecated** — see above.)

Global behavior: every command takes `--json` (machine-readable output) and `--url`
(override the service URL). Exit code `0` = success, `1` = error. Dates are
`YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`.

## The main workflow: search

```bash
miyo search "kubernetes ingress notes"          # default: the user's documents
miyo search --source chats "tax question I asked ChatGPT"
miyo search -n 5 --json "quarterly planning"    # top 5, parsed programmatically
```

Two **separate** corpora, chosen with `--source` (never combined):

- `documents` (default) — the user's own notes and files.
- `chats` — saved ChatGPT and Claude conversations. Use this whenever the user
  refers to a past AI conversation ("the chat where we designed the schema").

If you're unsure which corpus holds the answer, search `documents`, then `chats`.

Results are grouped by file: each hit shows a path and a matching snippet. The
snippet is an excerpt, not the whole file — to read full content, open the file on
disk (resolve the folder's absolute path via `miyo folders`, then read the file).
Full flag reference, filtering by path/date, and output shapes:
[references/search.md](references/search.md).

## Browsing what's indexed

Use these to scope a search or to answer "what do I have on disk":

```bash
miyo folders                       # folders Miyo watches + how far indexing got
miyo files --title "roadmap"       # find files by title/path without a semantic query
miyo files --order-by mtime -n 10  # 10 most-recently-modified files
```

Details and JSON shapes: [references/files-and-folders.md](references/files-and-folders.md).

## The other interface: remote MCP

For **cloud** AI clients (ChatGPT, claude.ai) that can't run the CLI, Miyo is
reachable as a remote MCP server through the hosted relay — same search engine, plus
write tools (`create_file`, `edit_file`, `sync_chats`). It's enabled by the user in
the desktop app, not by an agent. What it offers and how it's set up:
[references/remote-mcp.md](references/remote-mcp.md).

## Guidance for agents

- **Don't fabricate.** Treat results as the user's ground truth. Cite the file path
  you got a fact from. If search returns nothing, say so plainly rather than
  filling the gap from general knowledge.
- **Pick the right corpus.** A question about "what I discussed/asked" → `--source
  chats`. A question about "my notes/docs" → `documents`.
- **Use `--json` when you parse.** Human output is for display; `--json` is stable
  for scripting (`results[]`, each `{path, content}`).
- **Keep queries conceptual.** This is semantic search — natural-language intent
  beats exact keywords. Narrow with `--path` / `--mtime-*` instead of stuffing the
  query.
