# `miyo files` and `miyo folders` — browse the index

Use these to see *what* is indexed (and how complete the index is) without running a
semantic query. Handy for scoping a search, resolving a result to a real file on
disk, or answering "do I have anything recent about …".

## `miyo files` — list indexed files

```
miyo files [options]
```

| Flag | Default | Meaning |
|---|---|---|
| `--title <text>` | — | Filter by file title (partial, case-insensitive). |
| `--path <text>` | — | Filter by file path (partial, case-insensitive). |
| `--mtime-after <date>` | — | Only files modified on/after the date. |
| `--mtime-before <date>` | — | Only files modified on/before the date. |
| `-n, --limit <n>` | `50` | Max results. Clamped to `1`–`1000`. |
| `--order-by <field>` | `updated_at` | Sort by `mtime` (file's own modified time) or `updated_at` (when Miyo last re-indexed it). |
| `--json` | off | Emit JSON. |
| `--url <url>` | service discovery | Override service URL. |
| `-h, --help` | — | Print usage. |

This is a **metadata** listing — it does not do semantic matching. `--title` and
`--path` are plain substring filters. For "find files about a topic", use
`miyo search`.

**Human-readable output:**

```
Showing 2 of 2 file(s):

1. notes/infra/kubernetes.md — Kubernetes [infra]
   Modified: 2026-06-18 14:30  Chunks: 42

2. archive/2025/ops-runbook.md [archive/2025]
   Modified: 2025-11-02 09:12  Chunks: 17
```

**JSON output:**

```json
{
  "files": [
    {
      "path": "notes/infra/kubernetes.md",
      "title": "Kubernetes",
      "mtime": 1718721000000,
      "updated_at": 1718721100000,
      "folder_path": "infra",
      "total_chunks": 42
    }
  ],
  "total": 2
}
```

`mtime` / `updated_at` are epoch milliseconds. `title` and `folder_path` may be
`null`. `total` is the full match count (may exceed the returned `files.length` when
capped by `--limit`).

## `miyo folders` — list indexed folders

```
miyo folders [options]
```

Only `--json`, `--url`, and `-h/--help`. No filters.

Shows every folder Miyo watches and how far indexing has progressed — useful to
sanity-check that the user's material is actually indexed before concluding a search
"found nothing."

**Human-readable output:**

```
Showing 1 folder(s):

1. Notes [writable]
   /Users/alex/Documents/Notes
   158/160 indexed, 2 errors  Status: indexing  Last scan: 2026-06-21 14:30
```

**JSON output:**

```json
{
  "folders": [
    {
      "path": "Notes",
      "absolute_path": "/Users/alex/Documents/Notes",
      "status": "indexing",
      "total_files": 160,
      "indexed_files": 158,
      "error_files": 2,
      "allow_writes": true,
      "last_scan_at": 1718980200000
    }
  ]
}
```

Field notes:

- `absolute_path` — the folder's real location. **Join it with a search result's
  `path` to read the actual file** off disk.
- `status` — e.g. `indexing` vs settled; `indexed_files` < `total_files` means a
  scan is still in flight, so a search may be incomplete.
- `error_files` — files that failed to index (unsupported/corrupt); they won't
  appear in search.
- `allow_writes` — whether tools are permitted to create/edit files in this folder.
- No folders prints: `No folders registered. Add a folder in the Miyo app to get
  started.`
