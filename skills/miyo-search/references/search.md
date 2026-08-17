# `miyo search` — semantic search

Hybrid semantic + keyword search over the user's indexed material, fused with
Reciprocal Rank Fusion. Returns the passages most relevant to a natural-language
query, grouped by source file.

```
miyo search [options] <query>
```

`<query>` is everything not consumed by a flag, joined with spaces — quoting is
optional but recommended. A query is required.

## Options

| Flag | Default | Meaning |
|---|---|---|
| `-n, --limit <n>` | `20` | Max file results. Clamped to `1`–`1000`. |
| `--source <documents\|chats>` | `documents` | Which corpus to search (see below). |
| `--path <text>` | — | Keep only results whose path contains `<text>` (partial, case-insensitive). **Repeatable** — multiple `--path` flags OR together. |
| `--variant <query>` | — | Another phrasing of the same question, searched alongside `<query>` and fused into one ranking. **Repeatable**; the service uses the first 2 and ignores the rest. A value cannot start with `-`. |
| `--mtime-after <date>` | — | Only files modified on/after the date. |
| `--mtime-before <date>` | — | Only files modified on/before the date. |
| `--json` | off | Emit JSON instead of formatted text. |
| `--url <url>` | service discovery | Override the service URL (else `MIYO_URL`, else the running app, else `http://127.0.0.1:8742`). |
| `-h, --help` | — | Print usage. |

Dates accept `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS` (a `T` separator also works).
Invalid dates error out with exit code `1`.

## Sources: documents vs chats

The two corpora live in separate collections and are **never** searched together.

- `documents` — the user's own notes and files (the default, the primary corpus).
- `chats` — conversations the user saved from ChatGPT (`chatgpt.com`) and Claude
  (`claude.ai`).

Choose `chats` whenever the user points at a past AI conversation ("what did I ask
ChatGPT about…", "find the Claude chat where we…"). When unsure, run both.

## Output

**Human-readable (default):** results grouped by file.

```
Found 2 file result(s) from 5 chunk hit(s) (142ms):

1. notes/infra/kubernetes.md
   ...ingress controllers terminate TLS at the edge; we standardized on...

2. archive/2025/ops-runbook.md
   ...the ingress class must be set explicitly or the controller ignores...
```

No matches prints `No results found.` (exit code still `0` — an empty result is a
valid answer, not an error).

**JSON (`--json`):**

```json
{
  "results": [
    { "path": "notes/infra/kubernetes.md", "content": "...excerpt..." },
    { "path": "archive/2025/ops-runbook.md", "content": "...excerpt..." }
  ],
  "count": 2,
  "chunk_count": 5,
  "execution_time_ms": 142
}
```

Parse `results[]`; each entry is `{ path, content }`. `count` is files returned,
`chunk_count` is the number of underlying chunk hits before grouping.

## The `content` field is a snippet, not the file

Each result's `content` is the matching excerpt(s), not the whole document. The CLI
has no read command — to get full text, **read the file off disk**: results are the
user's real files, so resolve the folder's `absolute_path` from `miyo folders`, join
it with the result `path`, and open the file directly.

## Query expansion: search more than one phrasing

A phrasing is embedded as a single vector and gets one keyword pass over the same
string, so it only reaches notes written in that vocabulary. Two things follow:

- **Don't concatenate synonyms into one query.** The extra terms drag the vector
  toward an average of several meanings, and a padded string no longer matches any
  title literally, so a file named after exactly what was asked loses the ranking
  edge it would otherwise get.
- **Do pass the alternatives as `--variant`.** Each becomes its own pair of
  retrieval arms, landing in a different part of the index and getting its own
  clean keyword pass. The service fuses every arm into one ranking with the same
  Reciprocal Rank Fusion it already uses, in the same request, so a file that
  several phrasings agree on rises without you doing anything.

### Writing the variants

Start from the user's question and produce two or three *complete* phrasings.
Taking *"what did we decide about rate limiting the ingest API?"*:

| Goes in | What changes | Text |
|---|---|---|
| the query | Verbatim. The user's own words, minus the filler. | `rate limiting the ingest API decision` |
| `--variant` | Domain synonyms: what their notes probably say instead. | `ingest API throttling policy` |
| `--variant` | The mechanism an answer would have to name. | `token bucket quota per API key` |

What matters for recall:

- **The query itself stays in the user's own terms.** Their nouns, proper nouns,
  project names, and jargon are what their notes actually contain. Invention
  belongs in the variants, never in the query.
- **Stay in the language the user asked in.** Translating their terms searches a
  vocabulary their notes may not use. If you know they keep notes in another
  language, spend one variant there rather than translating the whole set.
- **Resolve time expressions to dates.** "last month", "yesterday" and the like
  compete for semantic weight in a query and are rejected as flag values: the CLI
  accepts only `YYYY-MM-DD` (or with a time). Work out the absolute date yourself,
  then pass `--mtime-after` / `--mtime-before`.
- **Two variants is the budget, and it is a hard one.** The service uses the
  first two it is given and ignores the rest. The reason is not cost: the fusion
  weights every arm equally, so each phrasing dilutes the share the user's own
  wording holds. Since rewrites of one question tend to resemble each other,
  piling them on lets broad agreement among your inventions outrank the best
  match for what was actually asked.
- **Raise `-n` when you expand.** Variants widen what is *searched*, not how much
  comes back: the fused ranking still returns the number you asked for, drawn from
  a wider pool. At `-n 5` a file only one variant found has to beat four others to
  appear at all.

Which makes the whole thing one command. Keep it on one line: a trailing `\`
continues a command in bash and zsh only, and this skill supports PowerShell and
cmd as well.

```bash
miyo search --json -n 30 "rate limiting the ingest API decision" --variant "ingest API throttling policy" --variant "token bucket quota per API key"
```

The user's own wording belongs in the query, not in a `--variant`, because the
ranking still keys off it: a file whose title literally matches those words is
floated to the top, and the excerpt is centred on that phrasing. A `--variant`
that merely repeats the query is dropped rather than counted twice.

### When to expand

- **Up front**, when the ask is broad or recall-shaped: "everything I have on X",
  "did I ever write about Y", "summarize what I know about Z".
- **As a second pass**, whenever the first search returns few results or hits that
  miss the point. Retry with different words before telling the user they have
  nothing. If every variant comes back empty, stop assuming it is the wording: a
  stopped Qdrant or a folder still indexing also returns `No results found.` with
  exit `0`. Work through
  [troubleshooting.md](troubleshooting.md#empty-results) before answering.
- **Skip it** when the user named a file or an exact title. That's a `miyo files`
  lookup, not a semantic sweep.

## Recipes

```bash
# Top 5, scoped to a subtree, recent only
miyo search -n 5 --path "work/" --mtime-after 2026-01-01 "migration plan"

# OR across two subtrees
miyo search --path "notes/" --path "archive/" "postmortem"

# A past ChatGPT conversation, parsed
miyo search --source chats --json "the prompt we wrote for the classifier"

# Against a non-default service (e.g. a dev instance)
miyo search --url http://127.0.0.1:9999 "test query"
```

## Tips

- Phrase queries by **intent**, not keywords — semantic search rewards
  natural-language descriptions of what you're looking for.
- Narrow with `--path` / `--mtime-*` rather than overloading the query string.
- Widen with `--variant` rather than a longer query; see
  [Query expansion](#query-expansion-search-more-than-one-phrasing).
- Raise `-n` when you need recall (feeding many candidates to a summarizer); keep
  it low when you want the single best hit.
