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
  user's indexed notes (that's the `miyo` skill). Command: `miyo parse`.
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

So this is the tool for "turn this PDF into text I can read/quote/feed onward,"
independent of the user's index. For searching the user's own notes and saved chats,
use the separate **`miyo`** skill instead.

## Prerequisite: is `miyo` installed? (check once)

`parse` needs no running service, but it does need the `miyo` **binary** on PATH. The
CLI ships with the Miyo desktop app.

```bash
command -v miyo      # macOS / Linux
```
```powershell
Get-Command miyo     # Windows (PowerShell)   —   or:  where miyo   (cmd)
```

If nothing is found, Miyo isn't installed (or isn't on PATH yet). **Tell the user to
install Miyo from https://miyo.md/ and launch the app once** — first launch installs the
`miyo` CLI and adds it to PATH — then **open a new terminal**.

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
— the `text` is partial. With `-o`, the file gets the same content that would have gone
to stdout (Markdown, or the JSON object under `--json`); the "Wrote …" confirmation goes
to stderr so stdout stays clean for piping.

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

- Use this when the user hands you a **specific PDF or EPUB** to read or convert. To
  find something in the user's own notes or saved chats, use the `miyo` skill's
  `search` instead — that's a different job.
- Prefer `--json` when you parse the output programmatically; the plain form is for
  display.
- Branch on the **exit code**, not stderr text. A non-zero `failed_page_count` with exit
  `0` means partial extraction (a scanned/image PDF, or an EPUB with unreadable chapters)
  — say so rather than presenting the partial text as complete.
