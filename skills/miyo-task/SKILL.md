---
name: miyo-task
description: >-
  Schedule a prompt for Claude Code, Codex or OpenCode to run on this computer
  at set times and write its result to a file in the user's folders, and manage
  those scheduled tasks, with the local `miyo task` CLI. Reach for this whenever the
  user wants an agent to do something later or on a repeat, even when they
  don't mention Miyo: "every morning summarize my notes",
  "every weekday at 9, check ...", "remind me weekly to ...", "run this every
  Friday", "once on the 1st, ...", "set up a recurring job", "make this an
  automation", "schedule this prompt", "instead of a cron job". Also for tasks
  that already exist: "list my Miyo tasks", "what's scheduled", "turn off the
  task", "move it to 8am", "run it now", "delete that task". Needs the Miyo app
  running. Commands: `miyo task list|create|update|enable|disable|run|delete`.
  (Searching the user's notes is the `miyo-search` skill; converting a PDF is
  `miyo-parse`.)
---

# `miyo task`: scheduled prompts

A Miyo task is a saved prompt, a schedule, the agent that runs it, and the file or
folder it writes its result to. At each occurrence the Miyo app starts that agent on
this computer without a terminal, hands it the prompt, and then checks that the run
wrote to its output. Nobody reads the agent's reply as it arrives, so the file is the
result. The app's Automations tab only shows tasks. Only `miyo task` creates or changes one,
so when the user asks for a task, you write it.

## Prerequisites (check once)

The CLI ships with the **Miyo desktop app**, which also runs the local service that
stores and runs tasks. Invocation differs by OS below; the `miyo` subcommands are
identical everywhere.

**1. Invoke `miyo` by its full path**

Don't rely on `miyo` being on PATH. An agent that wasn't started from a terminal (an
editor running it over ACP, say) can inherit a bare environment that never sources the
user's shell rc files, so a plain `miyo` fails on a perfectly good install. Invoke the
CLI by its full install path instead. The form depends on the shell:

| Shell | Full invocation (replaces `miyo`) |
|---|---|
| macOS / Linux (bash, zsh) | `~/.miyo/bin/miyo` |
| Windows PowerShell | `& "$env:LOCALAPPDATA\Miyo\bin\miyo\miyo.exe"` |
| Windows cmd | `"%LOCALAPPDATA%\Miyo\bin\miyo\miyo.exe"` |

The examples below write plain `miyo` for brevity; swap in the full form for your shell
(`%LOCALAPPDATA%` only expands in cmd, so PowerShell must use `$env:LOCALAPPDATA`). Each
command runs in a fresh shell, so don't stash it in a variable. Write the path out.

If that path doesn't exist, fall back to a bare `miyo`, since a non-standard install may
still be on PATH. Only when both fail is Miyo actually missing: **tell the user to
install it from https://miyo.md/ and launch the app once**. First launch installs the
`miyo` CLI. If `miyo task` answers `Unknown command: task`, the installed Miyo is older
than tasks, so ask the user to update the app.

**2. Is the service up?**

Don't run a separate health probe. The first real command (usually `miyo task list`)
*is* the readiness check. If the service is down it exits `1` with **"Cannot connect to
Miyo service / Is the Miyo app running?"**. That means the app isn't running: **ask the
user to open it**. Inside a sandboxed agent such as Codex, that local connection counts
as network access and may need the user's approval the first time.

## Commands at a glance

| Command | Purpose |
|---|---|
| `miyo task list` | Every task, whether it is on, and its next run |
| `miyo task create --name --agent --agent-path --folder --output --prompt --rule` | Save a new task, switched off |
| `miyo task update <task> [fields]` | Change only the fields given |
| `miyo task enable <task>` / `disable <task>` | Switch it on or off |
| `miyo task run <task>` | Run it now and wait for the outcome |
| `miyo task delete <task>` | Delete it; its past runs stay in Activity |

`<task>` is the task's id or its exact name. Create and update also take
`--timezone`. Every command takes `--json`.
`miyo task --help` prints the full list.

## A worked example

User: *"Every weekday at 9, add what I left unfinished yesterday to today's daily note."*

**1. Know where the result goes.** Every task writes its result to a file in one of
the user's folders. Here the user said: today's daily note. When the user hasn't
said where the result should go, ask them before creating anything.

**2. Find the folder.** A run starts in its folder, which has to be registered with
Miyo. `miyo folders` lists them. Look inside the right one so the prompt can name real
paths (here, daily notes named `Daily/YYYY-MM-DD.md`).

**3. Create it, with yourself as the runner.** Claude Code:

```bash
miyo task create \
  --name "Loose ends" \
  --agent claude-code --agent-path "$(command -v claude)" \
  --folder "/Users/me/Notes" \
  --output "Daily" \
  --rule "DTSTART:20261001T090000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR" \
  --prompt "Append to today's daily note, Daily/YYYY-MM-DD.md, creating it if it doesn't exist yet. Read yesterday's daily note (on a Monday, read Friday's) and list what I left unfinished: unchecked boxes and TODO lines. Add them at the end of today's note under a '## Loose ends' heading, one per line, or 'Nothing left open.' if there are none. Don't change anything else in either note. Finish with one line saying what you changed, and what was refused or failed if anything you needed was."
```

The output is `Daily`, the folder, because today's note has a new name every day.
Codex writes `--agent codex --agent-path "$(command -v codex)"` in the same place, and
OpenCode `--agent opencode --agent-path "$(command -v opencode)"`. It prints the saved
task and its next three runs:

```
No --timezone given, so the task runs in this machine's time zone, America/Los_Angeles.
Created task "Loose ends" (c0c2fbe8-0750-4e08-9e5c-a2bc15b0c8b7)
   Agent: claude-code  Enabled: no
   Agent path: /Users/me/.local/bin/claude
   PATH: /Users/me/.local/bin:/opt/homebrew/bin:/usr/bin:/bin
   Folder: /Users/me/Notes
   Output: Daily
   Rule: DTSTART:20261001T090000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR  Time zone: America/Los_Angeles
   Prompt: Append to today's daily note, Daily/YYYY-MM-DD.md, ...
   Next runs: 2026-10-01 09:00, 2026-10-02 09:00, 2026-10-05 09:00
```

Check `Next runs` against what the user asked for (Thursday, Friday, then Monday here)
and tell them. Miyo saved the task switched off.

**4. Offer a test run.** It is how you find out what the run isn't allowed to do. Ask
the user whether to try it now, and say first that a test run writes for real: here it
appends to today's note. If they agree:

```bash
miyo task run "Loose ends"
```
```
Ran "Loose ends" (1cc185b1-f659-4a8f-8a6c-eaf2e0c37d90)
   Agent: Claude Code  Took: 41.2s
   Outcome: succeeded
   Wrote: Daily/2026-09-30.md
   Added 3 loose ends to Daily/2026-09-30.md.
```

Read the last line as well as the outcome. A run that was refused something can still
write its file and succeed; "When a run is refused something" below says what to do.

**5. Switch it on once the user says so,** and not before:

```bash
miyo task enable "Loose ends"
```

## Choosing the agent

Name yourself: `--agent claude-code` if you are Claude Code, `--agent codex` if you
are Codex, `--agent opencode` if you are OpenCode. These are the only three agents a
task can run. If you are none of them, ask the user which one to use, and check it is
installed. OpenCode has to be 2.x: Miyo refuses an OpenCode 1.x executable and says to
update it.

`--agent-path` is the absolute path of that agent's executable, taken from your own
shell with `"$(command -v claude)"`, `"$(command -v codex)"` or
`"$(command -v opencode)"` (PowerShell: `(Get-Command claude).Source` or
`(Get-Command opencode).Source`). If that prints an alias or nothing, find the real file
or ask the user for it. The CLI saves your shell's PATH with the task, and every run
uses that PATH, so create the task from a shell where the agent starts. The `PATH:`
line in the output shows what the task got. `--agent` always needs `--agent-path` in
the same command.

## Writing the schedule

`--rule` is an RRULE with a `DTSTART` line, written as one string with a literal `\n`
between the two lines:

- `DTSTART:YYYYMMDDTHHMMSS` is local wall-clock time in the task's time zone. Never add
  `Z` or `TZID`; the service refuses both.
- Its time is the time of day the task runs. Its date is the first day it may run: use
  today's date (`date +%Y%m%d`) for a repeating task, and the day itself for a one-time
  task.
- Leave out `--timezone` to use this machine's zone. Pass an IANA name such as
  `Europe/Berlin` only when the user asks for another zone.
- For several times a day, use `FREQ=DAILY` with `BYHOUR` and `BYMINUTE`. The service
  refuses `FREQ=HOURLY` or `FREQ=MINUTELY` combined with `BYHOUR` or `BYMINUTE`.
- The service refuses a rule with no future occurrence, so a one-time task has to be in
  the future.

| Request | `--rule` |
|---|---|
| Every weekday at 9:00 | `"DTSTART:20261001T090000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"` |
| Every day at 7:30 | `"DTSTART:20261001T073000\nRRULE:FREQ=DAILY"` |
| Every Friday at 17:00 | `"DTSTART:20261001T170000\nRRULE:FREQ=WEEKLY;BYDAY=FR"` |
| Every other Monday at 10:00 | `"DTSTART:20261005T100000\nRRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=MO"` |
| At 9:00 and 17:00 every day | `"DTSTART:20261001T090000\nRRULE:FREQ=DAILY;BYHOUR=9,17;BYMINUTE=0"` |
| Every 2 hours, from 8:00 | `"DTSTART:20261001T080000\nRRULE:FREQ=HOURLY;INTERVAL=2"` |
| The 1st of every month at 9:00 | `"DTSTART:20261001T090000\nRRULE:FREQ=MONTHLY;BYMONTHDAY=1"` |
| The last day of every month at 18:00 | `"DTSTART:20261001T180000\nRRULE:FREQ=MONTHLY;BYMONTHDAY=-1"` |
| The first Monday of every month at 9:00 | `"DTSTART:20261001T090000\nRRULE:FREQ=MONTHLY;BYDAY=1MO"` |
| Weekdays at 9:00 until the end of the year | `"DTSTART:20261001T090000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;UNTIL=20261231T235959"` |
| Once, on 1 November at 8:30 | `"DTSTART:20261101T083000\nRRULE:FREQ=DAILY;COUNT=1"` |

## Writing the prompt

A fresh agent runs the prompt later, with no memory of this conversation and nobody to
answer its questions. Make it self-contained: what to read (paths relative to the
folder), which file to write, and what to write when there is nothing to report.

- Name the file the result goes in, inside the task's output, and say whether to
  append to it or create a new file each run. Prefer appending to one named file over
  rewriting it: an unattended run that rewrites a note can lose what the user wrote.
- Ask for a one-line final reply saying what changed, and what was refused or failed if
  anything it needed was. Activity shows it under the file the run wrote, and it is
  where a refusal shows up.
- After each run Miyo looks in the output for files created or edited during the
  run. A run that finished without writing there is recorded as "Nothing written",
  whatever it replied, so a prompt that only asks for an answer never succeeds.

## When a run is refused something

A run never stops to ask, so anything the user's agent would normally ask about is
refused, and the agent carries on without it. The run can still write its file and
read "succeeded", so look for refusals in the test run's last line:

- Claude Code says what it was refused, naming the command.
- Codex's sandbox doesn't refuse a command, it lets it fail: a network call or a write
  outside the task's folder fails, and only the last line says so, if the prompt asked.
- OpenCode refuses whatever would need approval and carries on.

When the test run was refused something the task needs:

1. Tell the user what was refused and why the task needs it.
2. Propose the narrowest fix: a prompt that does without it when the task can, or else
   a change to their agent's own settings that allows only that, such as a rule for
   that one command rather than every shell command. You are the task's agent, so
   these are your own settings.
3. Change the settings only after the user says yes. The change outlives the task:
   every later run gets it, and so does the user's own use of their agent.
4. Run the test again.

## Folder and output

Every task needs both:

- `--folder` takes a folder registered with Miyo, by the absolute path
  `miyo folders` shows. The run starts there and writes there. The service refuses a
  folder that isn't registered; the user adds folders in the Miyo app.
- `--output` is the file or folder inside it that each run writes: a file to create
  or edit, or a folder to write new files into. Give it relative to `--folder`, or as
  an absolute path inside it. It can't be the folder itself. When the file's name
  changes from run to run, such as today's daily note, give the folder that holds it.

## What to tell the user

Relay these plainly when you create a task; they are what the user can rely on:

- A task runs only while the Miyo app is running and the computer is awake. It starts
  up to half a minute after its time.
- If the computer slept or Miyo was closed through several occurrences, the task runs
  once to catch up when Miyo is next running.
- Switching a task on, or changing it, never runs an occurrence whose time has already
  passed. The first run is the next one due.
- If a run is still going when the next occurrence falls due, Miyo records that
  occurrence as skipped. Two runs of one task never overlap. A run still going after 30
  minutes is stopped and recorded as failed.
- New tasks start switched off. Every run writes for real, test runs included.
- A run uses the user's own agent settings, and Miyo adds only two things. It never
  stops to ask for approval, so anything their agent would normally ask about is
  refused. And it may edit files in the task's folder. Beyond that, it can do no more
  than their agent already does without asking.
- A task's own run can create a new task, only switched off, and cannot switch a task
  on, change, run or delete one. Those take a person.
- Each run's result is the file it wrote. The Miyo app's Activity tab, under Local
  with the Tasks filter, lists each run with the file it wrote and its one-line
  summary. Miyo sends no notification, so for "remind me to ..." say which file the
  reminder will land in.
- Each run uses the user's own agent login and counts against their plan, so a task
  that runs often costs accordingly.
- For an OpenCode task, check the user's OpenCode config for `share: "auto"`. If it is
  set, warn them that every run of the task will be shared publicly.

## Managing tasks

```bash
miyo task list                                          # every task, on or off, next run
miyo task update "Loose ends" --rule "DTSTART:20261001T080000\nRRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
miyo task update "Loose ends" --prompt "..."            # only the fields given change
miyo task disable "Loose ends"
miyo task enable "Loose ends"
miyo task run "Loose ends"
miyo task delete "Loose ends"
```

- Look up the task with `miyo task list` before changing it, and name it by id when
  two tasks could match.
- Names are unique. The service refuses a second task with a name already in use, so
  update the existing one instead.
- `run` waits until the agent finishes, which can take minutes, so give the command a
  long timeout. It exits `0` only when the run succeeded, which means it wrote to its
  output, and `1` when it wrote nothing, failed, was cancelled, or the task was already
  running. "Nothing written" means the prompt needs fixing: make it name the file to
  write and say how.
- If `run` stops before the agent finishes, because your shell timed out or the CLI
  said "Cannot connect to Miyo service" partway through a long run, the run carries on
  in Miyo and its outcome lands in Activity. If `miyo task list` still answers, the app
  is running; tell the user where to find the result rather than asking them to open
  Miyo.
- `enable` checks the schedule and the agent path again, so a one-time task whose time
  has passed can't be switched back on. Give it a new `--rule` instead.
- A refused command exits `1` with the service's reason. Read it, fix the one thing it
  names, and try again rather than guessing.
