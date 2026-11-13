"""Generate PNG and Windows .ico icons from the Javo Agents brand mark.

Uses Pillow (PIL) to render high-contrast crisp icons at standard Windows and
web sizes (16, 24, 32, 48, 64, 128, 256) plus `icon.ico` and `tray-icon.png`.
If `cairosvg` is installed, renders directly from `windows-app-icon.svg`;
otherwise falls back to procedural Pillow vector drawing matching the SVG spec.
"""

from __future__ import annotations

import io
import math
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]
OUT_DIR = Path(__file__).resolve().parent / "dist"


def _render_with_pillow(size: int) -> "Image.Image":
    from PIL import Image, ImageDraw

    # Oversample 4x for crisp antialiasing
    scale = 4
    dim = size * scale
    img = Image.new("RGBA", (dim, dim), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = cy = dim / 2
    r_pad = dim * 0.04
    corner = dim * 0.20

    # Background rounded square (#0B1026)
    draw.rounded_rectangle(
        [r_pad, r_pad, dim - r_pad, dim - r_pad],
        radius=corner,
        fill=(11, 16, 38, 255),
        outline=(0, 229, 255, 110),
        width=max(2, dim // 64),
    )

    # Orbital ellipse approximation (tilted -24 deg)
    orbit_pts = []
    angle_rad = math.radians(-24)
    rx, ry = dim * 0.37, dim * 0.15
    for step in range(72):
        t = (step / 72.0) * 2 * math.pi
        px = rx * math.cos(t)
        py = ry * math.sin(t)
        qx = cx + px * math.cos(angle_rad) - py * math.sin(angle_rad)
        qy = cy + px * math.sin(angle_rad) + py * math.cos(angle_rad)
        orbit_pts.append((qx, qy))
    draw.line(orbit_pts + [orbit_pts[0]], fill=(0, 229, 255, 175), width=max(2, dim // 60))

    # Hexagonal shield
    hex_pts = [
        (cx, cy - dim * 0.32),
        (cx + dim * 0.27, cy - dim * 0.16),
        (cx + dim * 0.27, cy + dim * 0.13),
        (cx, cy + dim * 0.32),
        (cx - dim * 0.27, cy + dim * 0.13),
        (cx - dim * 0.27, cy - dim * 0.16),
    ]
    draw.polygon(hex_pts, fill=(13, 20, 48, 240))
    draw.line(hex_pts + [hex_pts[0]], fill=(0, 229, 255, 255), width=max(3, dim // 38), joint="curve")

    # Node connector lines
    line_w = max(2, dim // 85)
    top_node = (cx, cy - dim * 0.195)
    left_node = (cx - dim * 0.155, cy + dim * 0.115)
    right_node = (cx + dim * 0.155, cy + dim * 0.115)

    draw.line([top_node, (cx, cy - dim * 0.09)], fill=(0, 229, 255, 220), width=line_w)
    draw.line([left_node, (cx - dim * 0.06, cy + dim * 0.04)], fill=(56, 189, 248, 220), width=line_w)
    draw.line([right_node, (cx + dim * 0.06, cy + dim * 0.04)], fill=(139, 92, 246, 220), width=line_w)

    # Nodes
    nr = max(3, dim * 0.028)
    for (nx, ny), col in [
        (top_node, (0, 229, 255, 255)),
        (left_node, (56, 189, 248, 255)),
        (right_node, (139, 92, 246, 255)),
    ]:
        draw.ellipse([nx - nr, ny - nr, nx + nr, ny + nr], fill=col)

    # Waveform bars
    bar_specs = [
        (-0.095, 0.085, (0, 229, 255, 255)),
        (-0.048, 0.17, (37, 178, 250, 255)),
        (0.0, 0.23, (88, 130, 248, 255)),
        (0.048, 0.17, (118, 108, 247, 255)),
        (0.095, 0.085, (139, 92, 246, 255)),
    ]
    bw = max(2, dim * 0.028)
    for x_off, h_frac, col in bar_specs:
        bx = cx + dim * x_off
        bh = dim * h_frac
        draw.rounded_rectangle(
            [bx - bw / 2, cy - bh / 2, bx + bw / 2, cy + bh / 2],
            radius=bw / 2,
            fill=col,
        )

    return img.resize((size, size), Image.Resampling.LANCZOS)


def main() -> int:
    try:
        from PIL import Image
    except ImportError:
        print(
            "Pillow is not installed. Install it with `pip install pillow` "
            "and re-run `python generate_icons.py`.",
            file=sys.stderr,
        )
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg_path = Path(__file__).resolve().parent / "windows-app-icon.svg"

    use_cairo = False
    try:
        import cairosvg  # type: ignore

        use_cairo = svg_path.exists()
    except ImportError:
        cairosvg = None

    images: list[Image.Image] = []
    for sz in ICON_SIZES:
        if use_cairo and cairosvg is not None:
            png_bytes = cairosvg.svg2png(url=str(svg_path), output_width=sz, output_height=sz)
            img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        else:
            img = _render_with_pillow(sz)
        out_png = OUT_DIR / f"javo-icon-{sz}.png"
        img.save(out_png, format="PNG")
        images.append(img)

    # Save Windows multi-resolution .ico and tray icon
    ico_path = OUT_DIR / "javo-app.ico"
    images[-1].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in ICON_SIZES],
    )
    (OUT_DIR / "tray-icon.png").write_bytes((OUT_DIR / "javo-icon-32.png").read_bytes())

    print(f"Generated {len(ICON_SIZES)} PNG icons and {ico_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
