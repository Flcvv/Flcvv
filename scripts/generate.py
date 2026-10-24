from __future__ import annotations

import colorsys
import os
import random
import time
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path(__file__).resolve().parent.parent / "profile.svg"

ORIGIN_X = 450.0
ORIGIN_Y = 310.0
ISO_X = 1.58
ISO_Y = 0.84
SLAB_H = 20.0


def iso_point(x: float, y: float, z: float) -> tuple[float, float]:
    sx = ORIGIN_X + (x - y) * ISO_X
    sy = ORIGIN_Y + (x + y) * ISO_Y - z * SLAB_H
    return round(sx, 2), round(sy, 2)


def fmt_pts(pts: list[tuple[float, float]]) -> str:
    return " ".join(f"{px:.2f},{py:.2f}" for px, py in pts)


def hsl_hex(h_deg: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb((h_deg % 360.0) / 360.0, l, s)
    return f"#{int(round(r * 255)):02X}{int(round(g * 255)):02X}{int(round(b * 255)):02X}"


def slab_colors(hue_deg: float) -> tuple[str, str, str]:
    top = hsl_hex(hue_deg, 0.76, 0.67)
    left = hsl_hex((hue_deg - 5.0) % 360.0, 0.70, 0.55)
    right = hsl_hex((hue_deg + 7.0) % 360.0, 0.66, 0.42)
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
    top_col, left_col, right_col = colors

    t_back = iso_point(x0, y0, z1)
    t_right = iso_point(x1, y0, z1)
    t_front = iso_point(x1, y1, z1)
    t_left = iso_point(x0, y1, z1)

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


def simulate_ai_game(
    rng: random.Random,
    target_layers: int,
    start_hue: float,
    hue_step: float,
    t_offset: float,
) -> tuple[list[dict[str, Any]], float, dict[str, Any]]:
    x0, x1 = -54.0, 54.0
    y0, y1 = -54.0, 54.0
    t_cur = t_offset
    steps: list[dict[str, Any]] = []

    for k in range(1, target_layers + 1):
        axis = "x" if (k % 2 == 1) else "y"
        prev_x0, prev_x1, prev_y0, prev_y1 = x0, x1, y0, y1
        cur_w = (x1 - x0) if axis == "x" else (y1 - y0)

        is_fail_step = (k == target_layers) or (cur_w < 11.0)
        hue = (start_hue + k * hue_step) % 360.0
        colors = slab_colors(hue)

        bounces = 1 if (not is_fail_step and rng.random() < 0.22) else 0
        base_dur = max(1.05, 1.48 - k * 0.025 + rng.uniform(-0.08, 0.10))
        dur = round(base_dur + (0.48 if bounces else 0.0), 3)

        if is_fail_step:
            miss_dir = rng.choice([-1.0, 1.0])
            delta = round(miss_dir * (cur_w + rng.uniform(6.0, 18.0)), 2)
            t_start = round(t_cur, 3)
            t_drop = round(t_cur + dur * 0.72, 3)
            t_end = round(t_drop + 0.15, 3)
            t_cur = t_end

            if axis == "x":
                miss_box = (prev_x0 + delta, prev_x1 + delta, prev_y0, prev_y1)
            else:
                miss_box = (prev_x0, prev_x1, prev_y0 + delta, prev_y1 + delta)

            steps.append(
                {
                    "k": k,
                    "axis": axis,
                    "delta": delta,
                    "bounces": bounces,
                    "failed": True,
                    "perfect": False,
                    "prev_bounds": (prev_x0, prev_x1, prev_y0, prev_y1),
                    "bounds": None,
                    "slice_box": (*miss_box, "front" if delta > 0 else "back"),
                    "t_start": t_start,
                    "t_drop": t_drop,
                    "t_end": t_end,
                    "colors": colors,
                    "collapse_dx": round(rng.uniform(-55.0, 55.0), 1),
                    "collapse_dy": round(rng.uniform(210.0, 310.0), 1),
                }
            )
            break

        if rng.random() < 0.28:
            delta = 0.0
        else:
            max_cut = min(cur_w * 0.36, cur_w - 9.5)
            min_cut = min(4.5, max_cut * 0.5)
            if max_cut <= 2.0:
                delta = 0.0
            else:
                cut_mag = round(rng.uniform(min_cut, max_cut), 2)
                delta = cut_mag if rng.random() < 0.52 else -cut_mag

        slice_box = None
        if delta != 0.0:
            if axis == "x":
                if delta > 0:
                    slice_box = (x1, x1 + delta, y0, y1, "front")
                    x0 = round(x0 + delta, 2)
                else:
                    slice_box = (x0 + delta, x0, y0, y1, "back")
                    x1 = round(x1 + delta, 2)
            else:
                if delta > 0:
                    slice_box = (x0, x1, y1, y1 + delta, "front")
                    y0 = round(y0 + delta, 2)
                else:
                    slice_box = (x0, x1, y0 + delta, y0, "back")
                    y1 = round(y1 + delta, 2)

        t_start = round(t_cur, 3)
        t_drop = round(t_cur + dur * 0.74, 3)
        t_end = round(t_cur + dur, 3)
        t_cur = t_end

        angle_dir = 1.0 if (k % 2 == 0) else -1.0
        collapse_dx = round(angle_dir * rng.uniform(25.0, 95.0) + rng.uniform(-15.0, 15.0), 1)
        collapse_dy = round(rng.uniform(220.0, 340.0), 1)

        steps.append(
            {
                "k": k,
                "axis": axis,
                "delta": delta,
                "bounces": bounces,
                "failed": False,
                "perfect": (delta == 0.0),
                "prev_bounds": (prev_x0, prev_x1, prev_y0, prev_y1),
                "bounds": (x0, x1, y0, y1),
                "slice_box": slice_box,
                "t_start": t_start,
                "t_drop": t_drop,
                "t_end": t_end,
                "colors": colors,
                "collapse_dx": collapse_dx,
                "collapse_dy": collapse_dy,
            }
        )

    t_fail_drop = steps[-1]["t_drop"]
    t_collapse_start = round(t_fail_drop + 0.18, 3)
    t_collapse_end = round(t_collapse_start + 0.95, 3)
    t_reset_done = round(t_collapse_end + 0.55, 3)

    game_meta = {
        "t_game_start": round(t_offset, 3),
        "t_fail_drop": t_fail_drop,
        "t_collapse_start": t_collapse_start,
        "t_collapse_end": t_collapse_end,
        "t_reset_done": t_reset_done,
        "start_hue": start_hue,
        "placed_count": len(steps) - 1,
    }
    return steps, t_reset_done, game_meta


def render_perfect_ring(
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z_bottom: float,
    t_drop: float,
    total_dur: float,
) -> str:
    pad_start = 1.5
    pad_end = 13.0

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
    k1 = round(min(0.999, (t_drop + 0.42) / total_dur), 5)

    return (
        f'<polygon points="{fmt_pts(p_start)}" fill="none" stroke="#FFFFFF" '
        f'stroke-width="2.8" opacity="0" stroke-linejoin="round">'
        f'<animate attributeName="points" values="{fmt_pts(p_start)};{fmt_pts(p_start)};{fmt_pts(p_end)};{fmt_pts(p_end)}" '
        f'keyTimes="0;{k0};{k1};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
        f'<animate attributeName="opacity" values="0;0;0.92;0;0" '
        f'keyTimes="0;{max(0.0, round(k0 - 0.001, 5))};{k0};{k1};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
        f"</polygon>"
    )


def render_game_svg(
    steps: list[dict[str, Any]],
    meta: dict[str, Any],
    total_dur: float,
) -> str:
    t_game_start = meta["t_game_start"]
    t_collapse_start = meta["t_collapse_start"]
    t_collapse_end = meta["t_collapse_end"]
    t_reset_done = meta["t_reset_done"]
    placed_count = meta["placed_count"]

    kg_start = round(t_game_start / total_dur, 5)
    kg_pre = max(0.0, round(kg_start - 0.001, 5))
    kc_start = round(t_collapse_start / total_dur, 5)
    kc_end = round(t_collapse_end / total_dur, 5)

    pedestal_layers: list[str] = []
    for z_idx in range(-11, 1):
        p_hue = (meta["start_hue"] + z_idx * 10.0) % 360.0
        pedestal_layers.append(
            render_prism_faces(-54.0, 54.0, -54.0, 54.0, float(z_idx - 1), float(z_idx), slab_colors(p_hue))
        )
    pedestal_inner = "\n        ".join(pedestal_layers)

    pedestal_svg = (
        f'<g opacity="0">'
        f"\n        {pedestal_inner}\n      "
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0 90;0 0;0 0;0 180;0 90" '
        f'keyTimes="0;{kg_start};{kc_start};{kc_end};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
        f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
        f'keyTimes="0;{kg_pre};{kg_start};{kc_start};{kc_end};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
        f"</g>"
    )

    layers_svg: list[str] = [pedestal_svg]

    for step in steps:
        k = step["k"]
        z0, z1 = float(k - 1), float(k)
        axis = step["axis"]
        delta = step["delta"]
        bounces = step["bounces"]
        prev_x0, prev_x1, prev_y0, prev_y1 = step["prev_bounds"]
        colors = step["colors"]
        t_start = step["t_start"]
        t_drop = step["t_drop"]

        ks = round(t_start / total_dur, 5)
        kd = round(t_drop / total_dur, 5)
        ks_pre = max(0.0, round(ks - 0.001, 5))
        kd_post = min(1.0, round(kd + 0.001, 5))

        slide_dist = 148.0
        if axis == "x":
            start_dx, start_dy = iso_point(-slide_dist, 0, 0)[0] - ORIGIN_X, iso_point(-slide_dist, 0, 0)[1] - ORIGIN_Y
            over_dx, over_dy = iso_point(52.0, 0, 0)[0] - ORIGIN_X, iso_point(52.0, 0, 0)[1] - ORIGIN_Y
            end_dx, end_dy = iso_point(delta, 0, 0)[0] - ORIGIN_X, iso_point(delta, 0, 0)[1] - ORIGIN_Y
        else:
            start_dx, start_dy = iso_point(0, -slide_dist, 0)[0] - ORIGIN_X, iso_point(0, -slide_dist, 0)[1] - ORIGIN_Y
            over_dx, over_dy = iso_point(0, 52.0, 0)[0] - ORIGIN_X, iso_point(0, 52.0, 0)[1] - ORIGIN_Y
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

        extra_back = ""
        extra_front = ""
        if step["slice_box"] is not None:
            sx0, sx1, sy0, sy1, side = step["slice_box"]
            slice_prism = render_prism_faces(sx0, sx1, sy0, sy1, z0, z1, colors)
            fall_dur = 0.72 if step["failed"] else 0.58
            k_fall_mid = round(min(0.995, (t_drop + fall_dur * 0.42) / total_dur), 5)
            k_fall_end = round(min(0.999, (t_drop + fall_dur) / total_dur), 5)

            drift_x = 24.0 if (axis == "x" and delta > 0) or (axis == "y" and delta < 0) else -24.0
            drop_y = 195.0 if step["failed"] else 140.0
            slice_anim = (
                f'<g opacity="0">'
                f"{slice_prism}"
                f'<animateTransform attributeName="transform" type="translate" '
                f'values="0 0;0 0;{drift_x * 0.45:.1f} {drop_y * 0.25:.1f};{drift_x:.1f} {drop_y:.1f};{drift_x:.1f} {drop_y:.1f}" '
                f'keyTimes="0;{kd};{k_fall_mid};{k_fall_end};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
                f'<animate attributeName="opacity" values="0;0;1;0.9;0;0" '
                f'keyTimes="0;{kd};{kd_post};{k_fall_mid};{k_fall_end};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
                f"</g>"
            )
            if side == "back":
                extra_back = slice_anim
            else:
                extra_front = slice_anim

        if step["failed"]:
            if extra_back:
                insert_pos = max(0, len(layers_svg) - 2)
                layers_svg.insert(insert_pos, extra_back)
            layers_svg.append(f"{sliding_svg}\n      {extra_front}")
            continue

        bx0, bx1, by0, by1 = step["bounds"]
        placed_prism = render_prism_faces(bx0, bx1, by0, by1, z0, z1, colors)

        stagger = max(0.0, (placed_count - k) * 0.032)
        t_blk_col_start = min(t_collapse_end - 0.25, t_collapse_start + stagger)
        t_blk_col_mid = min(t_collapse_end - 0.10, t_blk_col_start + 0.22)
        t_blk_col_end = min(t_reset_done - 0.05, t_blk_col_start + 0.58)

        k_cs = round(t_blk_col_start / total_dur, 5)
        k_cm = round(t_blk_col_mid / total_dur, 5)
        k_ce = round(t_blk_col_end / total_dur, 5)

        cdx = step["collapse_dx"]
        cdy = step["collapse_dy"]

        placed_svg = (
            f'<g opacity="0">'
            f"{placed_prism}"
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 0;{cdx * 0.35:.1f} {cdy * 0.22:.1f};{cdx:.1f} {cdy:.1f};{cdx:.1f} {cdy:.1f}" '
            f'keyTimes="0;{k_cs};{k_cm};{k_ce};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
            f'<animate attributeName="opacity" values="0;0;1;1;0.85;0;0" '
            f'keyTimes="0;{kd};{kd_post};{k_cs};{k_cm};{k_ce};1" dur="{total_dur:.2f}s" repeatCount="indefinite" />'
            f"</g>"
        )

        if step["perfect"]:
            extra_front = render_perfect_ring(bx0, bx1, by0, by1, z0, t_drop, total_dur)

        if extra_back:
            insert_pos = max(0, len(layers_svg) - 2)
            layers_svg.insert(insert_pos, extra_back)

        layers_svg.append(f"{sliding_svg}\n      {placed_svg}\n      {extra_front}")

    return "\n      ".join(layers_svg)


def build_multi_game_camera(
    all_games: list[tuple[list[dict[str, Any]], dict[str, Any]]],
    total_dur: float,
) -> str:
    key_times: list[str] = ["0"]
    values: list[str] = ["0 0"]

    for steps, meta in all_games:
        for step in steps:
            if step["failed"]:
                continue
            k = step["k"]
            cam_prev = max(0.0, (k - 3) * SLAB_H)
            cam_curr = max(0.0, (k - 2) * SLAB_H)
            if cam_curr == cam_prev:
                continue

            t_drop = step["t_drop"]
            t_settled = min(meta["t_collapse_start"] - 0.05, t_drop + 0.34)
            kt_d = round(t_drop / total_dur, 5)
            kt_s = round(t_settled / total_dur, 5)

            if kt_d > float(key_times[-1]):
                key_times.append(f"{kt_d}")
                values.append(f"0 {cam_prev:.1f}")
            if kt_s > float(key_times[-1]):
                key_times.append(f"{kt_s}")
                values.append(f"0 {cam_curr:.1f}")

        top_cam = max(0.0, (meta["placed_count"] - 2) * SLAB_H)
        kt_col_s = round(meta["t_collapse_start"] / total_dur, 5)
        kt_col_e = round(meta["t_collapse_end"] / total_dur, 5)

        if kt_col_s > float(key_times[-1]):
            key_times.append(f"{kt_col_s}")
            values.append(f"0 {top_cam:.1f}")
        if kt_col_e > float(key_times[-1]):
            key_times.append(f"{kt_col_e}")
            values.append("0 0")

    if float(key_times[-1]) < 1.0:
        key_times.append("1")
        values.append("0 0")

    return (
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{";".join(values)}" keyTimes="{";".join(key_times)}" '
        f'dur="{total_dur:.2f}s" repeatCount="indefinite" />'
    )


def generate_svg() -> str:
    seed_val = int(os.environ.get("STACK_SEED", int(time.time()) // 3600))
    rng = random.Random(seed_val)

    game_configs = [
        (rng.randint(8, 10), rng.uniform(0.0, 360.0), 16.0),
        (rng.randint(5, 7), rng.uniform(0.0, 360.0), 19.0),
        (rng.randint(11, 14), rng.uniform(0.0, 360.0), 14.5),
    ]

    t_cursor = 0.0
    all_games: list[tuple[list[dict[str, Any]], dict[str, Any]]] = []
    for target_layers, start_hue, hue_step in game_configs:
        steps, t_cursor, meta = simulate_ai_game(
            rng=rng,
            target_layers=target_layers,
            start_hue=start_hue,
            hue_step=hue_step,
            t_offset=t_cursor,
        )
        all_games.append((steps, meta))

    total_dur = round(t_cursor, 2)
    camera_anim = build_multi_game_camera(all_games, total_dur)

    games_svg = "\n\n      ".join(
        render_game_svg(steps, meta, total_dur) for steps, meta in all_games
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 560" width="100%" height="100%">
  <defs>
    <linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1E1B4B">
        <animate attributeName="stop-color"
          values="#1E1B4B;#3B1D5A;#1F3A52;#4A1D3F;#163A40;#1E1B4B"
          dur="{total_dur:.2f}s" repeatCount="indefinite" />
      </stop>
      <stop offset="55%" stop-color="#312E81">
        <animate attributeName="stop-color"
          values="#312E81;#6D286B;#2B5876;#7A2E52;#23575C;#312E81"
          dur="{total_dur:.2f}s" repeatCount="indefinite" />
      </stop>
      <stop offset="100%" stop-color="#4C1D95">
        <animate attributeName="stop-color"
          values="#4C1D95;#9D4E75;#4E798E;#A84A62;#3B7A75;#4C1D95"
          dur="{total_dur:.2f}s" repeatCount="indefinite" />
      </stop>
    </linearGradient>

    <radialGradient id="ambientGlow" cx="50%" cy="45%" r="55%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.14" />
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
    </radialGradient>

    <linearGradient id="bottomMist" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0F172A" stop-opacity="0" />
      <stop offset="100%" stop-color="#090D16" stop-opacity="0.52" />
    </linearGradient>

    <clipPath id="canvasClip">
      <rect x="0" y="0" width="900" height="560" rx="22" />
    </clipPath>
  </defs>

  <g clip-path="url(#canvasClip)">
    <rect x="0" y="0" width="900" height="560" fill="url(#skyGrad)" />
    <rect x="0" y="0" width="900" height="560" fill="url(#ambientGlow)" />

    <g id="towerWorld">
      {camera_anim}

      {games_svg}
    </g>

    <rect x="0" y="455" width="900" height="105" fill="url(#bottomMist)" />
  </g>
</svg>
"""


def main() -> None:
    svg_content = generate_svg()
    OUTPUT_PATH.write_text(svg_content, encoding="utf-8")


if __name__ == "__main__":
    main()
