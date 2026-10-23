---
name: gf-audio
description: "Game audio with Runway: sound direction (references, instrument palette, theme per character/location, SFX list) in pre-production, and production of looping music, stings, SFX, ambiences and short voices, with normalization and import into Godot. Use in W2 (direction), in production (W5 onward), or when the user asks for music, a sound effect, a soundtrack, a voice or mix adjustments (\"make the boss theme\", \"make a sword sound\")."
---

# gf-audio: sound direction and production

Handles sound from direction to delivery. In pre-production it defines references, instrument palette, themes and the SFX list. In production it generates looping music, stingers, sound effects, ambiences and short voices with Runway, normalizes them and imports them into Godot. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Writing the audio direction
- Making music, a sound effect, ambience or a voice line
- Adjusting the mix or fixing loops

Produces: `docs/07-audio-direction.md`, `audio/`, `game/assets/audio/`.

Works with: gf-runway, gf-godot-core.

---

Runway tools: `generate_music` (`lyria-3-clip` loops and stings, `lyria-3-pro` full track), `generate_sound_effect` (up to 30 s, `loop: true` for ambience), `generate_speech` (voice). Read `gf-runway` for logging and cost.

## W2: direction (`docs/07-audio-direction.md`)

```markdown
# Audio direction
## Identity (pure chiptune, hybrid chip + orchestra, period acoustic...)
## References (games and soundtracks, what to take from each)
## Instrument palette
## Themes
   theme | where it plays | mood | tempo (BPM) | key | instruments | loop?
## Music map per chapter/location/state (exploration, combat, boss, victory, defeat)
## SFX list
   sfx_id | game event | description | duration | variations
## Voice (grunts, exclamations, spoken lines or not)
## Mix rules
   music -14 LUFS, SFX -12 to -16 LUFS, buses: Master, Music, SFX, UI, Voice (+ Ambience)
```

Generate **one demo theme** (`lyria-3-clip`) of the protagonist or the menu to validate the identity at G2. Save in `audio/music/demo/`.

## Production (after G3)

Music prompts: genre and mood first, instruments and BPM after, structure ("seamless loop, no intro, no fade out" for loops), "instrumental, no vocals". SFX prompts: source, action, space ("short dry pixel-game sword slash, no reverb"). For a pixel art game, ask for a timbre that matches the identity (chip, 16-bit, or acoustic).

**Moderation:** SFX prompts that mention a child ("boy", "kid") can be blocked by moderation (CHILDREN). Describe the sound by source and action instead ("light footstep on dry grass", "small grunt").

Mandatory post-processing with ffmpeg:

```bash
# loudness
ffmpeg -i in.mp3 -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 44100 out.ogg
# SFX: trim silence
ffmpeg -i in.mp3 -af silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,loudnorm=I=-16:TP=-1.5 out.ogg
```

- If your ffmpeg has no `libvorbis` (common with Homebrew builds), use the native encoder: `-c:a vorbis -strict -2`; or install an ffmpeg with libvorbis.
- Music and ambience in `.ogg` with loop enabled; SFX in `.ogg` (short ones may be `.wav`).
- **Godot imports audio with `loop = false`.** Looping music will play once and stop unless the loop flag is turned on at import, or the audio manager sets it in code. The manager turns the loop on for every music track except stingers (`mus_stinger_*`). Check this on a real run.
- Loop: check the seam by playing 3 laps; if it clicks, regenerate or cut at a zero crossing.
- Variations: repetitive SFX (steps, hits) get 3 variations to alternate in game.
- Ambience goes on its own bus, about -12 dB below music: an Ambience bus left at 0 dB is as loud as the music.
- Destination: `audio/<music|sfx|voice>/<id>.ogg` and the final copy in `game/assets/audio/` with the same name.

## Integration

The bus layout `default_bus_layout.tres` is created by gf-godot-core from the mix rules of this skill. gf-audio delivers the table `game/assets/audio/audio_map.json` (`event -> file, bus, volume_db, variations`) that the core AudioManager reads.

## Done criteria

Every event listed in the GDD and every location in the content plan has a mapped sound; loops without clicks; loudness normalized; music loops confirmed in the running game (emulator media volume can be low: raise it before judging).
