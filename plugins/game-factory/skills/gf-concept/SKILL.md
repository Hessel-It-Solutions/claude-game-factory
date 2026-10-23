---
name: gf-concept
description: Mobile game concept: interview with the user, alternative pitches, reference and market research, and the document docs/00-concept.md (premise, genre, core loop, audience, pillars, platform, monetization, scope, pixel art style). Use in W1 of /game-factory, when the user wants to discuss a new game idea, compare pitches, "pitch me a game", or revise the concept after G1 was rejected.
---

# gf-concept: concept

The first thing that happens in a game. No final art, code or script before G1.

## 1a. Interview (main context)

Use AskUserQuestion, up to 4 questions per round, at most 3 rounds. Always offer concrete options and a recommendation. Cover:

1. **Player fantasy**: what does the person feel while playing? (example: "being the shepherd who becomes king")
2. **Genre and camera**: 2D side platformer, top-down action, tactical RPG, metroidvania, runner, puzzle, roguelite, narrative adventure.
3. **Mobile session**: typical length (2 min, 10 min, 30 min), portrait or landscape, one hand or two.
4. **Touch controls**: virtual joystick, tap-to-move, swipe, contextual buttons.
5. **Audience and tone**: age, content sensitivity (violence, religious or historical themes), humor vs epic.
6. **References**: 2 to 4 games the user loves and what to take from each.
7. **Pixel art**: density (16-bit 32px, HD pixel 64px+, large portraits), visual reference. The final decision belongs to gf-art-direction in W2; here only the intent.
8. **Monetization**: premium, F2P with ads, F2P with IAP, demo + unlock. This defines whether gf-mobile handles ads/IAP later.
9. **Scope**: target size (hours of play, number of chapters), deadline, platforms (Android, iOS).

What the user already said in the request is not asked again.

## 1b. Research and pitches (subagents)

**Pitches**: 3 proposals from the interview, each with:

- working title and logline (1 sentence);
- genre, camera, screen orientation;
- core loop in 3 to 5 steps (action → reward → progression);
- 3 design pillars (what can never be missing);
- market hook (why someone downloads this one and not another);
- main risk and how to mitigate it;
- estimated MVP scope (chapters/levels, characters, scenes).

The three must be truly different (different genre or loop), not name variations.

**References and market**: for the genres in play, list 5 to 8 comparable mobile pixel art titles, with what each does well (loop, control, monetization, art), store ratings when available through WebSearch, and gaps our game can fill. Cite the sources.

Agent output: `production/waves/01-concept.gf-concept.pitches.md` and `...gf-concept.market.md`.

## 1c. Concept document (main context)

After the user chooses or combines pitches, write `docs/00-concept.md`:

```markdown
# <Title>: Concept
Status: in review (G1)

## Logline
## Player fantasy
## Genre, camera and orientation
## Core loop
## Design pillars (3)
## Audience and tone
## Platforms and typical session
## Touch controls
## Monetization
## Visual style (intent) and references
## Languages (source language of the dialogue, target languages)
## MVP scope
## Out of scope (what this game is not)
## Risks and mitigation
## Open questions for W2
```

Record every locked choice (genre, orientation, monetization) in DECISIONS.md. Ask for G1 approval.

## Done criteria

A developer who never heard of the game reads the concept and can explain in 30 seconds what the player does, why it is fun and how much content the MVP has.
