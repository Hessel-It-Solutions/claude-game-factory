---
name: gf-release
description: "Mobile game release: store listing (Google Play and App Store) with copy and ASO in the game's languages, icon, feature graphic, framed screenshots, trailer assembled from game captures, static illustrations and music (no AI-generated video), age rating, privacy policy and submission checklist. Use in WF of /game-factory, or when the user asks for store copy, screenshots, a trailer, the final icon or help publishing (\"write the store listing\", \"make the trailer\")."
---

# gf-release: store and marketing

Prepares the launch: store listings for Google Play and the App Store with copy and ASO in every language, icon, feature graphic, framed screenshots, a trailer cut from real gameplay captures, age rating, privacy policy and a submission checklist. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Writing store copy and ASO
- Making the icon, screenshots or trailer
- Preparing the submission to the stores

Produces: `store/` and `art/marketing/`.

Works with: gf-mobile, gf-runway, gf-audio.

---

Owner of `store/` and `art/marketing/`. Read `gf-runway`. Publishing to the stores is a user action (account, payment, terms acceptance); the skill prepares everything and delivers the checklist.

## Store listing (`store/<locale>/listing.md`, one folder per language of the concept, for example `en-US`)

- Title (≤ 30), subtitle/short description (≤ 80), long description (≤ 4000) with a hook in the first line, concept pillars, feature list.
- Keywords (App Store ≤ 100 characters) from the gf-concept market research.
- Category, age rating (IARC questionnaire on Play, Age Rating on Apple), privacy policy (a simple page saying what the game collects; with ads/analytics, list the SDKs).
- Plain copy: no empty hype ("an unforgettable epic"); say what the player does. Write in the language of each listing.

## Store art (`art/marketing/`)

| Asset | Size | Source |
|---|---|---|
| Icon | 512x512 (Play), 1024x1024 (Apple), adaptive 432x432 fg/bg | `generate_image` with the protagonist base and `@style`, big face/silhouette; pixelize at 64 or 128 logical and enlarge with nearest |
| Feature graphic | 1024x500 | key art of the first chapter + logo |
| Logo | not vector; pixel art in 2 sizes | `gpt-image-2` for the lettering, then pixelize and retouch |
| Screenshots | per device required by the store | real gf-qa captures, enlarged with nearest, frame and short caption in the game font |

Screenshots show the real game. Generated art that does not exist in the game does not go into a screenshot.

## Trailer (`art/marketing/trailer/`)

1. 30 s script: hook (3 s), main mechanic, world, boss/big moment, logo + call to action.
2. Only captures of the game running (gf-qa recording or `ffmpeg` from headless frames) and the game's static illustrations. No AI-generated video.
3. Music: the game theme (gf-audio) or `generate_music` with a final stinger.
4. Assemble with `ffmpeg` (cuts, music, text). Export 16:9 and 9:16.

## Submission checklist (`store/checklist.md`)

Accounts created by the user, AAB/IPA from gf-mobile with the right version, signing, listing filled in every language, age rating, privacy policy published, data safety (Play) and App Privacy (Apple), internal testing/TestFlight before launch, price or free, countries. The release build must be verified on a clean install (`pm clear`) and its installed size and time checked on the device (see gf-mobile).
