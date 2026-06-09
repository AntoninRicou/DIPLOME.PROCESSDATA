#!/usr/bin/env python3
"""
Build an aspect-preserving texture atlas for the Three.js viewer.

Every image is fit (letterboxed) into a TILE_SIZE x TILE_SIZE cell so its
original aspect ratio is preserved. The JSON records two UV rects per image:

  - cell UV  (u, v, uSize, vSize)        : the full cell, including padding
  - content UV (imgU, imgV, imgUSize, imgVSize) : the actual image rect

On the Three.js side, use `imgU/imgV/imgUSize/imgVSize` for the texture
coordinates and `aspect` (w/h) to size the quad — that gives a crisp image
with no padding bleed and the original proportions.

Inputs:
  ../DIPLOME.Feedback/datas/images/<path>
  ../DIPLOME.Feedback/static/data/mapping.json

Outputs (./cache/):
  atlas.jpg     packed texture
  atlas.json    {cols, rows, tile, width, height, images: {id: {...}}}
"""

import argparse
import json
import math
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent / "DIPLOME.Feedback"
IMAGES_DIR = PROJECT_DIR / "datas" / "images"
MAPPING_PATH = PROJECT_DIR / "static" / "data" / "mapping.json"
CACHE_DIR = HERE / "cache"

BG_COLOR = (14, 14, 16)  # matches Three.js scene background


def fit_into_cell(img: Image.Image, tile: int) -> tuple[Image.Image, int, int, int, int]:
    """Resize `img` to fit inside a `tile`x`tile` cell, preserving aspect.

    Returns the resized image plus (offset_x, offset_y, fit_w, fit_h) describing
    its placement inside the cell (top-left origin).
    """
    w, h = img.size
    scale = min(tile / w, tile / h)
    fit_w = max(1, round(w * scale))
    fit_h = max(1, round(h * scale))
    resized = img.resize((fit_w, fit_h), Image.LANCZOS)
    offset_x = (tile - fit_w) // 2
    offset_y = (tile - fit_h) // 2
    return resized, offset_x, offset_y, fit_w, fit_h


def build_atlas(tile: int, quality: int, fmt: str) -> None:
    print(f"Loading mapping from {MAPPING_PATH} …")
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    print(f"  → {len(mapping)} entries")

    n = len(mapping)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    atlas_w = cols * tile
    atlas_h = rows * tile
    print(f"Atlas grid: {cols}×{rows} cells of {tile}px = {atlas_w}×{atlas_h} px")

    if fmt == "png":
        atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    else:
        atlas = Image.new("RGB", (atlas_w, atlas_h), BG_COLOR)

    atlas_meta: dict[str, dict] = {}
    errors = 0

    for i, entry in enumerate(mapping):
        img_path = IMAGES_DIR / entry["path"]
        col = i % cols
        row = i // cols
        cell_x = col * tile
        cell_y = row * tile

        try:
            with Image.open(img_path) as src:
                mode = "RGBA" if fmt == "png" else "RGB"
                img = src.convert(mode)
                orig_w, orig_h = img.size
                fit_img, off_x, off_y, fit_w, fit_h = fit_into_cell(img, tile)
        except Exception as exc:
            print(f"  Error {entry['id']}: {exc}")
            errors += 1
            continue

        paste_pos = (cell_x + off_x, cell_y + off_y)
        if fmt == "png":
            atlas.paste(fit_img, paste_pos, fit_img)
        else:
            atlas.paste(fit_img, paste_pos)

        # UVs are top-left origin (matches row/col indexing).
        u = col / cols
        v = row / rows
        u_size = 1.0 / cols
        v_size = 1.0 / rows

        # Content UVs in absolute atlas coordinates.
        img_u = (cell_x + off_x) / atlas_w
        img_v = (cell_y + off_y) / atlas_h
        img_u_size = fit_w / atlas_w
        img_v_size = fit_h / atlas_h

        atlas_meta[entry["id"]] = {
            "col": col,
            "row": row,
            "u": u,
            "v": v,
            "uSize": u_size,
            "vSize": v_size,
            "imgU": img_u,
            "imgV": img_v,
            "imgUSize": img_u_size,
            "imgVSize": img_v_size,
            "width": orig_w,
            "height": orig_h,
            "aspect": orig_w / orig_h,
            "fitWidth": fit_w,
            "fitHeight": fit_h,
        }

        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{n} …")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if fmt == "png":
        atlas_img_path = CACHE_DIR / "atlas.png"
        atlas.save(atlas_img_path, optimize=True)
    else:
        atlas_img_path = CACHE_DIR / "atlas.jpg"
        atlas.save(atlas_img_path, quality=quality, optimize=True)
    print(f"Saved atlas image → {atlas_img_path} ({atlas_w}×{atlas_h})")

    atlas_json_path = CACHE_DIR / "atlas.json"
    meta_out = {
        "cols": cols,
        "rows": rows,
        "tile": tile,
        "width": atlas_w,
        "height": atlas_h,
        "format": fmt,
        "images": atlas_meta,
    }
    with open(atlas_json_path, "w", encoding="utf-8") as f:
        json.dump(meta_out, f)
    print(f"Saved atlas JSON  → {atlas_json_path} ({len(atlas_meta)} entries)")

    if errors:
        print(f"⚠ {errors} images failed")
    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build aspect-preserving atlas.")
    parser.add_argument("--tile", type=int, default=96,
                        help="px per cell (default: 96; keeps atlas under 8192px for ~5k images)")
    parser.add_argument("--quality", type=int, default=90, help="JPG quality (default: 90)")
    parser.add_argument("--format", choices=("jpg", "png"), default="jpg",
                        help="output format; png keeps transparency in padding (default: jpg)")
    args = parser.parse_args()

    build_atlas(tile=args.tile, quality=args.quality, fmt=args.format)


if __name__ == "__main__":
    main()
