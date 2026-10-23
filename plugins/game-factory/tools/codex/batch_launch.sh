#!/bin/sh
# Launch one Codex batch in an isolated clone of the project.
#
# usage: tools/codex/batch_launch.sh <brief-file> <batch-id>
#   brief-file  markdown brief (acceptance criteria, owned paths), relative to the repo root
#   batch-id    short id, for example u1; names the clone and the output files
#
# environment (all optional):
#   WT_ROOT       where clones go (default: ../_wt_<repo name>)
#   GAME_DIR      Godot project folder inside the repo (default: game)
#   GODOT         Godot binary (default: godot)
#   CODEX_MODEL   Codex model passed with -m (default: Codex's own default)
#   CODEX_EFFORT  reasoning effort (default: medium)
#   BOT_CMD       scenario bot command for the validation block, run against the clone's
#                 scratch copy of the game in .batch/game; leave empty to skip the bot step
#   BOT_PASS      expected PASS count the bot should print (shown in the brief)
set -eu

BRIEF=${1:?brief file}
ID=${2:?batch id}

# These values end up in file paths and in the `sh -c` command line below, so only allow
# plain names: anything else could run shell code or point outside the clone folder.
case "$ID" in ''|*[!A-Za-z0-9_-]*) echo "batch id must match [A-Za-z0-9_-]+: $ID" >&2; exit 2 ;; esac
case "${CODEX_EFFORT:-medium}" in minimal|low|medium|high|xhigh) ;; *) echo "CODEX_EFFORT must be minimal, low, medium, high or xhigh" >&2; exit 2 ;; esac
case "${CODEX_MODEL:-x}" in *[!A-Za-z0-9._:-]*) echo "CODEX_MODEL must match [A-Za-z0-9._:-]+" >&2; exit 2 ;; esac

SRC=$(cd "$(dirname "$0")/../.." && pwd)
NAME=$(basename "$SRC")
WT_ROOT=${WT_ROOT:-"$SRC/../_wt_$NAME"}
GAME_DIR=${GAME_DIR:-game}
GODOT=${GODOT:-godot}
CODEX_EFFORT=${CODEX_EFFORT:-medium}
BOT_CMD=${BOT_CMD:-}
BOT_PASS=${BOT_PASS:-}
WT="$WT_ROOT/batch-$ID"

[ -f "$SRC/$BRIEF" ] || [ -f "$BRIEF" ] || { echo "brief not found: $BRIEF" >&2; exit 2; }
case "$BRIEF" in /*) BRIEF_ABS=$BRIEF ;; *) BRIEF_ABS=$SRC/$BRIEF ;; esac

mkdir -p "$WT_ROOT"
if [ -e "$WT" ]; then
  echo "clone already exists: $WT (delete it after merging the previous run)" >&2
  exit 2
fi

# Isolated clone. APFS copy-on-write on macOS is instant and carries untracked files
# (.godot import cache, generated art). On Linux fall back to a detached git worktree,
# which only has tracked files: run the Godot import step inside it.
if cp -cR "$SRC" "$WT" 2>/dev/null; then
  :
else
  rm -rf "$WT"
  git -C "$SRC" worktree add --detach "$WT"
fi

OUT_DIR="$WT/production/waves"
mkdir -p "$OUT_DIR" "$WT/production/codex"
FULL="$WT/production/codex/batch-$ID.full.md"
cat "$BRIEF_ABS" > "$FULL"
cat >> "$FULL" <<EOT

## Environment
You are in an isolated clone of the project (the current directory). Other batches run at the same
time in their own clones; the changes are merged afterwards by diff. So change only what the batch
needs: no reformatting, no renames outside the batch, so the merge stays clean. New player-visible
strings go in a file of their own (for example $GAME_DIR/i18n/batch_$ID.csv), not in the shared strings file.

## Validation (mandatory, report the numbers)
- Test suite (GUT) in an rsync copy with its own HOME, so parallel batches do not fight over
  the Godot user dir and the import cache:
  \`mkdir -p .batch/home && rsync -a --delete --exclude .godot $GAME_DIR/ .batch/game/ && HOME=\$PWD/.batch/home $GODOT --headless --path .batch/game --import; HOME=\$PWD/.batch/home $GODOT --headless --path .batch/game -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit\`
  Report the exact total; nothing may fall below the baseline.
EOT
if [ -n "$BOT_CMD" ]; then
cat >> "$FULL" <<EOT
- Scenario bot, one run: \`mkdir -p .batch/home_bot && HOME=\$PWD/.batch/home_bot $BOT_CMD > .batch/bot.log 2>&1; grep -c '^PASS' .batch/bot.log\`${BOT_PASS:+ (expected $BOT_PASS)}.
  If the bot depended on the old behavior, adjust the bot without hiding a regression. The full multi-seed bot runs happen after the merge.
EOT
fi
cat >> "$FULL" <<EOT
- New GUT tests for each fix, exercising the real code path (a test that only reads source text does not count).
- Window captures in $GAME_DIR/.captures/$ID/ showing each visible change.

## Restrictions
No adb, no emulator. No \`timeout\` command. No commit. At the end write production/waves/batch-$ID.out.md:
what changed per item, files changed, GUT total, bot PASS count, captures, what you did not solve and why.
EOT

cd "$WT"
# stdin must be /dev/null: without it codex exec waits on the terminal and hangs when backgrounded.
MODEL_ARG=""
[ -n "${CODEX_MODEL:-}" ] && MODEL_ARG="-m $CODEX_MODEL"
nohup sh -c "codex exec $MODEL_ARG -c model_reasoning_effort='\"$CODEX_EFFORT\"' -s workspace-write --skip-git-repo-check -o production/waves/batch-$ID.last.md \"\$(cat production/codex/batch-$ID.full.md)\" < /dev/null > production/waves/batch-$ID.codex.log 2>&1; echo \"exit \$?\" >> production/waves/batch-$ID.codex.log" >/dev/null 2>&1 &
echo "launched batch-$ID in $WT"
echo "log:    $WT/production/waves/batch-$ID.codex.log"
echo "report: $WT/production/waves/batch-$ID.out.md (final message: batch-$ID.last.md)"
