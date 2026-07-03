# Troubleshooting the `miyo` CLI

## "Cannot connect to Miyo service / Is the Miyo app running?"

The CLI is a client of a local HTTP service that the **Miyo desktop app** owns. This
error means the service isn't reachable.

1. Confirm the service:
   ```bash
   curl -s --max-time 2 http://127.0.0.1:8742/v0/health          # macOS / Linux
   ```
   ```powershell
   curl.exe -s http://127.0.0.1:8742/v0/health                   # Windows (see note below)
   ```
   Expect `{"status":"ok",...}`. No response ⇒ the app isn't running.
2. Ask the user to open the Miyo desktop app — **or, if Miyo isn't installed at all,
   to download it from https://miyo.md/**. The service starts with the app and stops
   when it quits.

Do **not** interpret a connection error as "the user has nothing on this topic."
It's an availability problem, not an empty result.

> **Windows `curl` gotcha:** in PowerShell, `curl` is an alias for
> `Invoke-WebRequest`, which doesn't accept `-s` and prints differently. Use
> `curl.exe` (real curl ships with Windows 10+), or `Invoke-RestMethod <url>`. In
> `cmd.exe`, plain `curl` is the real one.

## `miyo: command not found` (or `miyo` not recognized)

The binary isn't installed, or isn't on `PATH` yet.

- **First, is Miyo installed?** The CLI ships with the desktop app. If the user has
  never installed Miyo, point them to **https://miyo.md/**; installing and launching
  the app once puts the CLI in place.
- **Where the app installs it** (on first launch, and adds the dir to PATH):

  | OS | Binary path | PATH mechanism |
  |---|---|---|
  | macOS / Linux | `~/.miyo/bin/miyo` (symlink) | shell rc — `.zshenv`, or `.bashrc` + `.bash_profile` |
  | Windows | `%LOCALAPPDATA%\Miyo\bin\miyo\miyo.exe` (full copy) | User `Path` env var |

- A fresh install needs **one new terminal** to pick up the updated PATH (Windows:
  a newly opened terminal inherits the new User `Path`).
- Workaround without waiting: call the binary by full path — e.g.
  `~/.miyo/bin/miyo search "…"` (macOS/Linux) or
  `& "$env:LOCALAPPDATA\Miyo\bin\miyo\miyo.exe" search "…"` (PowerShell).
- If it's still missing after a relaunch, the app may never have finished first-run
  setup. Have the user open Miyo once more.

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
3. Service discovery — `service.json` written by the running app under its app-data
   dir: `~/Library/Application Support/Miyo/` (macOS), `%APPDATA%\Miyo\` (Windows),
   `~/.config/Miyo/` (Linux)
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
