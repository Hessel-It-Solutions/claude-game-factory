# Codex batch <id>: <short title>

You are working on <game> in the current directory, an isolated copy of the project. Other batches run at the same time in their own copies; changes are merged later by diff. Change only what this brief needs. Do not reformat or rename anything outside it.

## Acceptance criteria
1. <observable, measurable behavior>
2. 

## You own only these paths
- 

## Do not
- Change the scenario bot to make it pass. If the bot depended on old behavior, say so in the report.
- Write tests that only read source code.
- Edit generated files (list them here).
- Use adb or the emulator. Commit.

## Validation (report the exact numbers)
- Full GUT suite total, nothing may drop.
- Bot PASS count.
- New GUT tests for each criterion in game/tests/test_<id>.gd.
- Windowed captures of each visible change in game/.captures/<id>/.

## Report
Write production/waves/<id>.out.md: what changed per criterion, files changed, GUT total, bot PASS, captures, what did not get solved and why.
