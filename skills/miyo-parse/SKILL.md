---
name: miyo-parse
description: >-
  Convert a document (PDF, EPUB, or Word .docx) or the text in an image (PNG, JPEG, WebP,
  AVIF, JPEG XL) into Markdown/plain text with the local `miyo parse` CLI, so you can read, quote, or
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

`miyo parse <file>` turns a PDF, EPUB, Word `.docx`, or a PNG, JPEG, WebP, AVIF, or JPEG XL
(`.jxl`) image into Markdown/plain text and prints it. The file can be anywhere on disk, and the Miyo app doesn't need to
be running. Scanned PDF pages and images are read with OCR on the user's machine;
nothing is uploaded. EPUB chapters come out in reading order. A `.docx` keeps its
headings, lists, and tables, and reads with tracked changes accepted. Legacy `.doc`,
HEIC, GIF, TIFF, and animated WebP are **not** supported.

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

```bash
miyo parse ~/Downloads/contract.pdf                 # Markdown on stdout
miyo parse ~/Downloads/contract.pdf --json          # text plus page counts and OCR details
miyo parse ~/Downloads/book.epub -o ~/notes/book.md # write a Markdown file
```

`miyo parse --help` lists the flags, the `--json` fields, and the exit codes. Unlike
the other `miyo` commands, `parse` returns a distinct exit code per failure kind, so
branch on the code rather than on stderr. Exit `10` means the OCR runtime didn't load;
reinstalling Miyo restores it.

## Reading the `--json` result

- `page_count` counts pages for a PDF, chapters for an EPUB, and blocks (paragraphs,
  headings, list items, tables) for a `.docx`, which has no fixed pagination. An image
  is one page.
- `failed_page_count` above 0, or a non-empty `unreadable_pages`, means the `text` is
  partial. `ocr_pages` lists the pages whose text came from OCR.
- `ocr_error` is set when OCR failed on a PDF that also has typed text. Miyo keeps the
  typed text and still exits `0`; the plain form prints a `Warning:` line on stderr.

## Reading a long PDF in pages

A long PDF can be more text than you can hold at once. Read it in ranges with
`--pages` instead:

```bash
miyo parse book.pdf --pages 1-20 --json   # page_count says how many pages there are
miyo parse book.pdf --pages 21-40
```

Only `text` changes; every other `--json` field still describes the whole PDF, so
`unreadable_pages` or `ocr_pages` may name pages outside your range. The
first read parses the whole PDF, OCR included, so it takes as long as a plain
`miyo parse`, and later ranges come back right away. If OCR failed, nothing is saved
and each range reads the whole PDF again. Where a paragraph or table runs across a
page break, a range's text can differ slightly from the same pages in a full parse.

## Guidance for agents

- When the text is partial (a failed or unreadable page in the range you read, or
  `ocr_error` set), say so rather than presenting it as complete.
- OCR is slower than reading a typed PDF. Allow a few seconds per scanned page or image
  before treating `miyo parse` as stuck.
