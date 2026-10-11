---
name: miyo-parse
description: >-
  Convert a document (PDF, EPUB, or Word .docx) or the text in an image (PNG, JPEG)
  into Markdown/plain text with the local `miyo parse` CLI, so you can read, quote, or
  feed its contents onward. Reach for this whenever the user points at one of those
  and wants its text — "read this PDF", "what does this contract say", "pull the text
  out of report.pdf", "convert this PDF to Markdown", "summarize this PDF", "read this
  ebook/epub", "what's in book.epub", "read this Word doc", "what's in proposal.docx",
  "what does this screenshot say", "copy the text out of receipt.jpg". Works on any file path
  and needs **no** running Miyo app or service —
  it parses in-process. This is document *conversion*, distinct from searching the
  user's indexed notes (that's the `miyo-search` skill). Command: `miyo parse`.
---

# `miyo parse` — document → Markdown/text

`miyo parse <file>` turns a document into Markdown/plain text and prints it. Supports
**PDF**, **EPUB**, **Word `.docx`**, and **PNG** and **JPEG** images. Use it to read or
quote a document the user points you at, or to convert one to a Markdown file on disk.
Scanned PDF pages and images are read with OCR on the user's machine; nothing is
uploaded. For an EPUB, chapters come
out in reading (spine) order. For a `.docx`, headings, lists, and tables survive as
Markdown, and a document with tracked changes reads as it would with changes accepted.
Legacy `.doc` (Word 97-2003) is **not** supported, and neither are HEIC, GIF, TIFF, or
WebP images.

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
  "failed_page_count": 0,
  "pdf_type": "mixed",
  "pages_needing_ocr": [3, 4],
  "ocr_pages": [3, 4],
  "unreadable_pages": [],
  "ocr_error": null
}
```

`text` is the extracted Markdown/text; `format` is the **source** format (`"pdf"`,
`"epub"`, `"docx"`, or `"image"`); `title` may be `null`. `page_count` counts pages
for a PDF, chapter (spine) documents for an EPUB, and blocks (paragraphs, headings,
list items, tables) for a `.docx`, which has no fixed pagination. An image is one
page.

`failed_page_count` > 0 means some pages (PDF) or chapters (EPUB) couldn't be extracted
— the `text` is partial. The `-o` confirmation goes to **stderr**, so stdout stays clean
for piping.

For PDFs, `pdf_type` is `"text_based"`, `"scanned"`, `"image_based"`, or `"mixed"`,
and `pages_needing_ocr` contains 1-indexed pages whose text layer is absent, sparse, or
otherwise unreliable. Miyo reads the ones with no usable text layer with OCR.
`ocr_pages` lists the pages whose text came from OCR, and `unreadable_pages` the pages
that still have no credible text (blank, handwritten, or too blurred to read). An image
reports `pdf_type: null` and its one page in `pages_needing_ocr` and `ocr_pages`, and in
`unreadable_pages` when OCR found no credible text in it. For EPUBs and `.docx` files
`pdf_type` is `null` and the page lists are `[]`, and a `.docx` always reports
`failed_page_count: 0`, since its text either parses whole or the command fails.

`ocr_error` is `null` unless OCR failed on a PDF that has typed text. Miyo then keeps
the typed text, still exits `0`, lists the pages it couldn't read in
`unreadable_pages`, and sets `ocr_error` to `{ "code", "message" }`. The code is
`ocr_unavailable` (the OCR runtime didn't load), `parse_failed` (OCR failed or timed
out on this file), or `internal_error`. The plain form prints the message as a
`Warning:` line on stderr. A scan or image with no typed text still fails with its
exit code.

## Exit codes

Unlike the other `miyo` commands (which only use `0`/`1`), `parse` returns a **distinct
code per failure kind** so you can branch without scraping stderr:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Usage error (bad/missing/extra args) or failed to write `--output` |
| `2` | Invalid input |
| `3` | Unsupported media type (not a PDF, EPUB, `.docx`, PNG, or JPEG) |
| `4` | File not found |
| `5` | File not readable |
| `6` | Parse failed |
| `7` | Internal error |
| `8` | Encrypted / password-protected |
| `9` | No readable text (a PDF whose pages are blank or illegible even with OCR, an image with no legible text, or an empty EPUB or `.docx`) |
| `10` | The OCR runtime did not load, so a scan or image with no typed text can't be read. Typed PDFs still parse, and a PDF with some typed text exits `0` with `ocr_error` set. Reinstalling Miyo restores the runtime |

## Recipes

```bash
# Read a PDF's text
miyo parse ~/Downloads/contract.pdf

# Read an EPUB (chapters come out in reading order)
miyo parse ~/Downloads/book.epub

# Read a Word document (headings, lists, and tables become Markdown)
miyo parse ~/Downloads/proposal.docx

# Read the text in a screenshot or a photo of a receipt
miyo parse ~/Desktop/screenshot.png

# Capture structured metadata (page/chapter counts, title) for a pipeline
miyo parse ~/Downloads/contract.pdf --json > contract.json

# Convert to a Markdown file on disk
miyo parse ~/Downloads/book.epub -o ~/notes/book.md
```

## Guidance for agents

- Prefer `--json` when you parse the output programmatically; the plain form is for
  display.
- Branch on the **exit code**, not stderr text. A non-zero `failed_page_count`, a
  non-empty `unreadable_pages`, or a non-null `ocr_error` with exit `0` means partial
  extraction (damaged PDF pages, pages OCR couldn't read or never reached, or an EPUB
  with unreadable chapters). Say so rather
  than presenting the partial text as complete.
- OCR is slower than reading a typed PDF. Allow a few seconds per scanned page or image
  before treating `miyo parse` as stuck.
