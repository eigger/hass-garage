"""Generate Home Assistant brand images for Garage.

The artwork is an original geometric brand mark on a dark navy rounded square:
a cyan garage roof and bay framing a crisp white front-facing vehicle silhouette
with golden LED headlights and wireless telemetry arcs. Drawn from geometric
primitives at 4x scale and downsampled, so no source image, external font file,
or network access is needed. Run with Pillow 12.3.0 for reproducible PNGs.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BRAND = Path(__file__).resolve().parents[1] / "custom_components/garage/brand"
SIZE = 512
SCALE = 4
NAVY = "#1b2a41"
CYAN = "#38bdf8"
WHITE = "#ffffff"
YELLOW = "#ffd23f"
GOLD = "#f2a900"
WORDMARK = "#e0a100"


def _rounded_polygon(
    points: list[tuple[float, float]],
    radii: list[float] | float,
    steps: int = 24,
) -> list[tuple[float, float]]:
    """Return polygon vertices with mathematically rounded corners."""
    n = len(points)
    if isinstance(radii, (int, float)):
        radii = [float(radii)] * n
    poly_pts: list[tuple[float, float]] = []
    for i in range(n):
        r = radii[i]
        if r <= 0:
            poly_pts.append(points[i])
            continue
        p_prev = points[(i - 1) % n]
        p_curr = points[i]
        p_next = points[(i + 1) % n]

        v1 = (p_prev[0] - p_curr[0], p_prev[1] - p_curr[1])
        v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
        l1 = math.hypot(*v1)
        l2 = math.hypot(*v2)
        u1 = (v1[0] / l1, v1[1] / l1)
        u2 = (v2[0] / l2, v2[1] / l2)

        dot = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
        half_ang = math.acos(dot) / 2.0
        dist = min(r / math.tan(half_ang), l1 * 0.45, l2 * 0.45)
        eff_r = dist * math.tan(half_ang)
        t1 = (p_curr[0] + u1[0] * dist, p_curr[1] + u1[1] * dist)
        t2 = (p_curr[0] + u2[0] * dist, p_curr[1] + u2[1] * dist)

        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis)
        ub = (bis[0] / bl, bis[1] / bl)
        c_dist = eff_r / math.sin(half_ang)
        center = (p_curr[0] + ub[0] * c_dist, p_curr[1] + ub[1] * c_dist)

        a1 = math.atan2(t1[1] - center[1], t1[0] - center[0])
        a2 = math.atan2(t2[1] - center[1], t2[0] - center[0])
        da = a2 - a1
        while da <= -math.pi:
            da += 2 * math.pi
        while da > math.pi:
            da -= 2 * math.pi

        for s_idx in range(steps + 1):
            a = a1 + da * s_idx / steps
            poly_pts.append(
                (center[0] + eff_r * math.cos(a), center[1] + eff_r * math.sin(a))
            )
    return poly_pts


def _draw_arc_ring(
    d: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r_in: float,
    r_out: float,
    deg_start: float,
    deg_end: float,
    fill: str,
) -> None:
    """Draw a smooth annular sector."""
    steps = 48
    a0 = math.radians(deg_start)
    a1 = math.radians(deg_end)
    pts_out = [
        (
            cx + r_out * math.cos(a0 + (a1 - a0) * i / steps),
            cy + r_out * math.sin(a0 + (a1 - a0) * i / steps),
        )
        for i in range(steps + 1)
    ]
    pts_in = [
        (
            cx + r_in * math.cos(a0 + (a1 - a0) * i / steps),
            cy + r_in * math.sin(a0 + (a1 - a0) * i / steps),
        )
        for i in range(steps + 1)
    ]
    d.polygon(pts_out + list(reversed(pts_in)), fill=fill)


def draw_icon() -> Image.Image:
    """Draw the 512px RGBA app icon."""
    s = SCALE
    image = Image.new("RGBA", (SIZE * s, SIZE * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)

    def box(x0: float, y0: float, x1: float, y1: float) -> list[float]:
        return [x0 * s, y0 * s, x1 * s, y1 * s]

    # 1. Dark navy rounded square background.
    d.rounded_rectangle(box(0, 0, SIZE - 1, SIZE - 1), radius=104 * s, fill=NAVY)

    # 2. Geometric cyan garage outer structure (pitched roof + side pillars).
    garage_outer = [
        (246 * s, 72 * s),
        (424 * s, 184 * s),
        (424 * s, 408 * s),
        (68 * s, 408 * s),
        (68 * s, 184 * s),
    ]
    d.polygon(_rounded_polygon(garage_outer, 20 * s), fill=CYAN)

    # Inner garage bay recess in dark navy.
    d.rounded_rectangle(box(106, 196, 386, 412), radius=16 * s, fill=NAVY)

    # Overhead roll-up door slats at the top of the bay.
    d.rounded_rectangle(box(122, 210, 370, 224), radius=5 * s, fill=CYAN)

    # 3. Front-facing modern car silhouette emerging from the garage bay.
    # Navy knockout halo around the car cabin and fenders so it separates cleanly.
    car_cabin_ko = [
        (164 * s, 320 * s),
        (190 * s, 240 * s),
        (302 * s, 240 * s),
        (328 * s, 320 * s),
    ]
    d.polygon(_rounded_polygon(car_cabin_ko, 22 * s), fill=NAVY)
    d.rounded_rectangle(box(114, 300, 378, 412), radius=34 * s, fill=NAVY)

    # Tires (white) extending below the bumper.
    d.rounded_rectangle(box(136, 376, 184, 438), radius=14 * s, fill=WHITE)
    d.rounded_rectangle(box(308, 376, 356, 438), radius=14 * s, fill=WHITE)

    # Car upper cabin (white) + windshield cutout (navy).
    car_cabin = [
        (174 * s, 326 * s),
        (198 * s, 252 * s),
        (294 * s, 252 * s),
        (318 * s, 326 * s),
    ]
    d.polygon(_rounded_polygon(car_cabin, 18 * s), fill=WHITE)

    windshield = [
        (194 * s, 316 * s),
        (210 * s, 268 * s),
        (282 * s, 268 * s),
        (298 * s, 316 * s),
    ]
    d.polygon(_rounded_polygon(windshield, 10 * s), fill=NAVY)

    # Car main lower body / bumper (white).
    d.rounded_rectangle(box(126, 312, 366, 404), radius=28 * s, fill=WHITE)

    # Golden LED headlights + central navy grille.
    d.rounded_rectangle(box(146, 336, 192, 364), radius=12 * s, fill=GOLD)
    d.rounded_rectangle(box(300, 336, 346, 364), radius=12 * s, fill=GOLD)
    d.rounded_rectangle(box(208, 344, 284, 382), radius=10 * s, fill=NAVY)
    d.rounded_rectangle(box(222, 356, 270, 370), radius=5 * s, fill=CYAN)

    # 4. Golden telemetry signal arcs at the top-right above the garage roof.
    acx, acy = 374 * s, 128 * s
    for r_in, r_out, col in (
        (42 * s, 56 * s, YELLOW),
        (68 * s, 82 * s, GOLD),
    ):
        _draw_arc_ring(d, acx, acy, r_in, r_out, -72, 14, fill=col)

    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main() -> None:
    """Write icon.png, icon@2x.png, logo.png and logo@2x.png."""
    BRAND.mkdir(parents=True, exist_ok=True)
    icon = draw_icon()
    icon.save(BRAND / "icon@2x.png", optimize=True)
    icon.resize((256, 256), Image.Resampling.LANCZOS).save(
        BRAND / "icon.png", optimize=True
    )

    # Pillow bundles Aileron Regular, so regeneration needs no system fonts.
    font = ImageFont.load_default(size=416)
    bounds = font.getbbox("Garage")
    wordmark = Image.new("RGBA", (bounds[2] - bounds[0], bounds[3] - bounds[1]))
    ImageDraw.Draw(wordmark).text(
        (-bounds[0], -bounds[1]), "Garage", font=font, fill=WORDMARK
    )
    wordmark = wordmark.crop(wordmark.getbbox())
    gap = 96 + ((SIZE + 96 + wordmark.width) % 2)
    logo = Image.new("RGBA", (SIZE + gap + wordmark.width, SIZE))
    logo.alpha_composite(icon, (0, 0))
    logo.alpha_composite(wordmark, (SIZE + gap, (SIZE - wordmark.height) // 2))
    logo = logo.crop(logo.getbbox())
    logo.save(BRAND / "logo@2x.png", optimize=True)
    logo.resize((logo.width // 2, logo.height // 2), Image.Resampling.LANCZOS).save(
        BRAND / "logo.png", optimize=True
    )


if __name__ == "__main__":
    main()
