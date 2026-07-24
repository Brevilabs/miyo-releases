---
name: miyo-search
description: >-
  Search and read the user's personal knowledge base from the command line with
  the local `miyo` CLI — their own notes and documents, plus their saved ChatGPT /
  Claude conversations. Reach for this whenever a request could be answered from
  something the user wrote, saved, decided, or discussed before, even when they
  don't mention "Miyo," "notes," or a filename: "what did I decide about X", "find
  my doc on Y", "what did I ask ChatGPT about Z", "summarize what I have on …",
  "did I already write something about …". Also for listing/inspecting their
  indexed files and folders. Commands: `miyo search`, `miyo files`, `miyo folders`.
  (To convert a PDF to text, use the separate `miyo-parse` skill.)
---

# Miyo CLI

Miyo is a local-first knowledge tool. It indexes the user's notes, documents, and
saved AI chats into a local vector database and exposes **hybrid semantic search**
(dense + sparse, fused with RRF) over them. The `miyo` CLI is a thin client over a
local HTTP service — everything stays on the user's machine.

**Reach for it whenever the answer likely lives in the user's *own* material**
rather than your training data or the open web — including questions that never say
"Miyo" or "notes" ("what did we land on for the pricing model?", "have I written
about this already?"). When in doubt, search: it's cheap, and answering from your own
guess when the user has a real note on it is the failure mode to avoid.

## Prerequisites (check once)

The CLI ships *with* the **Miyo desktop app**, which also runs the local service the
CLI queries. Invocation differs by OS below; the `miyo` subcommands are identical
everywhere.

**1. Invoke `miyo` by its full path**

Don't rely on `miyo` being on PATH. An agent that wasn't started from a terminal (an
editor running it over ACP, say) can inherit a bare environment that never sources the
user's shell rc files, so a plain `miyo` fails on a perfectly good install. Invoke the
CLI by its full install path instead — the form depends on the shell:

| Shell | Full invocation (replaces `miyo`) |
|---|---|
| macOS / Linux (bash, zsh) | `~/.miyo/bin/miyo` |
| Windows PowerShell | `& "$env:LOCALAPPDATA\Miyo\bin\miyo\miyo.exe"` |
| Windows cmd | `"%LOCALAPPDATA%\Miyo\bin\miyo\miyo.exe"` |

The examples below write plain `miyo` for brevity; swap in the full form for your shell
(`%LOCALAPPDATA%` only expands in cmd, so PowerShell must use `$env:LOCALAPPDATA`). Each
command runs in a fresh shell, so don't stash it in a variable — write the path out.

If that path doesn't exist, fall back to a bare `miyo` — a non-standard install may
still be on PATH. Only when both fail is Miyo actually missing: **tell the user to
install it from https://miyo.md/ and launch the app once** — first launch installs the
`miyo` CLI.

If the full path is present but still fails,
[references/troubleshooting.md](references/troubleshooting.md) has the PATH fixes.

**2. Is the service up?**

Don't run a separate health probe — the first real command *is* the readiness check.
Every service-backed `miyo` command opens the same local connection, so if the
service is down it exits `1` with **"Cannot connect to Miyo service / Is the Miyo app
running?"**. That means the app isn't running: **ask the user to open it** (or
download it from https://miyo.md/). It never means "the user has no notes about this."

Inside a sandboxed coding agent (e.g. Codex), that local connection counts as network
access and may prompt for approval the first time `miyo` runs — a separate `curl`
would only add a second prompt.
[references/troubleshooting.md](references/troubleshooting.md) covers allowing it
once, and pointing the CLI at a non-default or remote service (`MIYO_URL`,
Tailscale).

## Commands at a glance

| Command | Purpose |
|---|---|
| `miyo search <query>` | Semantic search over documents or saved chats |
| `miyo files` | List indexed files, with filters |
| `miyo folders` | List indexed folders + indexing status |

(Converting a PDF to text is a separate skill — `miyo-parse`.)

Global behavior: every service-backed command takes `--json` (machine-readable
output) and `--url` (override the service URL). Exit code `0` = success, `1` =
error. Dates are `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`.
(`miyo mcp` also exists but is **deprecated** — don't use or recommend it.)

## A worked example

User: *"What did we decide about rate-limiting the ingest API?"* — a question about a
past decision, so the answer is likely in the user's own notes, not yours.

```bash
# 1. Search the user's documents for the decision.
miyo search --json -n 5 "rate limiting the ingest API decision"
#    → results[0].path = "eng/ingest-api.md"
#      results[0].content = "...settled on a token bucket, 100 req/s per key..."

# 2. The snippet is often enough to answer. If you need fuller context, read the
#    file from disk — resolve the folder's absolute path, then open the file.
miyo folders --json        # → folders[].absolute_path, e.g. /Users/me/Notes
#    read /Users/me/Notes/eng/ingest-api.md
```

Then answer **from what you found**, citing `eng/ingest-api.md`. The pattern —
*search → trust the user's material over your own guess → cite the path → read the
file when the snippet is thin* — is the core of using Miyo well.

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

Results are grouped by file: each hit shows a path and a matching snippet — an
excerpt, not the whole file (the worked example above shows how to read the full
file). Full flag reference, filtering by path/date, and output shapes:
[references/search.md](references/search.md).

## Browsing what's indexed

Use these to scope a search or to answer "what do I have on disk":

```bash
miyo folders                       # folders Miyo watches + how far indexing got
miyo files --title "roadmap"       # find files by title/path without a semantic query
miyo files --order-by mtime -n 10  # 10 most-recently-modified files
```

Details and JSON shapes: [references/files-and-folders.md](references/files-and-folders.md).

## Guidance for agents

- **Don't fabricate.** Treat results as the user's ground truth and cite the file
  path a fact came from. If search returns nothing, say so plainly rather than
  filling the gap from general knowledge — and consider whether the other `--source`
  or looser filters would find it.
- **Use `--json` when you parse.** Human output is for display; `--json` is stable
  for scripting.
