# Contributing

Thanks for wanting to help. This project grew out of one game, so the best contributions come from people using it on their own games and fixing what did not fit.

## Ways to help

- **Lessons learned.** Hit a trap with Godot, Codex, Runway, sprite-gen or the emulator? Add it to `docs/lessons-learned.md`, and if a skill should prevent it, add the rule to that skill too.
- **Skills.** Improve a `gf-*` skill, or propose a new one. Each skill must keep its file ownership clear and must not contradict `gf-producer`.
- **Tools.** Fix or extend `tools/gf`, the Codex launcher, the playtest kit or the Godot scripts. Mechanical work belongs in a tool, not in a prompt.
- **Platforms and engines.** Linux and Windows setup notes, iOS shipping experience, other engines.
- **Show your game.** Open a discussion or an issue with screenshots. If you want it in a showcase folder, say so in the PR and include a license file for the assets.

## Ground rules for changes

1. English only, in plain technical prose. No em dashes, no marketing tone.
2. Skills stay generic. A concrete example from a real game is fine when marked, for example "Example (David: Rise of a King): ...".
3. Do not hardcode paths, account names, package ids or model versions that only exist on your machine. Model names are examples, not requirements.
4. Keep `SKILL.md` frontmatter valid (`name`, `description`). The description is how Claude decides to load the skill, so keep it specific and include the phrases a user would actually say.
5. If you rename a file, a skill, a command argument or a production file heading, update every reference: other skills, the command, tools, templates, docs.
6. Run the tool tests before opening a PR:

   ```sh
   cd plugins/game-factory/tools/gf && python3 -m unittest discover -s tests
   ```

7. Never commit generated assets you do not have the rights to, API keys, or anything from a private game without permission.

## Testing a change locally

```text
/plugin marketplace add /absolute/path/to/your/clone
/plugin install game-factory@hessel
```

After editing, reinstall or run `/plugin` to refresh, and try the affected skill on a scratch game folder.

## Pull requests

- One topic per PR. Explain what problem you hit and how the change fixes it.
- For skill changes, describe how you tested it (which wave, which game, what came out).
- Bump the version in `plugins/game-factory/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` when the change affects users.

## Code of conduct

By participating you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
