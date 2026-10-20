# Troubleshooting the `miyo` CLI

## "Cannot connect to Miyo service / Is the Miyo app running?"

The CLI is a client of a local HTTP service that the **Miyo desktop app** owns, and
this error means the service isn't reachable. Ask the user to open the Miyo desktop
app, **or, if Miyo isn't installed at all, to download it from https://miyo.md/**.
The service starts with the app and stops when it quits.

Do **not** interpret a connection error as "the user has nothing on this topic."
It's an availability problem, not an empty result.

## Running Miyo inside a sandboxed agent (e.g. Codex)

Some coding agents run commands in a sandbox that blocks network access by
default, and a connection to `127.0.0.1:8742` counts as network. So the *first*
`miyo` command that talks to the service may pause for an approval prompt — this is
the sandbox, not a Miyo error. Once approved, the local service works normally;
everything still stays on the user's machine.

To avoid the prompt entirely, let the sandbox reach loopback. In Codex, either:

- **Approve for the session** when first asked to run `miyo`, so later calls don't
  re-prompt; or
- **Allow network in the workspace sandbox** — in `~/.codex/config.toml`:
  ```toml
  [sandbox_workspace_write]
  network_access = true
  ```

Other sandboxed agents have equivalent settings (allow the command, or permit
loopback). None of this weakens Miyo's local-only model: the connection is still
loopback to a service on the same machine.

## `miyo: command not found` (or `miyo` not recognized)

**Try the full path before concluding anything** — it succeeds in the most common
version of this failure:

| OS | Binary path | PATH mechanism |
|---|---|---|
| macOS / Linux | `~/.miyo/bin/miyo` (symlink) | shell rc — `.zshenv`, or `.bashrc` + `.bash_profile` |
| Windows | `%LOCALAPPDATA%\Miyo\bin\miyo\miyo.exe` (full copy) | User `Path` env var |

In PowerShell, run it with the call operator: `& "$env:LOCALAPPDATA\Miyo\bin\miyo\miyo.exe"
search "…"` (`%LOCALAPPDATA%` only expands in `cmd`).

Causes, most likely first:

- **PATH is bare in this session.** Either the agent wasn't started from a terminal
  (an editor launching it over ACP, or any process started by launchd rather than a
  shell, begins with just `/usr/bin:/bin:/usr/sbin:/sbin` on macOS), or the shell is
  non-interactive (`bash -c` sources neither `.bashrc` nor `.bash_profile`). Neither
  reads the user's shell rc files, so the install is fine and PATH is correct for
  terminals; this session just can't see it. **Stop escalating** — the full path works,
  and no reinstall or terminal restart will help. The CLI lives under the user's home
  dir, which can never be on that bare PATH.
- **Fresh install, old terminal.** A new install needs **one new terminal** to pick up
  the updated PATH (Windows: a newly opened terminal inherits the new User `Path`).
- **Miyo was never installed.** The CLI ships with the desktop app. If the full path
  doesn't exist either, point the user to **https://miyo.md/**; installing and
  launching the app once puts the CLI in place. If it's still missing after a relaunch,
  the app may never have finished first-run setup. Have them open Miyo once more.

## Empty results

A `0`-exit `No results found.` is a legitimate answer. Before concluding the user
has nothing relevant:

- Check the corpus — was the question about a past AI chat? Retry with
  `--source chats` (a `--folder` search ignores it; name the chat folder instead).
- Check coverage — `miyo folders`. If `indexed_files` < `total_files` or
  `status` is still `indexing`, the index is incomplete; wait and retry. Files
  counted in `error_files` failed to index and never appear in search, so if
  the answer may be in one, tell the user it exists but couldn't be searched.
- Loosen the query — semantic search rewards conceptual phrasing; drop
  over-specific `--path` / `--mtime-*` filters.

## Pointing at a non-default service

Pass `--url http://127.0.0.1:9999` or set `MIYO_URL` to target another instance,
such as a dev build on another port.
