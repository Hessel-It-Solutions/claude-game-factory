# tools/codex

Scripts for running Codex CLI batches in isolation and bringing the results back.

- `batch_launch.sh <brief-file> <batch-id>`: copies the repo into an isolated clone, appends the
  environment, validation and restrictions blocks to the brief, and starts `codex exec` in the
  background. Clones go to `$WT_ROOT` (default `../_wt_<repo name>/batch-<id>`).
  On macOS the clone is an APFS copy-on-write copy (`cp -cR`, instant, keeps untracked files such
  as the `.godot` cache). Elsewhere it falls back to `git worktree add --detach` (tracked files only).
- `merge_batches.py --base <baseline> --main <main tree> [--apply] <clone>...`: per-file three-way
  merge (`git merge-file`) of each clone against a pristine baseline into the main tree. Lists files
  taken as is, merged, and conflicts (left with conflict markers). It never deletes files.

Environment for `batch_launch.sh`: `WT_ROOT`, `GAME_DIR` (default `game`), `GODOT`, `CODEX_MODEL`
(optional, example: your Codex coding model), `CODEX_EFFORT` (default `medium`), `BOT_CMD` and
`BOT_PASS` (optional scenario bot step in the validation block).

Rules baked into the script:

- `codex exec ... < /dev/null`, always. Without it Codex waits on stdin and hangs in the background.
- No `timeout` command inside the batch (it does not exist on stock macOS, and a killed run loses its work).
- The GUT suite runs in an `rsync` copy of `game/` with its own `HOME`, so parallel batches do not
  share a Godot user dir or import cache.
- The batch writes its own report to `production/waves/batch-<id>.out.md`; the final Codex message
  lands in `batch-<id>.last.md` and the raw log in `batch-<id>.codex.log`.

## Brief template

Keep it short. A long brief gets partly ignored.

```markdown
# Batch <id>: <one-line goal>

## Acceptance criteria
1. <observable behavior, one line each, 5 to 10 items at most>
2. ...

## Owned paths (change only these)
- game/scripts/<area>/...
- game/tests/test_<batch>.gd (new)

## Numbers to report
- GUT total (exact), and how many are new
- Scenario bot PASS count
- Paths of the captures, one per visible change

## Restrictions
- Do not touch: <shared files, autoloads, project.godot unless listed>
- No refactors, renames or reformatting outside the owned paths
- Do not edit the bot to make it pass; if the old behavior changed, say so in the report
- No commit
```

## Trust checklist (before you accept a batch)

Codex reports are claims, not evidence. It has faked captures, patched the bot to pass, and written
tests that only read source text.

1. Read the whole diff of the batch, not just the report. Look at test files and bot files first.
2. Merge into main, then run the full suite on main (not only inside the clone).
3. Run the scenario bot on main and compare with the baseline numbers. A drop is a regression, even if the report says otherwise.
4. Reject tests that only read source (`FileAccess.get_file_as_string`, regex over `.gd`) instead of exercising behavior.
5. Open the captures yourself. Check they are real window captures of the new state, not stale or edited images.
6. Keep at most 3 baselines (clones that are still a reference for a pending merge) and delete each batch clone after its merge.
