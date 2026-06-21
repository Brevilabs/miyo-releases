# Troubleshooting the `miyo` CLI

## "Cannot connect to Miyo service / Is the Miyo app running?"

The CLI is a client of a local HTTP service that the **Miyo desktop app** owns. This
error means the service isn't reachable.

1. Confirm the service:
   ```bash
   curl -s --max-time 2 http://127.0.0.1:8742/v0/health
   ```
   Expect `{"status":"ok",...}`. No response ⇒ the app isn't running.
2. Ask the user to open the Miyo desktop app, then retry. The service starts with
   the app and stops when it quits.

Do **not** interpret a connection error as "the user has nothing on this topic."
It's an availability problem, not an empty result.

## `miyo: command not found`

The binary isn't on `PATH`.

- The desktop app installs it on first launch to `~/.miyo/bin/miyo` (macOS/Linux,
  a symlink) or `%LOCALAPPDATA%\Miyo\bin\miyo.exe` (Windows), and appends the
  directory to PATH via shell rc files (`.zshenv`, or `.bashrc` + `.bash_profile`)
  / the Windows user PATH.
- A fresh install needs **one terminal restart** to pick up the new PATH.
- Workaround without a restart: call the binary by full path, e.g.
  `~/.miyo/bin/miyo search "…"`.
- If it's still missing, the app may never have launched. Have the user open Miyo
  once.

## Empty results

A `0`-exit `No results found.` is a legitimate answer. Before concluding the user
has nothing relevant:

- Check the corpus — was the question about a past AI chat? Retry with
  `--source chats`.
- Check coverage — `miyo folders`. If `indexed_files` < `total_files` or
  `status` is still `indexing`, the index is incomplete; wait and retry.
- Loosen the query — semantic search rewards conceptual phrasing; drop
  over-specific `--path` / `--mtime-*` filters.

## Pointing at a non-default service

URL resolution order (first wins):

1. `--url <url>` flag
2. `MIYO_URL` environment variable
3. Service discovery — `service.json` written by the running app
   (`~/Library/Application Support/Miyo/service.json` on macOS)
4. Default `http://127.0.0.1:8742`

So to target a dev instance on another port:

```bash
miyo search --url http://127.0.0.1:9999 "test"
# or
export MIYO_URL=http://127.0.0.1:9999
```

## Exit codes

- `0` — success (including a valid empty result).
- `1` — error: missing query, unknown flag, invalid date/`--limit`/`--source`,
  service unreachable, or a server-side failure.
