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
rather than your training data or the open web. That includes questions that never
say "Miyo" or "notes" but clearly point at something the user wrote, saved, decided,
or discussed before — "what did we land on for the pricing model?", "pull up my
onboarding doc", "have I written about this already?". When in doubt, search: a
quick `miyo search` is cheap, and answering from your own guess when the user has a
real note on it is the failure mode to avoid.

## Prerequisites (check once)

The CLI ships *with* the **Miyo desktop app**, which also runs the local service the
CLI queries. Confirm the binary is installed and the service is up before relying on
results. The commands differ slightly by OS; the `miyo` subcommands below are
identical everywhere.

**1. Is `miyo` installed?**

```bash
command -v miyo      # macOS / Linux
```
```powershell
Get-Command miyo     # Windows (PowerShell)   —   or:  where miyo   (cmd)
```

If nothing is found, Miyo isn't installed (or isn't on PATH yet). **Tell the user to
install Miyo from https://miyo.md/ and launch the app once** — first launch installs
the `miyo` CLI and adds it to PATH — then **open a new terminal**. If the app is
already installed, [references/troubleshooting.md](references/troubleshooting.md) has
the per-OS binary path and PATH fixes.

**2. Is the service up?**

Probe whatever URL the CLI will actually use — `MIYO_URL` overrides the localhost
default (see the cross-device note below), so honor it rather than hardcoding
`127.0.0.1`:

```bash
curl -s --max-time 2 "${MIYO_URL:-http://127.0.0.1:8742}/v0/health"   # macOS / Linux — expect {"status":"ok",...}
```
```powershell
curl.exe -s "$($env:MIYO_URL ?? 'http://127.0.0.1:8742')/v0/health"   # Windows: curl.exe (bare `curl` is an alias)
# or:  Invoke-RestMethod "$($env:MIYO_URL ?? 'http://127.0.0.1:8742')/v0/health"
```

If this fails or `miyo` prints **"Cannot connect to Miyo service / Is the Miyo app
running?"**, the desktop app isn't running — **ask the user to open the Miyo app (or
download it from https://miyo.md/ if it isn't installed)**. Don't treat that as "the
user has no notes about this."

**Miyo on another device (e.g. Tailscale):** if the user's index lives on a
*different* machine — a desktop they reach over Tailscale/LAN — point the CLI at it
with `MIYO_URL` / `--url http://<host>:8742` (a Tailscale MagicDNS name or `100.x`
address). This works only if that Miyo was bound to a reachable interface; details
and the security caveat are in
[references/troubleshooting.md](references/troubleshooting.md).

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
