---
name: miyo
description: >-
  Search and read the user's personal knowledge base from the command line with
  the local `miyo` CLI — their own notes and documents, plus their saved ChatGPT /
  Claude conversations. Reach for this whenever a request could be answered from
  something the user wrote, saved, decided, or discussed before, even when they
  don't mention "Miyo," "notes," or a filename: "what did I decide about X", "find
  my doc on Y", "what did I ask ChatGPT about Z", "summarize what I have on …",
  "did I already write something about …". Also for listing/inspecting their
  indexed files and folders, or converting a PDF to text. Commands: `miyo search`,
  `miyo files`, `miyo folders`, `miyo parse`.
---

# Miyo CLI

Miyo is a local-first knowledge tool. It indexes the user's notes, documents, and
saved AI chats into a local vector database and exposes **hybrid semantic search**
(dense + sparse, fused with RRF) over them. The `miyo` CLI is a thin client over a
local HTTP service — everything stays on the user's machine.

**Reach for it whenever the answer likely lives in the user's *own* material**
rather than your training data or the open web. That includes questions that never
say "Miyo" or "notes" but clearly point at something the user wrote, saved, decided,
or discussed before — "what did we land on for the pricing model?", "pull up my
onboarding doc", "have I written about this already?". When in doubt, search: a
quick `miyo search` is cheap, and answering from your own guess when the user has a
real note on it is the failure mode to avoid.

## Prerequisites (check once)

The CLI talks to a local service that the **Miyo desktop app** runs. Confirm both
the binary and the service before relying on results:

```bash
command -v miyo                                        # binary on PATH?
curl -s --max-time 2 http://127.0.0.1:8742/v0/health   # service up? expect {"status":"ok",...}
```

- The app installs `miyo` to `~/.miyo/bin/miyo` (macOS/Linux) or
  `%LOCALAPPDATA%\Miyo\bin\miyo.exe` (Windows) on first launch and adds it to PATH;
  a brand-new install needs one terminal restart.
- If `curl` fails or `miyo` prints **"Cannot connect to Miyo service / Is the Miyo
  app running?"**, the desktop app isn't running. Ask the user to open it — don't
  treat an empty result as "the user has no notes about this." See
  [references/troubleshooting.md](references/troubleshooting.md).

(`miyo parse` is the exception — it needs no service. See below.)

## Commands at a glance

| Command | Purpose |
|---|---|
| `miyo search <query>` | Semantic search over documents or saved chats |
| `miyo files` | List indexed files, with filters |
| `miyo folders` | List indexed folders + indexing status |
| `miyo parse <file>` | Convert a document (PDF) to Markdown/text — no service needed |

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

## Converting documents: parse

`miyo parse <file>` turns a document (currently PDF) into Markdown/text. It's the
**exception** to the prerequisites above — it runs in-process, so the Miyo app does
**not** need to be running, and the file need not be in an indexed folder.

```bash
miyo parse report.pdf                 # Markdown to stdout
miyo parse report.pdf -o report.md    # write to a file
miyo parse report.pdf --json          # structured: text, title, page_count, …
```

Use it to read or quote a PDF the user points at. It returns a **distinct exit code
per failure kind** (unsupported type, not found, parse failed, …) so you can branch
without scraping stderr. Full flags, JSON shape, and exit-code table:
[references/parse.md](references/parse.md).

## Guidance for agents

- **Search before you answer.** For anything that could live in the user's own
  material, run `miyo search` first. The expensive mistake is answering from your
  own knowledge when the user has a real note that says otherwise.
- **Don't fabricate.** Treat results as the user's ground truth and cite the file
  path a fact came from. If search returns nothing, say so plainly rather than
  filling the gap from general knowledge — and consider whether the other `--source`
  or looser filters would find it.
- **Pick the right corpus.** "What I discussed/asked" (an AI chat) → `--source
  chats`. "My notes/docs" → `documents` (the default).
- **Use `--json` when you parse.** Human output is for display; `--json` is stable
  for scripting (`results[]`, each `{path, content}`).
- **Keep queries conceptual.** This is semantic search — natural-language intent
  beats exact keywords. Narrow with `--path` / `--mtime-*` instead of stuffing the
  query string.
