#!/usr/bin/env python3
"""
Generate device frame template PNGs for every supported platform.

Outputs (all standalone device images, not positioned on a canvas —
compose.py positions them dynamically based on its per-platform preset):

  assets/device_frame.png            iPhone (Dynamic Island)     — App Store
  assets/android_device_frame.png    Android phone (punch-hole)  — Play Store
  assets/android_tablet7_frame.png   7"  Android tablet          — Play Store
  assets/android_tablet10_frame.png  10" Android tablet          — Play Store

Run with no arguments to regenerate all four, or pass one of:
  --platform ios | android | android-tablet-7 | android-tablet-10

The geometry constants here MUST stay in sync with the matching preset
in compose.py (see PRESETS).
"""

import argparse
import os
from PIL import Image, ImageDraw, ImageChops

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# ── Frame specs ─────────────────────────────────────────────────────
# Each spec is a standalone device drawing recipe. compose.py reads the
# same DEVICE_W / BEZEL / SCREEN_CORNER_R values from its PRESETS table.
SPECS = {
    "ios": dict(
        out="device_frame.png",
        DEVICE_W=1030, DEVICE_H=2800,
        DEVICE_CORNER_R=77, BEZEL=15, SCREEN_CORNER_R=62,
        notch="dynamic-island", DI_W=130, DI_H=38, DI_TOP=14,
        buttons="ios",
    ),
    "android": dict(
        out="android_device_frame.png",
        DEVICE_W=860, DEVICE_H=2000,
        DEVICE_CORNER_R=64, BEZEL=12, SCREEN_CORNER_R=52,
        notch="punch-hole", HOLE_D=34, HOLE_TOP=18,
        buttons="android",
    ),
    "android-tablet-7": dict(
        out="android_tablet7_frame.png",
        DEVICE_W=920, DEVICE_H=2000,
        DEVICE_CORNER_R=52, BEZEL=26, SCREEN_CORNER_R=28,
        notch="bezel-camera", CAM_D=16,
        buttons="android",
    ),
    "android-tablet-10": dict(
        out="android_tablet10_frame.png",
        DEVICE_W=1230, DEVICE_H=2700,
        DEVICE_CORNER_R=68, BEZEL=34, SCREEN_CORNER_R=38,
        notch="bezel-camera", CAM_D=20,
        buttons="android",
    ),
}


def generate(platform):
    s = SPECS[platform]
    W, H = s["DEVICE_W"], s["DEVICE_H"]
    bezel = s["BEZEL"]
    screen_w = W - 2 * bezel
    screen_h = H - 2 * bezel

    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)

    # ── Device body (dark grey outer, darker inner) ─────────────────
    fd.rounded_rectangle(
        [0, 0, W - 1, H - 1],
        radius=s["DEVICE_CORNER_R"],
        fill=(30, 30, 30, 255),
    )
    fd.rounded_rectangle(
        [1, 1, W - 2, H - 2],
        radius=s["DEVICE_CORNER_R"] - 1,
        fill=(20, 20, 20, 255),
    )

    # ── Screen cutout (transparent) ─────────────────────────────────
    cutout = Image.new("L", (W, H), 255)
    ImageDraw.Draw(cutout).rounded_rectangle(
        [bezel, bezel, bezel + screen_w, bezel + screen_h],
        radius=s["SCREEN_CORNER_R"],
        fill=0,
    )
    frame.putalpha(ImageChops.multiply(frame.getchannel("A"), cutout))
    fd = ImageDraw.Draw(frame)

    # ── Camera treatment ────────────────────────────────────────────
    if s["notch"] == "dynamic-island":
        di_w, di_h = s["DI_W"], s["DI_H"]
        di_x = (W - di_w) // 2
        di_y = bezel + s["DI_TOP"]
        fd.rounded_rectangle(
            [di_x, di_y, di_x + di_w, di_y + di_h],
            radius=di_h // 2,
            fill=(0, 0, 0, 255),
        )
    elif s["notch"] == "punch-hole":
        d = s["HOLE_D"]
        cx = W // 2
        cy = bezel + s["HOLE_TOP"] + d // 2
        fd.ellipse([cx - d // 2, cy - d // 2, cx + d // 2, cy + d // 2],
                   fill=(0, 0, 0, 255))
        # subtle lens ring
        r = d // 4
        fd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(12, 12, 14, 255))
    elif s["notch"] == "bezel-camera":
        # camera dot lives in the top bezel (portrait orientation)
        d = s["CAM_D"]
        cx = W // 2
        cy = bezel // 2
        fd.ellipse([cx - d // 2, cy - d // 2, cx + d // 2, cy + d // 2],
                   fill=(10, 10, 12, 255))

    # ── Side buttons ────────────────────────────────────────────────
    btn = (25, 25, 25, 255)
    if s["buttons"] == "ios":
        fd.rounded_rectangle([W, 340, W + 4, 460], radius=2, fill=btn)   # power (R)
        fd.rounded_rectangle([-4, 280, 0, 360], radius=2, fill=btn)      # vol up (L)
        fd.rounded_rectangle([-4, 380, 0, 460], radius=2, fill=btn)      # vol down (L)
        fd.rounded_rectangle([-4, 180, 0, 220], radius=2, fill=btn)      # silent (L)
    else:  # android — power + volume rocker on the right
        fd.rounded_rectangle([W - 4, 300, W, 400], radius=2, fill=btn)   # power
        fd.rounded_rectangle([W - 4, 440, W, 620], radius=2, fill=btn)   # volume

    os.makedirs(ASSETS, exist_ok=True)
    out = os.path.join(ASSETS, s["out"])
    frame.save(out, "PNG")
    print(f"✓ {out} ({W}×{H})")
    print(f"  BEZEL={bezel}, SCREEN_W={screen_w}, SCREEN_H={screen_h}, "
          f"SCREEN_CORNER_R={s['SCREEN_CORNER_R']}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate device frame templates")
    p.add_argument("--platform", choices=list(SPECS) + ["all"], default="all")
    args = p.parse_args()
    targets = list(SPECS) if args.platform == "all" else [args.platform]
    for t in targets:
        generate(t)
