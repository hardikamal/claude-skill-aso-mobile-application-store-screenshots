#!/usr/bin/env python3
"""
Google Play Feature Graphic Generator (1024×500)

Deterministic scaffold for the required Play Store listing banner:
brand-colour background, headline block on the left, Android phone
frame with the app screenshot bleeding off the bottom-right.

Layout mirrors compose.py's design language so the feature graphic
looks like part of the same set. Optionally enhanced afterwards via
the same Nano Banana edit_image flow as the screenshots.
"""

import argparse
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))

CANVAS_W = 1024
CANVAS_H = 500

# Text block occupies the left ~58%; phone occupies the right.
TEXT_LEFT = 64
TEXT_MAX_W = 520
VERB_SIZE_MAX = 110
VERB_SIZE_MIN = 64
DESC_SIZE = 46
VERB_DESC_GAP = 14
DESC_LINE_GAP = 10

# Phone placement (uses the Play Store phone frame, scaled down)
PHONE_W = 300
PHONE_X = CANVAS_W - PHONE_W - 70
PHONE_Y = 70          # top of phone; bottom bleeds off the canvas

FONT_CANDIDATES = [
    "/Library/Fonts/SF-Pro-Display-Black.otf",
    os.path.expanduser("~/Library/Fonts/SF-Pro-Display-Black.otf"),
    os.path.expanduser("~/Library/Fonts/Inter-Black.ttf"),
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

# Must match generate_frame.py SPECS["android"]
FRAME_FILE = "android_device_frame.png"
FRAME_DEVICE_W = 860
FRAME_BEZEL = 12
FRAME_SCREEN_CORNER_R = 52


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit(
        "✗ No usable headline font found. Install SF Pro Display Black "
        "(https://developer.apple.com/fonts/) at /Library/Fonts/SF-Pro-Display-Black.otf"
    )


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i: i + 2], 16) for i in (0, 2, 4))


def word_wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_font(text, max_w, size_max, size_min):
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for size in range(size_max, size_min - 1, -2):
        font = load_font(size)
        bbox = dummy.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_w:
            return font
    return load_font(size_min)


def measure_block(verb, desc, verb_font, desc_font):
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    h = 0
    bbox = dummy.textbbox((0, 0), verb, font=verb_font)
    h += (bbox[3] - bbox[1]) + VERB_DESC_GAP
    for line in word_wrap(dummy, desc, desc_font, TEXT_MAX_W):
        bbox = dummy.textbbox((0, 0), line, font=desc_font)
        h += (bbox[3] - bbox[1]) + DESC_LINE_GAP
    return h - DESC_LINE_GAP


def generate(bg_hex, verb, desc, screenshot_path, output_path):
    bg = hex_to_rgb(bg_hex)
    verb, desc = verb.upper(), desc.upper()

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (*bg, 255))
    draw = ImageDraw.Draw(canvas)

    # ── Headline block, vertically centred on the left ──────────────
    verb_font = fit_font(verb, TEXT_MAX_W, VERB_SIZE_MAX, VERB_SIZE_MIN)
    desc_font = load_font(DESC_SIZE)

    block_h = measure_block(verb, desc, verb_font, desc_font)
    y = (CANVAS_H - block_h) // 2

    bbox = draw.textbbox((0, 0), verb, font=verb_font)
    draw.text((TEXT_LEFT, y - bbox[1]), verb, fill="white", font=verb_font)
    y += (bbox[3] - bbox[1]) + VERB_DESC_GAP

    for line in word_wrap(draw, desc, desc_font, TEXT_MAX_W):
        bbox = draw.textbbox((0, 0), line, font=desc_font)
        draw.text((TEXT_LEFT, y - bbox[1]), line, fill="white", font=desc_font)
        y += (bbox[3] - bbox[1]) + DESC_LINE_GAP

    # ── Phone with screenshot, bleeding off bottom-right ────────────
    frame_path = os.path.join(BASE, "assets", FRAME_FILE)
    if not os.path.exists(frame_path):
        raise SystemExit(
            f"✗ Missing frame template {frame_path} — run: python3 generate_frame.py"
        )
    frame = Image.open(frame_path).convert("RGBA")
    scale = PHONE_W / FRAME_DEVICE_W
    frame = frame.resize(
        (PHONE_W, int(frame.height * scale)), Image.LANCZOS
    )
    bezel = max(1, round(FRAME_BEZEL * scale))
    screen_w = PHONE_W - 2 * bezel
    corner_r = max(2, round(FRAME_SCREEN_CORNER_R * scale))

    shot = Image.open(screenshot_path).convert("RGBA")
    s = screen_w / shot.width
    shot = shot.resize((screen_w, int(shot.height * s)), Image.LANCZOS)

    screen_x = PHONE_X + bezel
    screen_y = PHONE_Y + bezel
    screen_h = CANVAS_H - screen_y + 200      # bleeds off the bottom

    scr_mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(scr_mask).rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h],
        radius=corner_r, fill=255,
    )
    scr_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(scr_layer).rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h],
        radius=corner_r, fill=(0, 0, 0, 255),
    )
    scr_layer.paste(shot, (screen_x, screen_y))
    scr_layer.putalpha(scr_mask)
    canvas = Image.alpha_composite(canvas, scr_layer)

    frame_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    frame_layer.paste(frame, (PHONE_X, PHONE_Y))
    canvas = Image.alpha_composite(canvas, frame_layer)

    # ── Save (flattened RGB — Play Store rejects alpha) ─────────────
    canvas.convert("RGB").save(output_path, "PNG")
    print(f"✓ {output_path} ({CANVAS_W}×{CANVAS_H}, feature graphic)")


def main():
    p = argparse.ArgumentParser(description="Generate Play Store feature graphic")
    p.add_argument("--bg", required=True, help="Background hex colour (#E31837)")
    p.add_argument("--verb", required=True, help="Action verb / app name (TRACK)")
    p.add_argument("--desc", required=True, help="Benefit descriptor (TRADING CARD PRICES)")
    p.add_argument("--screenshot", required=True, help="Emulator screenshot path")
    p.add_argument("--output", required=True, help="Output file path")
    args = p.parse_args()

    generate(args.bg, args.verb, args.desc, args.screenshot, args.output)


if __name__ == "__main__":
    main()
