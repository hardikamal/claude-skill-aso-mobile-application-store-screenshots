# ASO Mobile Store Screenshots

A Claude Code skill that generates high-converting **App Store AND Google Play** screenshots for your mobile app. It analyzes your codebase, identifies core benefits, and creates professional screenshot images using AI — including the Play Store feature graphic.

> Forked from [adamlyttleapps/claude-skill-aso-appstore-screenshots](https://github.com/adamlyttleapps/claude-skill-aso-appstore-screenshots) (MIT), which is App Store-only. This fork adds full Google Play support.

## What It Does

1. **Target Store Selection** — App Store, Google Play, or both; benefits and branding are shared across stores
2. **Benefit Discovery** — Analyzes your app's codebase to identify the 3-5 core benefits that drive downloads
3. **Screenshot Pairing** — Reviews your simulator/emulator screenshots, rates them, and pairs each with the best benefit
4. **Generation** — Creates polished store screenshots using a two-stage process: deterministic scaffolding (compose.py) + AI enhancement (Nano Banana Pro via Gemini MCP)
5. **Feature Graphic** — Generates the required 1024×500 Play Store banner from your hero benefit
6. **Showcase** — Generates a preview image with all screenshots side-by-side

## Supported Output Targets

| Target | Size | Store |
|--------|------|-------|
| iPhone 6.7" (default; 6.5"/6.9" via resize) | 1290×2796 | App Store |
| Android phone | 1080×1920 | Google Play |
| 7" Android tablet | 1200×1920 | Google Play |
| 10" Android tablet | 1600×2560 | Google Play |
| Feature graphic | 1024×500 | Google Play |

Play outputs are compliance-checked: flattened RGB (no alpha channel), under 8 MB, exact dimensions.

## Installation

### 1. Add the skill to Claude Code

```
git clone https://github.com/hardikamal/claude-skill-aso-mobile-application-store-screenshots.git ~/.claude/skills/aso-store-screenshots
```

### 2. Install Python dependencies

```
pip install Pillow
```

### 3. Font requirement

The skill uses **SF Pro Display Black** for headline text. On macOS, install it from [Apple's developer fonts](https://developer.apple.com/fonts/). The expected path is:

```
/Library/Fonts/SF-Pro-Display-Black.otf
```

(Without it, the scripts fall back to Inter Black / Arial Bold / DejaVu Sans Bold.)

### 4. Set up Gemini MCP (for AI enhancement)

The generation phase requires [@houtini/gemini-mcp](https://www.npmjs.com/package/@houtini/gemini-mcp) to be configured as an MCP server in Claude Code:

```
npm install -g @houtini/gemini-mcp
```

Then add it to your Claude Code MCP config (`~/.claude/settings.json` or project `.mcp.json`).

## Usage

From within your app's project directory, run:

```
/aso-store-screenshots
```

The skill will guide you through each phase interactively. Progress is saved to Claude Code's memory system, so you can resume across conversations. Targeting both stores runs the generation flow once per store, reusing the same benefits, pairings, and brand colour.

## How It Works

### Scaffold → Enhance Pipeline

Rather than generating screenshots from scratch (which produces inconsistent results), the skill uses a two-stage approach:

1. **compose.py** creates a deterministic scaffold with exact text positioning, the platform's device frame (iPhone with Dynamic Island, punch-hole Android phone, or slim-bezel Android tablet), and your screenshot composited inside
2. **Nano Banana Pro** (via Gemini MCP) enhances the scaffold — adding a photorealistic device frame, breakout elements, and visual polish

This ensures consistent layout across all screenshots while letting AI handle the creative enhancement.

### Output

Screenshots are saved to a `screenshots/` directory in your project, one folder per platform:

```
screenshots/
  appstore/
    01-benefit-slug/            ← working versions (scaffold, v1–v3, resized)
    final/                      ← approved, App Store Connect-ready
  playstore/
    01-benefit-slug/
    final/                      ← approved, Play Console-ready
    feature-graphic/            ← 1024×500 banner working versions
    final-feature-graphic.png
  playstore-tablet-7/           ← optional
  playstore-tablet-10/          ← optional
  showcase.png
```

## Files

| File | Purpose |
| ---- | ------- |
| `SKILL.md` | The skill prompt — defines the multi-phase workflow |
| `compose.py` | Deterministic scaffold generator (Pillow-based), `--platform` presets for all targets |
| `generate_frame.py` | Generates all device frame templates (iPhone, Android phone, 7"/10" tablets) |
| `generate_feature_graphic.py` | Deterministic 1024×500 Play Store feature graphic scaffold |
| `showcase.py` | Generates the side-by-side showcase image |
| `assets/device_frame.png` | iPhone frame template |
| `assets/android_device_frame.png` | Android phone frame template |
| `assets/android_tablet7_frame.png` | 7" Android tablet frame template |
| `assets/android_tablet10_frame.png` | 10" Android tablet frame template |

## Credits

- Original App Store skill by [Adam Lyttle](https://github.com/adamlyttleapps) — [claude-skill-aso-appstore-screenshots](https://github.com/adamlyttleapps/claude-skill-aso-appstore-screenshots)
- Play Store support added in this fork

## License

MIT
