# Query expansion: search more than one phrasing

A phrasing is embedded as a single vector and gets one keyword pass over the same
string, so it only reaches notes written in that vocabulary. Two things follow:

- **Don't concatenate synonyms into one query.** The extra terms drag the vector
  toward an average of several meanings, and a padded string no longer matches any
  title literally, so a file named after exactly what was asked loses the ranking
  edge it would otherwise get.
- **Do pass the alternatives as `--variant`.** Each becomes its own pair of
  retrieval arms, landing in a different part of the index and getting its own
  clean keyword pass. The service fuses the variant arms among themselves first,
  then with the query's own two, all in one request: a file several phrasings
  agree on rises, but never above what the user's own words matched best.

## Writing the variants

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
- **Two variants is the budget.** The service searches at most two and drops
  the rest. The fusion keeps your rewrites from outvoting the user's own wording,
  so the budget is about cost: each variant is another embedding and two more
  retrieval arms, and rewrites of one question resemble each other enough that a
  third rarely finds what the first two missed.
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

## When to expand

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
