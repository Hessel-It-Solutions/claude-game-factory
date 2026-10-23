---
name: gf-playtester
description: "Blind playtester for the game. Plays the build on the Android emulator like an ordinary player who has never seen the game: only looks at the screen (screenshots) and touches it, without reading code, docs, script, handoff or memory, and without knowing where anything is. Notes every moment of doubt, where it got lost, what it misread and how long it was stuck, and delivers a diary with prioritized friction points. Use when the user asks to \"run a blind playtest\", \"test it like a player\", \"game tester\", \"play it knowing nothing\", \"would a normal user understand this?\", or before a chapter gate, after gf-autotest."
---

# gf-playtester: the player who knows nothing

A blind tester. It plays the build on the Android emulator like a person who has never seen the game, using only screenshots and taps, never the code or the docs. It writes a diary of every doubt, wrong reading and dead end, and ends with a prioritized list of friction points. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Checking whether a normal player would understand the game
- Before a chapter gate, after gf-autotest is green
- After a round of UX fixes, with a fresh tester

Produces: `production/qa/playtest/<run>/` with diary, lessons and report.

Works with: gf-qa, gf-rpg-review, gf-ui.

---

The bots and gf-autotest know where to go. This skill exists for the opposite: finding out
what a **real** player understands from what is on the screen alone. It fixes nothing. It
writes only the diary and the report. Reply to the user in the user's language; the tester
writes in the language the user asks for.

The reusable kit (scripts and the tester prompt template) is in `tools/playtest/`
(`cap.sh`, `in.sh`, `PROMPT_tester.md`, `README.md`). gf-setup copies it into the game repo.

## Golden rule: black box

The tester is a **fresh subagent** (Agent, `general-purpose`) or a fresh `codex exec`
process, never the main session and never a fork. The main session knows too much.

The tester prompt carries **only**: the black-box rules, the "How to play", "What to
write" and "Delivery" sections of the template, the requested scope (e.g. "play from the
start as far as you can, for up to 60 minutes"), the device serial and the output folder.
No level names, puzzles, lines of dialogue, solutions or known bugs.

The tester **must not**:
- read any file of the repository (code, `docs/`, `production/` outside its output folder,
  `art/`, README, CLAUDE.md, memory), search the code, or use a memory plugin;
- read the save, logcat or any internal game state;
- use the bot, GUT, the Godot capture scripts, or change flags;
- ask the main session how to get past a part.

It may: `adb exec-out screencap -p`, `adb shell input tap|swipe|keyevent|motionevent`,
`adb shell wm size`, view the PNGs it captured itself and write to its output folder
(`production/qa/playtest/<run>/`).

If stuck, it acts like a player: explores, tests buttons, goes back, re-reads what is on
screen. After **10 minutes stuck on the same objective** it notes "would quit here" with
the last screen and tries 5 more minutes before ending that stretch. It may not end the
session before the 15 minutes of being stuck have elapsed.

## Method: play like a person

A tester that captures, thinks for a long time and acts once per screenshot loses every
real-time fight, because adb round trips take seconds and the game runs in real time. Use
this method (it is in the prompt template):

- **Think with the game paused, act in bursts.** Pause for danger, new text or real doubt;
  when decided, unpause and act in bursts (one `adb shell "..."` call with several taps).
  Without danger on screen, do not pause or think long: walk in long drags, explore with
  curiosity, chain several actions before capturing again.
- **After each script, capture and look at the result.** A tester once beat a boss blind
  and never saw it.
- **Arsenal.** Keep `arsenal.md`: every action button, item, ranged attack, dodge, heal that
  the screen has shown, and what each did when tested.
- **Always fight back.** Standing still, only fleeing or only watching while being hit is not
  an option. Watch the enemy pattern before spending resources.
- **Reflex scripts.** Short `adb shell input` scripts for tested sequences ("throw 3
  stones", "hit, hit, dodge", "back off and shoot"), like muscle memory. Touches only:
  never read the game from the inside.
- **Deaths log, `lessons.md`.** One entry per death or failure: (1) what killed me, (2) did I
  fight back and with what, (3) the plan for the next life with one concrete change. Re-read
  it before trying again. Never repeat a plan that has failed twice.
- **Dying without fighting back** is the tester's failure, not the game's, unless the screen
  gave no way to fight back: then note [DID NOT UNDERSTAND] with what was missing.
- **Tester latency.** A death caused purely by slow reaction is marked [TESTER LATENCY] and
  does not count as game friction. Real damage bugs and tester latency look alike
  ("I hit 13 times and the bar did not move"); the main session settles it with a probe
  with a fixed reaction before touching balance.
- Real timestamps from `date +%H:%M`, not from memory.

## Preparation (main session, before calling the tester)

1. Never use the user's save. Use a dedicated AVD for testing or, on the user's AVD, back
   up first and restore after (`adb shell run-as <package> cat files/save_0.json >
   /tmp/save_backup.json`). `pm clear` only on the test AVD or with the backup made.
2. Install the APK under test and **open the first screen once yourself**. Clear data and
   open the APK on a fresh install first: an untested first boot with no saved language
   left a game black on Android. Check that the APK registers only `.translation` files
   (never `.csv`), or translation keys show raw on the phone and no unit test catches it.
3. Start the emulator with `-no-snapshot-load` (a snapshot sometimes stops forwarding touch)
   and `-no-audio` (the tester only sees screenshots). Check the emulator uses the host GPU,
   not software rendering (shader compile can take minutes and looks like a freeze).
4. Pass the tester the serial (`adb devices`) and the screen size (`adb shell wm size`).
5. **Machine load.** With other heavy processes running (other agents, Docker, databases,
   IDEs), the emulator gets ANRs and the tester spends 12 to 20 s per capture: deaths in that
   state do not measure the game. Close the heavy apps, check load and swap, warn the
   user, and stop the run if load climbs.
6. Prepare **resume saves** for long games: keep a save at the start of each part (with
   counters and hints reset) outside the repo, so a run can start where the previous one
   ended or restart a hard section.

## Who runs the tester: cost trade-off

- **Claude (Agent with `model: "fable"` or `opus`)**: plays the most reliably, but a 35 to 50
  minute run costs roughly 700k tokens. Several runs a week are the biggest spend of a project.
- **Codex (`codex exec`)**: spares the Anthropic quota and works: run it in an empty folder
  (`/tmp/playtestNN`), with `cap.sh`/`in.sh` and the image viewer. Use your strongest Codex
  model with high reasoning (a smaller model at medium reasoning played badly and stopped
  early). Demand that the diary is written **during** the play, forbid ending before 15 minutes
  stuck. It needs `-c sandbox_workspace_write.network_access=true` (adb talks to the server
  on TCP 5037), which opens the network for the whole sandbox: run it from an empty folder that
  holds only the prompt and the kit, never from the game repo. Run it with `< /dev/null`.
- If the Codex quota runs out mid-run: build a save at the last checkpoint seen and tell the
  same tester to re-read diary, arsenal and lessons. An API overload error (HTTP 529)
  kills a Claude tester the same way: resume it with SendMessage telling it to re-read
  the three files.
- Pick per run: Claude when reliability matters (gate runs), Codex for routine rounds.

## Rounds

- **The same player continues** until the chapter is closed (it remembers what it saw,
  nothing of the design).
- **After each round of fixes, a fresh tester** from zero, with the full method from the
  first screen. A tester that knows the old build misses the new confusion.
- **Phase A / Phase B.** If the method changes mid-way (new rules, new tooling), split the
  report into Phase A and Phase B: data from before the adjustment is biased.
- Run long games in parts (e.g. first half, second half from a resume save).
- After the report: validate it against the code and bring back what is still missing with a
  proposal and a cost.

## What to write

Diary `production/qa/playtest/<run>/diary.md`, one line per relevant decision (not per touch):
`hh:mm | screen NNN | what I see | what I think I should do | what I did | what happened`.

Tag with:
- **[LOST]** I do not know where to go or what to do;
- **[DID NOT UNDERSTAND]** text, icon or button that made no sense;
- **[MISLED]** something looked like one thing and was another (a passage that was a wall,
  an item that cannot be picked up);
- **[FRUSTRATED]** died or repeated without understanding why;
- **[LIKED]** a good moment, so it is not lost in refinement;
- **[BUG?]** looks like an error (froze, vanished, went through a wall; includes text in the
  wrong language).

Time each objective: when it appeared (or when you realized what to do) and when it was done.
Also `lessons.md` and `arsenal.md` as described above.

## Delivery

`production/qa/playtest/<run>/report.md` (in the language the user asked for):
1. How far I got, total time, deaths (separate game blockers from tester latency), and how
   tactics changed from one death to the next.
2. Objectives table: objective as the player understood it, time, attempts, result.
3. Friction points by priority (high: would make a player quit; medium: stuck more than
   2 min; low: annoyance), each with the reference screen and a player quote.
4. What worked.
5. Controls. 6. Reading the screen and language (list all text in the wrong language).
7. Orientation (the player must never be left without knowing where to go). 8. Pace and
difficulty. 9. Feedback. 10. Top 10 improvements with screens.

Per attempt on a section, say whether the game taught the player or it was trial and error.

The main session then reads the report, cross-checks it with the design (now it may read
code and docs), tags the owning skill of each item (gf-levels, gf-ui, gf-narrative,
gf-gameplay) and takes it to the user. Restore the user's save if their AVD was used. If
the user starts working on the machine and the load rises, stop the tester, restore the
save, shut the emulator down and keep the state for resuming.
