# Remote MCP — Miyo over the relay

Miyo exposes two agent interfaces:

1. **The local CLI** (`miyo …`) — for tools running on the same machine as the
   Miyo app. Read-only: `search`, `files`, `folders`. This is what a local agent
   (Claude Code, a shell script) should use.
2. **The remote MCP** — for cloud AI clients (ChatGPT, Claude on claude.ai, etc.)
   that aren't on the user's machine. Reaches the user's local Miyo through the
   hosted relay, and adds **write** tools on top of search.

> **Deprecated:** the local stdio MCP server (`miyo mcp`) is no longer the
> recommended path. Don't wire new integrations to it. On the same machine, call
> the CLI directly; for a remote client, use the relay MCP described here.

## How the remote MCP reaches local data

```
Cloud client (ChatGPT / Claude)
   │  HTTPS + OAuth 2.1 bearer token
   ▼
relay.miyo.md  ──WSS──▶  Miyo desktop app  ──localhost HTTP──▶  local service :8742
```

The relay stores **no documents**. Every request is forwarded over an authenticated
WebSocket tunnel to the user's desktop, runs against their local index, and the
result is returned through the relay. If the desktop is offline the relay returns
`503` — the data simply isn't reachable. (Architecture detail lives in the Miyo
repo at `docs/arch/relay.md`.)

## Enabling it (user action, one time)

This is set up by the **user**, not by an agent:

1. In the Miyo desktop app, sign in and turn on **Miyo Connect** (opens the tunnel
   to `relay.miyo.md`).
2. In the cloud client, add Miyo as a remote MCP / connector and complete the OAuth
   sign-in (magic link to the same email). The client then discovers Miyo's tools
   automatically.

An agent can't perform these steps; if a remote client reports Miyo as
unavailable, point the user here.

## Tool surface

An MCP client discovers these automatically — you don't hand-write schemas. Listed
so you know what the remote surface can do (it's a superset of the CLI).

| Tool | What it does | Write? |
|---|---|---|
| `search` | Semantic search; `source` = `documents` (default) or `chats`. Same engine as `miyo search`. | no |
| `list_folders` | Folders + file counts + `allow_writes`. | no |
| `list_files` | List indexed files, filter by title/path/mtime. | no |
| `read_file` | Full contents of a file by path (text, or base64 for images). Use after `search` to expand a hit. | no |
| `create_file` | Create a new file in a folder where `allow_writes` is true. Won't create new subfolders. | **yes** |
| `edit_file` | Targeted `old_text`→`new_text` replacement in an existing file (must match exactly once). | **yes** |

The CLI is read-only; `read_file` and the two write tools exist **only** on the
remote MCP. A local agent that needs full file contents should read the file from
disk instead — resolve the folder's `absolute_path` from `miyo folders` and join it
with the result path. A local agent that needs to write should write to disk
directly (within a folder Miyo watches; Miyo re-indexes it).

## Which interface for which agent

- **On the user's machine** (local shell/agent): use the **CLI**. Lowest latency,
  no auth, no relay.
- **A hosted assistant** (ChatGPT, claude.ai): use the **remote MCP** — it's the
  only way to reach the user's local index from off-machine.
