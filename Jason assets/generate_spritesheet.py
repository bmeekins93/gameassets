#!/usr/bin/env python3
"""
generate_spritesheet.py

Usage:
  pip install pillow
  python generate_spritesheet.py --input jason --output spritesheet.png --json spritesheet.json --width 2048 --padding 2 --pot

Creates a sprite sheet (PNG) and a TexturePacker-style JSON atlas.
"""
import os
import sys
import json
import argparse
from PIL import Image

def next_power_of_two(n):
    p = 1
    while p < n:
        p <<= 1
    return p

def collect_images(input_dir):
    exts = ('.png', '.jpg', '.jpeg', '.webp')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(exts)]
    files.sort()  # sort by filename; change if you want different order
    images = []
    for fname in files:
        path = os.path.join(input_dir, fname)
        try:
            img = Image.open(path).convert("RGBA")
        except Exception as e:
            print(f"Skipping {fname}: cannot open ({e})")
            continue
        images.append((fname, img))
    return images

def pack_images(images, max_width, padding):
    x = padding
    y = padding
    row_height = 0
    positions = {}
    max_row_w = 0

    for fname, img in images:
        w, h = img.size
        if x + w + padding > max_width:
            # move to next row
            y += row_height + padding
            x = padding
            row_height = 0
        positions[fname] = (x, y)
        x += w + padding
        if x > max_row_w:
            max_row_w = x
        if h > row_height:
            row_height = h

    total_height = y + row_height + padding
    total_width = max(max_row_w, max((img.size[0] for _, img in images), default=0) + 2*padding)
    return positions, total_width, total_height

def create_sheet(images, positions, sheet_w, sheet_h, output_image_path, pad_bg=(0,0,0,0), pot=False):
    if pot:
        sheet_w = next_power_of_two(sheet_w)
        sheet_h = next_power_of_two(sheet_h)
    sheet = Image.new("RGBA", (sheet_w, sheet_h), pad_bg)
    for fname, img in images:
        x, y = positions[fname]
        sheet.paste(img, (x, y), mask=img)
    sheet.save(output_image_path)
    return sheet_w, sheet_h

def build_json(images, positions, sheet_w, sheet_h, image_filename):
    frames = {}
    for fname, img in images:
        name = os.path.splitext(fname)[0]
        x, y = positions[fname]
        w, h = img.size
        frames[name] = {
            "frame": {"x": x, "y": y, "w": w, "h": h},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h},
            "sourceSize": {"w": w, "h": h},
            "pivot": {"x": 0.5, "y": 0.5}
        }
    meta = {
        "app": "generate_spritesheet.py",
        "image": image_filename,
        "size": {"w": sheet_w, "h": sheet_h},
        "scale": "1"
    }
    return {"frames": frames, "meta": meta}

def main():
    parser = argparse.ArgumentParser(description="Pack images in a folder into a spritesheet and JSON atlas.")
    parser.add_argument("--input", "-i", default="jason", help="Input directory containing images")
    parser.add_argument("--output", "-o", default="spritesheet.png", help="Output spritesheet image path")
    parser.add_argument("--json", "-j", default="spritesheet.json", help="Output JSON atlas path")
    parser.add_argument("--width", "-w", type=int, default=2048, help="Max spritesheet width")
    parser.add_argument("--padding", "-p", type=int, default=2, help="Padding between sprites (px)")
    parser.add_argument("--pot", action="store_true", help="Round final atlas dimensions to next power of two")
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Input directory not found: {args.input}")
        sys.exit(1)

    images = collect_images(args.input)
    if not images:
        print("No images found in the input directory.")
        sys.exit(1)

    # adjust max width if single image larger than requested width
    max_img_w = max(img.size[0] for _, img in images)
    max_width = max(args.width, max_img_w + 2*args.padding)

    positions, sheet_w, sheet_h = pack_images(images, max_width, args.padding)

    final_w, final_h = create_sheet(images, positions, sheet_w, sheet_h, args.output, pot=args.pot)

    atlas = build_json(images, positions, final_w, final_h, os.path.basename(args.output))
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(atlas, f, indent=2)
    print(f"Created {args.output} ({final_w}x{final_h}) and {args.json} with {len(images)} frames.")

if __name__ == "__main__":
    main()