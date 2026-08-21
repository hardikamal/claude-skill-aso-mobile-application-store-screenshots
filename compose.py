#!/usr/bin/env python3
"""
Store Screenshot Composer — App Store + Google Play
Composites headline text, device frame template, and app screenshot
into a pixel-perfect store-ready image.

Platforms (--platform):
  appstore             1290×2796  iPhone 6.7"          (default)
  playstore            1080×1920  Android phone, 9:16
  playstore-tablet-7   1200×1920  7"  Android tablet
  playstore-tablet-10  1600×2560  10" Android tablet

The device frame is a pre-rendered template (see generate_frame.py);
the frame geometry constants in PRESETS must match SPECS there.
"""

import argparse
import os
import re
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))

# ── Font resolution ─────────────────────────────────────────────────
# SF Pro Display Black is the intended face (macOS). The fallbacks keep
# the script running on machines without it — same layout, lesser font.
FONT_CANDIDATES = [
    "/Library/Fonts/SF-Pro-Display-Black.otf",
    os.path.expanduser("~/Library/Fonts/SF-Pro-Display-Black.otf"),
    os.path.expanduser("~/Library/Fonts/Inter-Black.ttf"),
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit(
        "✗ No usable headline font found. Install SF Pro Display Black "
        "(https://developer.apple.com/fonts/) at /Library/Fonts/SF-Pro-Display-Black.otf"
    )


# ── Platform presets ────────────────────────────────────────────────
# Frame constants (DEVICE_W, BEZEL, SCREEN_CORNER_R) must match the
# corresponding entry in generate_frame.py SPECS.
PRESETS = {
    "appstore": dict(
        CANVAS_W=1290, CANVAS_H=2796,
        FRAME="device_frame.png",
        DEVICE_W=1030, BEZEL=15, SCREEN_CORNER_R=62,
        DEVICE_Y=720, TEXT_TOP=200,
        VERB_SIZE_MAX=256, VERB_SIZE_MIN=150, DESC_SIZE=124,
        VERB_DESC_GAP=20, DESC_LINE_GAP=24,
    ),
    "playstore": dict(
        CANVAS_W=1080, CANVAS_H=1920,
        FRAME="android_device_frame.png",
        DEVICE_W=860, BEZEL=12, SCREEN_CORNER_R=52,
        DEVICE_Y=500, TEXT_TOP=130,
        VERB_SIZE_MAX=200, VERB_SIZE_MIN=118, DESC_SIZE=96,
        VERB_DESC_GAP=16, DESC_LINE_GAP=20,
    ),
    "playstore-tablet-7": dict(
        CANVAS_W=1200, CANVAS_H=1920,
        FRAME="android_tablet7_frame.png",
        DEVICE_W=920, BEZEL=26, SCREEN_CORNER_R=28,
        DEVICE_Y=520, TEXT_TOP=130,
        VERB_SIZE_MAX=210, VERB_SIZE_MIN=124, DESC_SIZE=100,
        VERB_DESC_GAP=16, DESC_LINE_GAP=20,
    ),
    "playstore-tablet-10": dict(
        CANVAS_W=1600, CANVAS_H=2560,
        FRAME="android_tablet10_frame.png",
        DEVICE_W=1230, BEZEL=34, SCREEN_CORNER_R=38,
        DEVICE_Y=700, TEXT_TOP=175,
        VERB_SIZE_MAX=280, VERB_SIZE_MIN=166, DESC_SIZE=132,
        VERB_DESC_GAP=20, DESC_LINE_GAP=24,
    ),
}


# ── Real device art (Google device frames, emulator-skin format) ────
# Copied locally from Android Studio by setup.sh (not redistributed in
# this repo). When the folder exists, scaffolds use the photorealistic
# frame — metallic edges, real buttons, camera — instead of the drawn one.
REAL_FRAMES = {
    "playstore": ("pixel_10_pro", 0),
    "playstore-tablet-7": ("pixel_tablet", 90),   # landscape art → portrait
    "playstore-tablet-10": ("pixel_tablet", 90),
}


def parse_layout(path):
    """Extract display rect + device offset from an emulator-skin layout file."""
    t = open(path).read()

    def block(name):
        m = re.search(rf"{name}\s*\{{(.*?)\n  \}}", t, re.S)
        return m.group(1) if m else ""

    def num(blk, key, default=0):
        m = re.search(rf"\b{key}\s+(\d+)", blk)
        return int(m.group(1)) if m else default

    disp = re.search(r"display\s*\{(.*?)\}", t, re.S).group(1)
    part2 = re.search(r"part2\s*\{(.*?)\}", t, re.S).group(1)
    return dict(
        screen_w=num(disp, "width"), screen_h=num(disp, "height"),
        corner_r=num(disp, "corner_radius", 0),
        dev_x=num(part2, "x"), dev_y=num(part2, "y"),
    )


def real_frame_dir(platform):
    entry = REAL_FRAMES.get(platform)
    if not entry:
        return None, 0
    d = os.path.join(BASE, "assets", entry[0])
    return (d, entry[1]) if os.path.exists(os.path.join(d, "back.webp")) else (None, 0)


def cover_crop(img, w, h):
    """Scale to fill w×h, crop centre-x / top-y (keeps app bar visible)."""
    scale = max(w / img.width, h / img.height)
    img = img.resize((max(1, round(img.width * scale)),
                      max(1, round(img.height * scale))), Image.LANCZOS)
    x = (img.width - w) // 2
    return img.crop((x, 0, x + w, h))


def paste_real_device(canvas, platform, shot, device_x, device_y, target_w):
    """Composite screenshot + Google device art onto canvas. Returns canvas."""
    d, rot = real_frame_dir(platform)
    back = Image.open(os.path.join(d, "back.webp")).convert("RGBA")
    mask = Image.open(os.path.join(d, "mask.webp")).convert("RGBA")
    lay = parse_layout(os.path.join(d, "layout"))
    sx, sy = lay["dev_x"], lay["dev_y"]
    sw, sh, cr = lay["screen_w"], lay["screen_h"], lay["corner_r"]

    if rot:  # rotate art (CCW) and transform the screen rect with it
        bw = back.width
        back = back.rotate(rot, expand=True)
        mask = mask.rotate(rot, expand=True)
        sx, sy, sw, sh = sy, bw - (sx + sw), sh, sw

    scale = target_w / back.width
    dims = lambda v: max(1, round(v * scale))
    back_s = back.resize((dims(back.width), dims(back.height)), Image.LANCZOS)
    mask_s = mask.resize((dims(mask.width), dims(mask.height)), Image.LANCZOS)
    sxs, sys_, sws, shs = round(sx * scale), round(sy * scale), dims(sw), dims(sh)

    # 1. screenshot, cover-cropped + rounded-rect clipped
    shot_s = cover_crop(shot, sws, shs)
    clip = Image.new("L", (sws, shs), 0)
    ImageDraw.Draw(clip).rounded_rectangle(
        [0, 0, sws - 1, shs - 1], radius=round(cr * scale), fill=255)
    shot_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shot_layer.paste(shot_s, (device_x + sxs, device_y + sys_), clip)
    canvas = Image.alpha_composite(canvas, shot_layer)

    # 2. mask overlay (punch-hole + corner anti-aliasing)
    mask_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    mask_layer.paste(mask_s, (device_x + sxs, device_y + sys_), mask_s)
    canvas = Image.alpha_composite(canvas, mask_layer)

    # 3. device body on top
    back_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    back_layer.paste(back_s, (device_x, device_y), back_s)
    return Image.alpha_composite(canvas, back_layer)


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
    """Return the largest font size where text fits within max_w."""
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for size in range(size_max, size_min - 1, -4):
        font = load_font(size)
        bbox = dummy.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_w:
            return font
    return load_font(size_min)


def draw_centered(draw, y, text, font, canvas_w, line_gap, max_w=None):
    lines = word_wrap(draw, text, font, max_w) if max_w else [text]
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        # anchor="mt" (middle-top) for pixel-perfect horizontal centering;
        # shift by bbox[1] so the glyph top lands on the intended y.
        draw.text((canvas_w // 2, y - bbox[1]), line, fill="white",
                  font=font, anchor="mt")
        y += h + line_gap
    return y


def compose(platform, bg_hex, verb, desc, screenshot_path, output_path,
            frame_mode="auto"):
    p = PRESETS[platform]
    bg = hex_to_rgb(bg_hex)
    canvas_w, canvas_h = p["CANVAS_W"], p["CANVAS_H"]
    screen_w = p["DEVICE_W"] - 2 * p["BEZEL"]
    max_text_w = int(canvas_w * 0.92)

    # ── 1. Canvas ───────────────────────────────────────────────────
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (*bg, 255))
    draw = ImageDraw.Draw(canvas)

    # ── 2. Headline text ────────────────────────────────────────────
    verb_font = fit_font(verb.upper(), max_text_w,
                         p["VERB_SIZE_MAX"], p["VERB_SIZE_MIN"])
    desc_font = load_font(p["DESC_SIZE"])

    y = p["TEXT_TOP"]
    y = draw_centered(draw, y, verb.upper(), verb_font,
                      canvas_w, p["DESC_LINE_GAP"])
    y += p["VERB_DESC_GAP"]
    draw_centered(draw, y, desc.upper(), desc_font,
                  canvas_w, p["DESC_LINE_GAP"], max_w=max_text_w)

    # ── 3. Device position ──────────────────────────────────────────
    device_x = (canvas_w - p["DEVICE_W"]) // 2
    device_y = p["DEVICE_Y"]
    screen_x = device_x + p["BEZEL"]
    screen_y = device_y + p["BEZEL"]

    # ── 4+5. Device + screenshot ────────────────────────────────────
    shot = Image.open(screenshot_path).convert("RGBA")
    use_real = frame_mode != "flat" and real_frame_dir(platform)[0]
    if frame_mode == "real" and not use_real:
        raise SystemExit(
            "✗ --frame real requested but no device art found in assets/ — "
            "run setup.sh to copy it from Android Studio, or use --frame flat"
        )

    if use_real:
        # Google device art: photorealistic body, metallic edges, buttons
        canvas = paste_real_device(canvas, platform, shot,
                                   device_x, device_y, p["DEVICE_W"])
    else:
        # Drawn template fallback
        # Scale to fill screen width
        scale = screen_w / shot.width
        shot = shot.resize((screen_w, int(shot.height * scale)), Image.LANCZOS)

        # Screen extends to bottom of canvas + overflow (device bleeds off)
        screen_h = canvas_h - screen_y + 500

        # Screen mask (rounded rect)
        scr_mask = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(scr_mask).rounded_rectangle(
            [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h],
            radius=p["SCREEN_CORNER_R"],
            fill=255,
        )

        # Black screen bg + screenshot on top
        scr_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(scr_layer).rounded_rectangle(
            [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h],
            radius=p["SCREEN_CORNER_R"],
            fill=(0, 0, 0, 255),
        )
        scr_layer.paste(shot, (screen_x, screen_y))
        scr_layer.putalpha(scr_mask)

        canvas = Image.alpha_composite(canvas, scr_layer)

        frame_path = os.path.join(BASE, "assets", p["FRAME"])
        if not os.path.exists(frame_path):
            raise SystemExit(
                f"✗ Missing frame template {frame_path} — run: python3 generate_frame.py"
            )
        frame_template = Image.open(frame_path).convert("RGBA")
        frame_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        frame_layer.paste(frame_template, (device_x, device_y))
        canvas = Image.alpha_composite(canvas, frame_layer)

    # ── 6. Save (flattened RGB — Play Store rejects alpha channels) ─
    canvas.convert("RGB").save(output_path, "PNG")
    print(f"✓ {output_path} ({canvas_w}×{canvas_h}, {platform})")


def main():
    p = argparse.ArgumentParser(description="Compose store screenshot")
    p.add_argument("--platform", choices=list(PRESETS), default="appstore",
                   help="Target store/format (default: appstore)")
    p.add_argument("--bg", required=True, help="Background hex colour (#E31837)")
    p.add_argument("--verb", required=True, help="Action verb (TRACK)")
    p.add_argument("--desc", required=True, help="Benefit descriptor (TRADING CARD PRICES)")
    p.add_argument("--screenshot", required=True, help="Simulator/emulator screenshot path")
    p.add_argument("--output", required=True, help="Output file path")
    p.add_argument("--frame", choices=["auto", "real", "flat"], default="auto",
                   help="auto: Google device art if present, else drawn template")
    args = p.parse_args()

    compose(args.platform, args.bg, args.verb, args.desc,
            args.screenshot, args.output, frame_mode=args.frame)


if __name__ == "__main__":
    main()
