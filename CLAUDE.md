# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Code skill (`aso-store-screenshots`) that guides users through creating high-converting **App Store and Google Play** screenshots, plus the Play Store feature graphic. It is invoked via the `/aso-store-screenshots` slash command from within a user's app project.

## Architecture

Five files + four assets make up the skill:

- **SKILL.md** — The skill prompt. Defines a multi-phase workflow: Target Store Selection → Benefit Discovery → Screenshot Pairing → Generation (per platform) → Feature Graphic (Play only). Uses Claude Code's memory system to persist state across conversations so users can resume mid-workflow. Generation first creates a deterministic scaffold via compose.py, then sends it to Nano Banana Pro for AI enhancement.
- **compose.py** — A standalone Python compositing script (Pillow-based) that deterministically renders store screenshots. Takes `--platform` (`appstore` 1290×2796 default, `playstore` 1080×1920, `playstore-tablet-7` 1200×1920, `playstore-tablet-10` 1600×2560), a background hex colour, action verb, benefit descriptor, and simulator/emulator screenshot path, then produces a pixel-perfect PNG with headline text, the platform's device frame template, and the screenshot composited inside. The verb text auto-sizes to fit the canvas width. Output is flattened to RGB (Play rejects alpha). Play targets automatically use Google's photorealistic device art (`assets/pixel_10_pro/`, `assets/pixel_tablet/` — emulator-skin format: back.webp body + mask.webp punch-hole/corner overlay + layout geometry) when present; setup.sh copies it from Android Studio, and `--frame flat` forces the drawn template.
- **generate_frame.py** — Generates all device frame template PNGs into `assets/` (`--platform ios|android|android-tablet-7|android-tablet-10|all`). Run once to create or update the templates. Frame geometry constants must stay in sync with `PRESETS` in compose.py (and the phone constants in generate_feature_graphic.py).
- **generate_feature_graphic.py** — Deterministic 1024×500 Play Store feature graphic scaffold: headline block left, Android phone with screenshot bleeding off the bottom-right. Same font/colour language as compose.py.
- **showcase.py** — Generates a showcase image showing up to 3 final screenshots side-by-side with an optional GitHub link at the bottom. Platform-agnostic; run per store.
- **assets/device_frame.png** — iPhone frame (Dynamic Island). **assets/android_device_frame.png** — Android phone frame (punch-hole). **assets/android_tablet7_frame.png / android_tablet10_frame.png** — Android tablet frames. Using templates instead of drawing at compose time ensures pixel-perfect consistency across all generated screenshots.

## Running compose.py

```bash
# Requires: pip install Pillow
# Preferred font: SF Pro Display Black at /Library/Fonts/SF-Pro-Display-Black.otf
# (falls back to Inter Black / Arial Bold / DejaVu Sans Bold if missing)

python3 compose.py \
  --platform playstore \
  --bg "#E31837" \
  --verb "TRACK" \
  --desc "TRADING CARD PRICES" \
  --screenshot path/to/emulator.png \
  --output output.png
```

## Key Design Decisions

- **Two-stage generation**: compose.py creates a deterministic scaffold first (text + frame + screenshot), then Nano Banana Pro enhances it. This avoids the inconsistencies of generating from scratch.
- **compose.py outputs exact store dimensions** per platform — the AI post-processing crop only compensates for Nano Banana's preset aspect ratios (9:16 for phones, 3:4 for tablets, 21:9 for the feature graphic).
- **Device frames are template images** in `assets/` — not drawn at compose time. Regenerate with `python3 generate_frame.py` if a frame design needs updating; keep constants in sync with compose.py `PRESETS`.
- **Verb text auto-sizes** per platform preset to fit multi-word verbs within the canvas width.
- **SKILL.md always generates 3 versions in parallel** for each benefit so the user can pick the best one.
- **The crop/resize step in SKILL.md is mandatory** after every `generate_image` or `edit_image` call — raw Nano Banana output is never the correct dimensions for either store.
- **Play compliance is deterministic**: every save path flattens to RGB (no alpha) and the target sizes keep files far under Play's 8 MB cap.
- **Benefits/pairings/brand colour are store-agnostic** — discovered once, reused for every target platform. Only frames, prompts wording, and dimensions differ.
- **Memory is central to the workflow** — target stores, benefits, screenshot assessments, pairings, brand colour, and per-platform generation state are all persisted so users can resume across conversations.
