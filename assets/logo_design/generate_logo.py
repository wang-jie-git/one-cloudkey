#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One Brand Logo Generator
Programmatically generates three versions of the One logo as SVG:
  1. full    - Digital hero version with gradients, glow, and star particles
  2. mark    - Single-color solid mark for favicon / small icon usage
  3. flat    - Print-ready flat color blocks, no glow / no gradients
"""

import math
import random

random.seed(42)

# Canvas
W, H, CX, CY = 720, 720, 360, 360

# Color palette: Cyan -> Violet -> Magenta -> Gold
PALETTE = [
    (0x00, 0xE5, 0xFF),   # electric cyan
    (0x7C, 0x3A, 0xED),   # deep violet (One brand purple)
    (0xEC, 0x48, 0x99),   # magenta
    (0xFB, 0xBF, 0x24),   # warm gold
]

MARK_COLOR = "#7C3AED"


def hex_color(rgb):
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def lerp_color(t, colors):
    n = len(colors) - 1
    idx = int(t * n)
    if idx >= n:
        idx = n - 1
    local_t = (t * n) - idx
    c1, c2 = colors[idx], colors[idx + 1]
    r = int(c1[0] + (c2[0] - c1[0]) * local_t)
    g = int(c1[1] + (c2[1] - c1[1]) * local_t)
    b = int(c1[2] + (c2[2] - c1[2]) * local_t)
    return (r, g, b)


def build_spiral(turns=2.8, point_count=220):
    """Generate asymmetric spiral points."""
    pts = []
    max_theta = turns * 2 * math.pi
    for i in range(point_count):
        t = i / (point_count - 1)
        theta = t * max_theta
        # Asymmetric radius: base Archimedean + sine perturbation
        r = 14 + t * 270 + 18 * math.sin(theta * 1.4)
        # Angle perturbation to break perfect symmetry
        theta_eff = theta + 0.35 * math.sin(theta * 0.6) + 0.15 * math.cos(theta * 2.1)
        x = CX + r * math.cos(theta_eff)
        y = CY + r * math.sin(theta_eff)
        pts.append((x, y, t, r))
    return pts


def svg_header():
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 720" width="720" height="720">\n'
        '  <rect width="720" height="720" fill="#ffffff"/>\n'
    )


def svg_footer():
    return "</svg>\n"


def build_full_logo():
    pts = build_spiral()
    lines = [svg_header()]

    # Defs: singularity glow filter
    lines.append("  <defs>")
    lines.append(
        '    <filter id="singularity" x="-100%" y="-100%" width="300%" height="300%">\n'
        '      <feGaussianBlur stdDeviation="5" result="blur"/>\n'
        '      <feMerge>\n'
        '        <feMergeNode in="blur"/>\n'
        '        <feMergeNode in="SourceGraphic"/>\n'
        '      </feMerge>\n'
        '    </filter>'
    )
    lines.append("  </defs>")

    # Background star dust (sparse, ~35 particles)
    dust = []
    for _ in range(35):
        sx = random.uniform(40, 680)
        sy = random.uniform(40, 680)
        sr = random.uniform(0.6, 1.8)
        so = random.uniform(0.25, 0.6)
        dust.append(f'    <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" fill="#ffffff" fill-opacity="{so:.2f}"/>')

    # Spiral group: overlapping translucent circles for natural density build-up
    lines.append('  <g>')

    # Draw spiral as a sequence of circles (brush-stroke / particle trail)
    for i, (x, y, t, r) in enumerate(pts):
        rgb = lerp_color(t, PALETTE)
        color = hex_color(rgb)
        # Radius shrinks toward center but keeps minimum
        cr = max(5.5, 16 * (1 - t) + 7)
        # Overlap-heavy opacity: centers stack to full density, edges stay soft
        alpha = 0.82 if 0.15 < t < 0.85 else 0.55
        lines.append(f'    <circle cx="{x:.2f}" cy="{y:.2f}" r="{cr:.2f}" fill="{color}" fill-opacity="{alpha:.2f}"/>')

    lines.append("  </g>")

    # Singularity: sharp bright core
    lines.append(f'  <circle cx="{CX}" cy="{CY}" r="5" fill="#ffffff" filter="url(#singularity)"/>')
    lines.append(f'  <circle cx="{CX}" cy="{CY}" r="2.5" fill="#fff9c4"/>')

    # Star dust layer above spiral
    lines.append('  <g>')
    lines.extend(dust)
    lines.append("  </g>")

    lines.append(svg_footer())
    return "\n".join(lines)


def build_mark_logo():
    pts = build_spiral()
    lines = [svg_header()]

    # Single flat color, opacity falloff toward edges for depth
    for x, y, t, r in pts:
        cr = max(4, 12 * (1 - t) + 5)
        alpha = 0.35 + 0.65 * t  # stronger toward center
        lines.append(f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{cr:.2f}" fill="{MARK_COLOR}" fill-opacity="{alpha:.2f}"/>')

    # Center dot
    lines.append(f'  <circle cx="{CX}" cy="{CY}" r="4" fill="{MARK_COLOR}"/>')
    lines.append(svg_footer())
    return "\n".join(lines)


def build_flat_logo():
    pts = build_spiral()
    lines = [svg_header()]

    n_segments = len(PALETTE)
    seg_len = len(pts) // n_segments

    for seg_idx in range(n_segments):
        color = hex_color(PALETTE[seg_idx])
        start = seg_idx * seg_len
        end = start + seg_len + 1 if seg_idx < n_segments - 1 else len(pts)
        segment_pts = pts[start:end]

        if not segment_pts:
            continue

        # Build path
        d = f"M {segment_pts[0][0]:.1f} {segment_pts[0][1]:.1f}"
        for x, y, t, r in segment_pts[1:]:
            d += f" L {x:.1f} {y:.1f}"

        # Stroke width tapers toward center
        sw = max(16, 28 - seg_idx * 3)
        lines.append(
            f'  <path d="{d}" stroke="{color}" stroke-width="{sw}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    # Center singularity dot
    lines.append(f'  <circle cx="{CX}" cy="{CY}" r="6" fill="{hex_color(PALETTE[-1])}"/>')
    lines.append(f'  <circle cx="{CX}" cy="{CY}" r="3" fill="#ffffff"/>')
    lines.append(svg_footer())
    return "\n".join(lines)


if __name__ == "__main__":
    import os
    base = "/Users/mac/Documents/ObsidianVault/2.项目/One Platform/4.one-cloudkey/assets/logo_design"

    with open(os.path.join(base, "one_logo_full.svg"), "w", encoding="utf-8") as f:
        f.write(build_full_logo())

    with open(os.path.join(base, "one_logo_mark.svg"), "w", encoding="utf-8") as f:
        f.write(build_mark_logo())

    with open(os.path.join(base, "one_logo_flat.svg"), "w", encoding="utf-8") as f:
        f.write(build_flat_logo())

    print("Generated:")
    print(f"  {base}/one_logo_full.svg")
    print(f"  {base}/one_logo_mark.svg")
    print(f"  {base}/one_logo_flat.svg")
