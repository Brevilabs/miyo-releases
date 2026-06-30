# `miyo parse` — document → Markdown/text

Parse a document into Markdown/plain text and print it. Currently supports **PDF**.

```
miyo parse [options] <file>
```

Two properties make this different from the other commands:

- **No service required.** Parsing runs in-process — the Miyo desktop app does
  **not** need to be running, and there's no HTTP call. (No `--url` flag.)
- **Any path.** `<file>` is any filesystem path; it does **not** need to live in an
  indexed Miyo folder.

So this is the tool for "turn this PDF into text I can read/quote/feed onward,"
independent of the user's index.

## Options

| Flag | Meaning |
|---|---|
| `--json` | Emit the structured result as JSON instead of plain Markdown. |
| `-o, --output <path>` | Write the result to `<path>` instead of stdout (Markdown by default, or the JSON object with `--json`). |
| `-h, --help` | Print usage. |

Exactly one file path is required; passing zero or more than one is an error.

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

`text` is the extracted Markdown/text; `format` is the **source** format (`"pdf"`);
`title` may be `null`.

`failed_page_count` > 0 means some pages couldn't be extracted (e.g. scanned/image
pages) — the `text` is partial. With `-o`, the file gets the same content that would
have gone to stdout (Markdown, or the JSON object under `--json`); the "Wrote …"
confirmation goes to stderr so stdout stays clean for piping.

## Exit codes

Unlike the other commands (which only use `0`/`1`), `parse` returns a **distinct code
per failure kind** so you can branch without scraping stderr:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Usage error (bad/missing/extra args) or failed to write `--output` |
| `2` | Invalid input |
| `3` | Unsupported media type (e.g. not a PDF) |
| `4` | File not found |
| `5` | File not readable |
| `6` | Parse failed |
| `7` | Internal error |

## Recipes

```bash
# Read a PDF's text
miyo parse ~/Downloads/contract.pdf

# Capture structured metadata (page counts, title) for a pipeline
miyo parse ~/Downloads/contract.pdf --json > contract.json

# Convert to a Markdown file on disk
miyo parse ~/Downloads/contract.pdf -o ~/notes/contract.md
```
