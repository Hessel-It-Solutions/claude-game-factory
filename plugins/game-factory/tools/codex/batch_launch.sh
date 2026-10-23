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
#   BOT_CMD       scenario bot command for the validation block, run with the clone's
#                 copy of the game in /tmp/game_<id>; leave empty to skip the bot step
#   BOT_PASS      expected PASS count the bot should print (shown in the brief)
set -eu

BRIEF=${1:?brief file}
ID=${2:?batch id}

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
  \`rsync -a --delete --exclude .godot $GAME_DIR/ /tmp/game_$ID/ && HOME=/tmp/h$ID $GODOT --headless --path /tmp/game_$ID --import; HOME=/tmp/h$ID $GODOT --headless --path /tmp/game_$ID -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit\`
  Report the exact total; nothing may fall below the baseline.
EOT
if [ -n "$BOT_CMD" ]; then
cat >> "$FULL" <<EOT
- Scenario bot, one run: \`HOME=/tmp/hb$ID $BOT_CMD > /tmp/bot$ID.log 2>&1; grep -c '^PASS' /tmp/bot$ID.log\`${BOT_PASS:+ (expected $BOT_PASS)}.
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
