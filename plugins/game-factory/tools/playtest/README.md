# Blind playtest kit

A tester that sees only screenshots and sends only touches, driven through adb. It measures
what a first-time player understands, which bots and unit tests cannot. Used by the
`gf-playtester` skill.

Files:

- `cap.sh NNN`: screenshot via adb, saved as `NNN.png` plus a downscaled `small/NNN.jpg`.
- `in.sh`: `tap`, `swipe`, `keyevent`, or `burst '<shell snippet>'` for several inputs in one
  adb call (reflex scripts).
- `PROMPT_tester.md`: the tester prompt with `{{PLACEHOLDERS}}`.

Requirements: `adb`, `ffmpeg` (for the small copies), `perl` (portable timeout on macOS).

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `SESSION_DIR` | current directory | where captures and journals go |
| `ADB` | `adb` from PATH, else `~/Library/Android/sdk/platform-tools/adb` | adb binary |
| `ADB_SERIAL` | `emulator-5554` | device serial (`adb devices`) |
| `SCALE_DIV` | `2` | divisor for the small copy |

The package id is not used by the scripts. It only appears in the prompt (`{{PACKAGE_ID}}`).

## Before the run (main session)

1. Use a dedicated test AVD, or back up the user's save first and restore it after.
2. Fresh install: `adb install -r <apk>`, `adb shell pm clear {{PACKAGE_ID}}`, open the game,
   confirm the first screen renders. Emulator flags: `-no-snapshot-load -no-audio`.
3. Check machine load. A loaded machine makes the emulator ANR and every capture take
   12 to 20 s; deaths then measure the machine, not the game.
4. Create a session folder, for example `production/qa/playtest/2026-01-01_run1/`, and copy
   `cap.sh` and `in.sh` into it (or call them by path with `SESSION_DIR` set).
5. Fill the placeholders of `PROMPT_tester.md`. Add no hints about the game.

## Running with a Claude subagent

Launch a fresh `Agent` (`general-purpose`, `model: "fable"` or `"opus"`) with the filled
prompt, from the tester's first line down. Never a fork and never the main session.
Expect 35 to 50 minutes and roughly 700k tokens for a long run. If the API overloads and
the tester dies, resume it with `SendMessage`, telling it to re-read `diary.md`,
`lessons.md` and `arsenal.md`.

## Running with `codex exec`

Cheaper on the Anthropic quota. Use an empty working folder and keep stdin closed:

```bash
mkdir -p /tmp/playtest01 && cd /tmp/playtest01
codex exec -s workspace-write \
  -c sandbox_workspace_write.network_access=true \
  -m <your strongest model> -c model_reasoning_effort='"high"' \
  - < prompt_filled.md
# or: codex exec ... "$(cat prompt_filled.md)" < /dev/null
```

- `network_access=true` is required: adb talks to its server on TCP 5037.
- `< /dev/null` (or a prompt on stdin): without it `codex exec` waits on stdin forever.
- Quote heredocs with `<<'EOF'`, otherwise backticks run as commands.
- The image viewer refuses the screencap PNG; Codex converts it to JPEG itself, which is fine.
- A smaller model at medium reasoning played badly and stopped early. The prompt already
  forbids ending before 15 minutes stuck and asks for a diary written while playing.
- If the quota ends mid-run, build a save at the last checkpoint seen and ask the same
  tester to re-read its three journal files. `codex exec resume --last` re-reads the whole
  session (cost accumulates).

## Journals the tester writes

- `diary.md`: one line per decision: `hh:mm | screen | what I see | what I think | what I did | result`,
  with tags [LOST] [DID NOT UNDERSTAND] [MISLED] [FRUSTRATED] [LIKED] [BUG?].
- `lessons.md`: one entry per death: what killed me, did I fight back and with what, next plan.
- `arsenal.md`: every action the screen showed, and what it did when tested.
- `report.md`: sections 1 to 10 listed in the prompt (progress and deaths, objectives table,
  friction by priority, what worked, controls, reading the screen, orientation, pace,
  feedback, top 10).
- Optional reflex scripts (`fight1.sh`, ...) with touches only.

## Reading the result

- Deaths tagged [TESTER LATENCY] are not game friction. Before touching balance for "I hit
  it 13 times and nothing happened", run a fixed-reaction probe.
- If you change the method mid-way, split the report into Phase A and Phase B.
- After each round of fixes, start a fresh tester from the first screen.
- Restore the user's save and shut the emulator down at the end.
