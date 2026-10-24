#!/usr/bin/env python3
"""
Pure 3D Isometric Stack Tower Game SVG Generator (`profile.svg`).

Renders an endless, seamless 20-stage 3D isometric block-stacking game
inspired by Ketchapp's Stack — complete with alternating axis slides,
overhang slicing & falling physics, perfect-drop shockwave rings, combo
expansion, and zero UI clutter.
"""

from __future__ import annotations

import colorsys
import math
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path(__file__).resolve().parent.parent / "profile.svg"

# Isometric projection constants
ORIGIN_X = 450.0
ORIGIN_Y = 230.0
ISO_X = 1.55       # horizontal pixel scale per world unit
ISO_Y = 0.82       # vertical pixel scale per world unit (isometric ~2:1 tilt)
SLAB_H = 21.0      # pixel height of each 3D slab


def iso_point(x: float, y: float, z: float) -> tuple[float, float]:
    """Converts 3D world coordinates (x, y, z) to 2D isometric screen coordinates."""
    sx = ORIGIN_X + (x - y) * ISO_X
    sy = ORIGIN_Y + (x + y) * ISO_Y - z * SLAB_H
    return round(sx, 2), round(sy, 2)


def fmt_pts(pts: list[tuple[float, float]]) -> str:
    return " ".join(f"{px:.2f},{py:.2f}" for px, py in pts)


def hsl_hex(h_deg: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb((h_deg % 360.0) / 360.0, l, s)
    return f"#{int(round(r * 255)):02X}{int(round(g * 255)):02X}{int(round(b * 255)):02X}"


def slab_colors(step_index: int, total_steps: int = 20) -> tuple[str, str, str]:
    """
    Returns (top_face_hex, left_face_hex, right_face_hex) for a given block index,
    cycling smoothly through a full 360-degree pastel/vibrant Stack spectrum.
    """
    # Start around warm coral/rose (348 deg) and sweep smoothly across the full wheel
    hue = (348.0 + (step_index % total_steps) * (360.0 / total_steps)) % 360.0
    top = hsl_hex(hue, 0.78, 0.68)
    left = hsl_hex((hue - 4) % 360.0, 0.72, 0.56)   # sunlit front-left face
    right = hsl_hex((hue + 6) % 360.0, 0.68, 0.43)  # shadowed front-right face
    return top, left, right


def render_prism_faces(
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    colors: tuple[str, str, str],
) -> str:
    """Renders the 3 visible isometric faces (Top, Left-Front, Right-Front) of a 3D box."""
    top_col, left_col, right_col = colors

    # Top face at z = z1
    t_back = iso_point(x0, y0, z1)
    t_right = iso_point(x1, y0, z1)
    t_front = iso_point(x1, y1, z1)
    t_left = iso_point(x0, y1, z1)

    # Bottom front vertices at z = z0
    b_right = iso_point(x1, y0, z0)
    b_front = iso_point(x1, y1, z0)
    b_left = iso_point(x0, y1, z0)

    left_face = fmt_pts([t_left, t_front, b_front, b_left])
    right_face = fmt_pts([t_front, t_right, b_right, b_front])
    top_face = fmt_pts([t_back, t_right, t_front, t_left])

    return (
        f'<polygon points="{left_face}" fill="{left_col}" stroke="{left_col}" stroke-width="0.35" stroke-linejoin="round" />'
        f'<polygon points="{right_face}" fill="{right_col}" stroke="{right_col}" stroke-width="0.35" stroke-linejoin="round" />'
        f'<polygon points="{top_face}" fill="{top_col}" stroke="{top_col}" stroke-width="0.35" stroke-linejoin="round" />'
    )


def build_choreography() -> list[dict[str, Any]]:
    """
    Builds a 20-block choreography that shrinks via realistic overhang slices on both
    axes, hits streaks of Perfect placements, and recovers back to [-50, 50] x [-50, 50]
    at step 10 and step 20 so the infinite climb has zero loop seam.
    """
    # Each tuple: (axis, delta, bounce_passes, duration_sec, expand_to_50)
    # delta > 0: front overhang slice (+x front-right or +y front-left)
    # delta < 0: back overhang slice (-x back-left or -y back-right)
    # delta == 0: PERFECT drop!
    moves = [
        # Wave 1: Sculpting down to a mid-sized tower, then a 4x Perfect recovery
        ("x", 0.0, 0, 1.55, False),     # 1: Perfect!
        ("y", 14.0, 0, 1.65, False),    # 2: Slice front-left (+y)
        ("x", 16.0, 0, 1.60, False),    # 3: Slice front-right (+x)
        ("y", 0.0, 1, 2.15, False),     # 4: Hesitation bounce -> Perfect!
        ("x", -12.0, 0, 1.55, False),   # 5: Slice back-left (-x)
        ("y", -14.0, 0, 1.60, False),   # 6: Slice back-right (-y)
        ("x", 0.0, 0, 1.45, False),     # 7: Perfect streak 1
        ("y", 0.0, 0, 1.45, False),     # 8: Perfect streak 2
        ("x", 0.0, 0, 1.50, True),      # 9: Perfect streak 3 -> Expand X to [-50, 50]
        ("y", 0.0, 0, 1.50, True),      # 10: Perfect streak 4 -> Expand Y to [-50, 50]
        # Wave 2: Faster slices down to a dramatic narrow spire, then combo recovery
        ("x", 20.0, 0, 1.50, False),    # 11: Slice front-right (+x)
        ("y", -18.0, 0, 1.55, False),   # 12: Slice back-right (-y)
        ("x", -16.0, 1, 2.10, False),   # 13: Hesitation bounce -> Slice back-left (-x)
        ("y", 18.0, 0, 1.50, False),    # 14: Slice front-left (+y)
        ("x", 12.0, 0, 1.45, False),    # 15: Narrow slice front-right (+x)
        ("y", -12.0, 0, 1.45, False),   # 16: Narrow slice back-right (-y)
        ("x", 0.0, 0, 1.40, False),     # 17: Clutch Perfect 1!
        ("y", 0.0, 0, 1.40, False),     # 18: Clutch Perfect 2!
        ("x", 0.0, 0, 1.50, True),      # 19: Clutch Perfect 3 -> Expand X to [-50, 50]
        ("y", 0.0, 0, 1.50, True),      # 20: Clutch Perfect 4 -> Expand Y to [-50, 50]
    ]

    x0, x1 = -50.0, 50.0
    y0, y1 = -50.0, 50.0
    t_cursor = 0.0

    steps: list[dict[str, Any]] = []
    for idx, (axis, delta, bounces, dur, expand) in enumerate(moves, start=1):
        prev_x0, prev_x1 = x0, x1
        prev_y0, prev_y1 = y0, y1
        slice_box = None

        if expand:
            if axis == "x":
                x0, x1 = -50.0, 50.0
            else:
                y0, y1 = -50.0, 50.0
        elif delta != 0.0:
            if axis == "x":
                if delta > 0:
                    # Shifted toward +x (front-right): overhang is [x1, x1 + delta]
                    slice_box = (x1, x1 + delta, y0, y1, "front")
                    x0 = x0 + delta
                else:
                    # Shifted toward -x (back-left): overhang is [x0 + delta, x0]
                    slice_box = (x0 + delta, x0, y0, y1, "back")
                    x1 = x1 + delta
            else:
                if delta > 0:
                    # Shifted toward +y (front-left): overhang is [y1, y1 + delta]
                    slice_box = (x0, x1, y1, y1 + delta, "front")
                    y0 = y0 + delta
                else:
                    # Shifted toward -y (back-right): overhang is [y0 + delta, y0]
                    slice_box = (x0, x1, y0 + delta, y0, "back")
                    y1 = y1 + delta

        t_start = round(t_cursor, 3)
        t_drop = round(t_cursor + dur * 0.74, 3)
        t_end = round(t_cursor + dur, 3)
        t_cursor = t_end

        steps.append(
            {
                "k": idx,
                "axis": axis,
                "delta": delta,
                "bounces": bounces,
                "expand": expand,
                "perfect": (delta == 0.0),
                "prev_bounds": (prev_x0, prev_x1, prev_y0, prev_y1),
                "bounds": (x0, x1, y0, y1),
                "slice_box": slice_box,
                "t_start": t_start,
                "t_drop": t_drop,
                "t_end": t_end,
                "colors": slab_colors(idx, len(moves)),
            }
        )

    return steps


def render_perfect_ring(
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z_bottom: float,
    t_drop: float,
    total_dur: float,
    is_expand: bool,
) -> str:
    """Renders the signature Stack expanding isometric glow ring on a Perfect drop."""
    pad_start = 2.0
    pad_end = 22.0 if is_expand else 14.0

    p_start = [
        iso_point(x0 - pad_start, y0 - pad_start, z_bottom),
        iso_point(x1 + pad_start, y0 - pad_start, z_bottom),
        iso_point(x1 + pad_start, y1 + pad_start, z_bottom),
        iso_point(x0 - pad_start, y1 + pad_start, z_bottom),
    ]
    p_end = [
        iso_point(x0 - pad_end, y0 - pad_end, z_bottom),
        iso_point(x1 + pad_end, y0 - pad_end, z_bottom),
        iso_point(x1 + pad_end, y1 + pad_end, z_bottom),
        iso_point(x0 - pad_end, y1 + pad_end, z_bottom),
    ]

    k0 = round(t_drop / total_dur, 5)
    k1 = round(min(0.999, (t_drop + 0.48) / total_dur), 5)
    stroke_col = "#FFFBEB" if is_expand else "#FFFFFF"
    stroke_w = 4.5 if is_expand else 3.0

    return (
        f'<polygon points="{fmt_pts(p_start)}" fill="none" stroke="{stroke_col}" '
        f'stroke-width="{stroke_w}" opacity="0" stroke-linejoin="round">'
        f'<animate attributeName="points" values="{fmt_pts(p_start)};{fmt_pts(p_start)};{fmt_pts(p_end)};{fmt_pts(p_end)}" '
        f'keyTimes="0;{k0};{k1};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
        f'<animate attributeName="opacity" values="0;0;0.95;0;0" '
        f'keyTimes="0;{max(0.0, round(k0 - 0.002, 5))};{k0};{k1};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
        f"</polygon>"
    )


def render_step_elements(step: dict[str, Any], total_dur: float) -> tuple[str, str]:
    """
    Returns (back_slice_svg, main_step_svg) for step k.
    If a slice occurs on the back side, back_slice_svg is placed before the tower layer
    so it falls behind the tower in 3D space.
    """
    k = step["k"]
    z0, z1 = float(k - 1), float(k)
    axis = step["axis"]
    delta = step["delta"]
    bounces = step["bounces"]
    prev_x0, prev_x1, prev_y0, prev_y1 = step["prev_bounds"]
    x0, x1, y0, y1 = step["bounds"]
    colors = step["colors"]
    t_start = step["t_start"]
    t_drop = step["t_drop"]

    ks = round(t_start / total_dur, 5)
    kd = round(t_drop / total_dur, 5)
    ks_pre = max(0.0, round(ks - 0.001, 5))
    kd_post = min(1.0, round(kd + 0.001, 5))

    # 1. Sliding incoming block (visible only during [t_start, t_drop])
    slide_dist = 155.0
    if axis == "x":
        # Slides in from back-left (-x) toward front-right (+x)
        start_dx, start_dy = iso_point(-slide_dist, 0, 0)[0] - ORIGIN_X, iso_point(-slide_dist, 0, 0)[1] - ORIGIN_Y
        over_dx, over_dy = iso_point(55.0, 0, 0)[0] - ORIGIN_X, iso_point(55.0, 0, 0)[1] - ORIGIN_Y
        end_dx, end_dy = iso_point(delta, 0, 0)[0] - ORIGIN_X, iso_point(delta, 0, 0)[1] - ORIGIN_Y
    else:
        # Slides in from back-right (-y) toward front-left (+y)
        start_dx, start_dy = iso_point(0, -slide_dist, 0)[0] - ORIGIN_X, iso_point(0, -slide_dist, 0)[1] - ORIGIN_Y
        over_dx, over_dy = iso_point(0, 55.0, 0)[0] - ORIGIN_X, iso_point(0, 55.0, 0)[1] - ORIGIN_Y
        end_dx, end_dy = iso_point(0, delta, 0)[0] - ORIGIN_X, iso_point(0, delta, 0)[1] - ORIGIN_Y

    sliding_prism = render_prism_faces(prev_x0, prev_x1, prev_y0, prev_y1, z0, z1, colors)

    if bounces == 0:
        trans_values = f"{start_dx:.1f} {start_dy:.1f};{start_dx:.1f} {start_dy:.1f};{end_dx:.1f} {end_dy:.1f};{end_dx:.1f} {end_dy:.1f}"
        trans_kt = f"0;{ks};{kd};1"
    else:
        k_mid = round((ks + kd) * 0.52, 5)
        trans_values = (
            f"{start_dx:.1f} {start_dy:.1f};"
            f"{start_dx:.1f} {start_dy:.1f};"
            f"{over_dx:.1f} {over_dy:.1f};"
            f"{end_dx:.1f} {end_dy:.1f};"
            f"{end_dx:.1f} {end_dy:.1f}"
        )
        trans_kt = f"0;{ks};{k_mid};{kd};1"

    sliding_svg = (
        f'<g opacity="0">'
        f"{sliding_prism}"
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{trans_values}" keyTimes="{trans_kt}" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
        f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
        f'keyTimes="0;{ks_pre};{ks};{kd};{kd_post};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
        f"</g>"
    )

    # 2. Settled placed block (visible from t_drop to end of cycle)
    placed_prism = render_prism_faces(x0, x1, y0, y1, z0, z1, colors)
    placed_svg = (
        f'<g opacity="0">'
        f"{placed_prism}"
        f'<animate attributeName="opacity" values="0;0;1;1" '
        f'keyTimes="0;{kd};{kd_post};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
        f"</g>"
    )

    # 3. Optional Perfect flash ring or Falling overhang slice
    extra_front = ""
    extra_back = ""

    if step["perfect"]:
        extra_front = render_perfect_ring(x0, x1, y0, y1, z0, t_drop, total_dur, step["expand"])
    elif step["slice_box"] is not None:
        sx0, sx1, sy0, sy1, side = step["slice_box"]
        slice_prism = render_prism_faces(sx0, sx1, sy0, sy1, z0, z1, colors)
        k_fall_mid = round(min(0.995, (t_drop + 0.25) / total_dur), 5)
        k_fall_end = round(min(0.999, (t_drop + 0.62) / total_dur), 5)

        # Drift slightly outward along slice direction while dropping under gravity
        drift_x = 18.0 if (axis == "x" and delta > 0) or (axis == "y" and delta < 0) else -18.0
        slice_anim = (
            f'<g opacity="0">'
            f"{slice_prism}"
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 0;{drift_x * 0.4:.1f} 28;{drift_x:.1f} 135;{drift_x:.1f} 135" '
            f'keyTimes="0;{kd};{k_fall_mid};{k_fall_end};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
            f'<animate attributeName="opacity" values="0;0;1;0.85;0;0" '
            f'keyTimes="0;{kd};{kd_post};{k_fall_mid};{k_fall_end};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
            f"</g>"
        )
        if side == "back":
            extra_back = slice_anim
        else:
            extra_front = slice_anim

    main_svg = f"{sliding_svg}\n      {placed_svg}\n      {extra_front}"
    return extra_back, main_svg


def build_camera_animation(steps: list[dict[str, Any]], total_dur: float) -> str:
    """
    Smoothly pans the tower world downward by SLAB_H each time a block is placed,
    reaching +20 * SLAB_H at the end of the 20-block cycle.
    """
    key_times: list[str] = ["0"]
    values: list[str] = ["0 0"]

    for step in steps:
        k = step["k"]
        t_drop = step["t_drop"]
        t_settled = min(total_dur - 0.02, t_drop + 0.36)

        kt_drop = round(t_drop / total_dur, 5)
        kt_settled = round(t_settled / total_dur, 5)

        prev_y = (k - 1) * SLAB_H
        curr_y = k * SLAB_H

        key_times.append(f"{kt_drop}")
        values.append(f"0 {prev_y:.1f}")

        key_times.append(f"{kt_settled}")
        values.append(f"0 {curr_y:.1f}")

    key_times.append("1")
    values.append(f"0 {len(steps) * SLAB_H:.1f}")

    return (
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{";".join(values)}" keyTimes="{";".join(key_times)}" '
        f'dur="{total_dur:.2f}s" repeatCount="indefinite" />'
    )


def generate_svg() -> str:
    steps = build_choreography()
    num_steps = len(steps)
    total_dur = round(steps[-1]["t_end"], 2)

    # Pre-existing base tower (blocks -19 .. 0) mirrors blocks 1 .. 20 in bounds and colors
    # so that at t = total_dur (shifted down by 20 * SLAB_H), the visible tower matches t = 0 pixel-for-pixel!
    base_layers_svg: list[str] = []
    for idx in range(num_steps):
        z_level = idx - (num_steps - 1)  # -19 .. 0
        ref_step = steps[idx]
        bx0, bx1, by0, by1 = ref_step["bounds"]
        b_colors = ref_step["colors"]
        base_layers_svg.append(
            render_prism_faces(bx0, bx1, by0, by1, float(z_level - 1), float(z_level), b_colors)
        )

    # Active animated blocks 1 .. 20
    active_layers_svg: list[str] = []
    for step in steps:
        back_slice, main_step = render_step_elements(step, total_dur)
        if back_slice:
            # Insert back-side falling slice before recent layers so it falls behind the tower
            insert_pos = max(0, len(active_layers_svg) - 2)
            active_layers_svg.insert(insert_pos, back_slice)
        active_layers_svg.append(main_step)

    camera_anim = build_camera_animation(steps, total_dur)

    base_svg_str = "\n      ".join(base_layers_svg)
    active_svg_str = "\n      ".join(active_layers_svg)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 560" width="100%" height="100%">
  <defs>
    <linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1E1B4B">
        <animate attributeName="stop-color"
          values="#1E1B4B;#3B1D5A;#5B2148;#1F3A52;#163A40;#1E1B4B"
          dur="{total_dur:.2f}s" repeatCount="indefinite" />
      </stop>
      <stop offset="55%" stop-color="#312E81">
        <animate attributeName="stop-color"
          values="#312E81;#6D286B;#833857;#2B5876;#23575C;#312E81"
          dur="{total_dur:.2f}s" repeatCount="indefinite" />
      </stop>
      <stop offset="100%" stop-color="#4C1D95">
        <animate attributeName="stop-color"
          values="#4C1D95;#9D4E75;#B56565;#4E798E;#3B7A75;#4C1D95"
          dur="{total_dur:.2f}s" repeatCount="indefinite" />
      </stop>
    </linearGradient>

    <radialGradient id="ambientGlow" cx="50%" cy="42%" r="55%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.14" />
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
    </radialGradient>

    <linearGradient id="bottomMist" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0F172A" stop-opacity="0" />
      <stop offset="100%" stop-color="#090D16" stop-opacity="0.48" />
    </linearGradient>

    <clipPath id="canvasClip">
      <rect x="0" y="0" width="900" height="560" rx="22" />
    </clipPath>
  </defs>

  <g clip-path="url(#canvasClip)">
    <!-- Dynamic Smooth Color-Shifting Stack Background -->
    <rect x="0" y="0" width="900" height="560" fill="url(#skyGrad)" />
    <rect x="0" y="0" width="900" height="560" fill="url(#ambientGlow)" />

    <!-- 3D Isometric Stack Tower World -->
    <g id="towerWorld">
      {camera_anim}

      <!-- Sculpted Base Tower Layers (-19 .. 0) -->
      {base_svg_str}

      <!-- Live Animated Stacking & Slicing Layers (1 .. 20) -->
      {active_svg_str}
    </g>

    <!-- Subtle Depth Mist at Base of Viewport -->
    <rect x="0" y="450" width="900" height="110" fill="url(#bottomMist)" />
  </g>
</svg>
"""


def main() -> None:
    svg_content = generate_svg()
    OUTPUT_PATH.write_text(svg_content, encoding="utf-8")
    print(f"Generated pure 3D Isometric Stack Tower {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
