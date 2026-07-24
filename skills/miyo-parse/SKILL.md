---
name: miyo-parse
description: >-
  Convert a document (PDF or EPUB) into Markdown/plain text with the local `miyo
  parse` CLI, so you can read, quote, or feed its contents onward. Reach for this
  whenever the user points at a PDF or EPUB and wants its text — "read this PDF",
  "what does this contract say", "pull the text out of report.pdf", "convert this
  PDF to Markdown", "summarize this PDF", "read this ebook/epub", "what's in
  book.epub". Works on any file path and needs **no** running Miyo app or service —
  it parses in-process. This is document *conversion*, distinct from searching the
  user's indexed notes (that's the `miyo-search` skill). Command: `miyo parse`.
---

# `miyo parse` — document → Markdown/text

`miyo parse <file>` turns a document into Markdown/plain text and prints it. Supports
**PDF** and **EPUB**. Use it to read or quote a book or PDF the user points you at, or
to convert one to a Markdown file on disk. For an EPUB, chapters come out in reading
(spine) order.

Two properties make this different from the rest of the Miyo CLI (`miyo search`, `miyo
files`, `miyo folders`, which query the running app):

- **No service required.** Parsing runs in-process — the Miyo desktop app does **not**
  need to be running, and there's no HTTP call (so there's no `--url` flag).
- **Any path.** `<file>` is any filesystem path; it does **not** need to live in an
  indexed Miyo folder.

## Prerequisite: invoke `miyo` by its full path

`parse` needs no running service, but it does need the `miyo` **binary**.

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

## Usage

```
miyo parse [options] <file>
```

Exactly one file path is required; passing zero or more than one is an error.

## Options

| Flag | Meaning |
|---|---|
| `--json` | Emit the structured result as JSON instead of plain Markdown. |
| `-o, --output <path>` | Write the result to `<path>` instead of stdout (Markdown by default, or the JSON object with `--json`). |
| `-h, --help` | Print usage. |

## Output

**Default:** the parsed Markdown/text on stdout.

```bash
miyo parse report.pdf
miyo parse report.pdf -o report.md     # writes report.md; prints "Wrote Markdown to report.md" to stderr
```

**`--json`:** a structured object —

```json
{
  "text": "# Title\n\nBody…",
  "format": "pdf",
  "source_path": "/abs/path/report.pdf",
  "title": "Report",
  "page_count": 12,
  "failed_page_count": 0
}
```

`text` is the extracted Markdown/text; `format` is the **source** format (`"pdf"` or
`"epub"`); `title` may be `null`. For an EPUB, `page_count` is the number of chapter
(spine) documents rather than pages.

`failed_page_count` > 0 means some pages (PDF) or chapters (EPUB) couldn't be extracted
— the `text` is partial. The `-o` confirmation goes to **stderr**, so stdout stays clean
for piping.

## Exit codes

Unlike the other `miyo` commands (which only use `0`/`1`), `parse` returns a **distinct
code per failure kind** so you can branch without scraping stderr:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Usage error (bad/missing/extra args) or failed to write `--output` |
| `2` | Invalid input |
| `3` | Unsupported media type (not a PDF or EPUB) |
| `4` | File not found |
| `5` | File not readable |
| `6` | Parse failed |
| `7` | Internal error |
| `8` | Encrypted / password-protected |
| `9` | No extractable text (scanned/image-only PDF, or an empty/image-only EPUB) |

## Recipes

```bash
# Read a PDF's text
miyo parse ~/Downloads/contract.pdf

# Read an EPUB (chapters come out in reading order)
miyo parse ~/Downloads/book.epub

# Capture structured metadata (page/chapter counts, title) for a pipeline
miyo parse ~/Downloads/contract.pdf --json > contract.json

# Convert to a Markdown file on disk
miyo parse ~/Downloads/book.epub -o ~/notes/book.md
```

## Guidance for agents

- Prefer `--json` when you parse the output programmatically; the plain form is for
  display.
- Branch on the **exit code**, not stderr text. A non-zero `failed_page_count` with exit
  `0` means partial extraction (a scanned/image PDF, or an EPUB with unreadable chapters)
  — say so rather than presenting the partial text as complete.
