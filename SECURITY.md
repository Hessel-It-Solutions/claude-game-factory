# Security policy

## Reporting a vulnerability

Report security problems privately through GitHub: open the **Security** tab of this repository and choose **Report a vulnerability**. Do not open a public issue for them.

Include what is affected (skill, command, tool), how to reproduce it and what an attacker could do with it. We aim to reply within a week.

## What this project runs on your machine

The plugin is a set of instructions for Claude Code plus a few local tools. It has no server and collects nothing. It does run things on your machine, so know what they are:

- **Skills drive Claude Code and Codex CLI.** They tell the agents to run shell commands, install tools, edit files in your game repo and call the Runway API with your account. Review what the agents propose, and keep Claude Code permission prompts on for anything outside the game folder.
- **Codex batches** run with `-s workspace-write` inside an isolated clone. `tools/codex/merge_batches.py` merges their output back and never follows or copies symbolic links, so a clone cannot smuggle a file from outside the project into your repo. Still review the full diff before committing: agent output is untrusted input.
- **The blind playtest kit** needs network access inside the Codex sandbox (adb uses TCP). Run it from an empty folder and against a disposable emulator. See `tools/playtest/README.md`.
- **Third-party tools** installed by `gf-setup` (sprite-gen, Godot, the Android SDK, Homebrew packages) run their own code. sprite-gen is pinned to a reviewed commit; review the diff before moving the pin.

## Secrets

- Never commit API keys, Runway or OpenAI tokens, Android keystores or keystore passwords. `gf-mobile` reads keystore data from environment variables only.
- Generated assets, prompts and wave reports are committed to your game repo. Do not paste credentials into prompts.

## Supported versions

Only the latest release on `main` gets fixes.
