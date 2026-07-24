# Troubleshooting the `miyo` CLI

## "Cannot connect to Miyo service / Is the Miyo app running?"

The CLI is a client of a local HTTP service that the **Miyo desktop app** owns. This
error means the service isn't reachable.

1. The `miyo` command you already ran is the check — a `1` exit with this message
   means the service isn't reachable. If you want a manual probe (e.g. to confirm
   the app is back up), `curl` the health endpoint directly, but you don't need to
   before a normal search:
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

## Miyo on another device (Tailscale / LAN)

Some users keep their index on one machine (a desktop) and want to reach it from
another (a laptop) — commonly over **Tailscale**. The CLI supports this: point it at
the remote host.

```bash
export MIYO_URL=http://my-desktop.tailnet-name.ts.net:8742   # MagicDNS name
# or a Tailscale IP:  export MIYO_URL=http://100.101.102.103:8742
miyo search "the thing I wrote on my desktop"
```

Two things have to be true, and both are the **user's** setup, not something the CLI
or an agent can do:

- **The service must be listening on a reachable interface.** By default Miyo binds
  to `127.0.0.1` (loopback only), so it is *not* reachable from other devices out of
  the box. The user has to start it with `MIYO_HOST` set to an address the other
  device can reach.
- **Bind narrowly, because the local API has no authentication.** Prefer binding to
  the device's **Tailscale IP** specifically — `MIYO_HOST=100.x.y.z` — so only the
  tailnet can reach it. Binding to `0.0.0.0` exposes the unauthenticated API to every
  network the host is on; only do that on a network you fully trust. The tailnet
  (WireGuard-encrypted, ACL-gated) is the security boundary here — there is no
  token or password on the service itself.

If `MIYO_URL` points at a remote host that isn't reachable, `miyo` reports the same
"Cannot connect" error as a stopped local service — check the tailnet connection and
that the remote Miyo is running and bound as above.

## Exit codes

- `0` — success (including a valid empty result).
- `1` — error: missing query, unknown flag, invalid date/`--limit`/`--source`,
  service unreachable, or a server-side failure.
