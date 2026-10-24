#!/usr/bin/env python3
"""
Automated 3D Space Arcade & Cosmic Starfighter SVG Generator for @Flcvv.

Fetches live GitHub telemetry and renders a 3D perspective space animation +
auto-playing starfighter arcade battle (`profile.svg`) for GitHub READMEs.
"""

from __future__ import annotations

import base64
import datetime as dt
import html
import json
import math
import os
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_USERNAME = "Flcvv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "profile.svg"

LANGUAGE_COLORS: dict[str, str] = {
    "Python": "#00F5D4",
    "TypeScript": "#38BDF8",
    "JavaScript": "#FACC15",
    "Rust": "#FB7185",
    "Go": "#2DD4BF",
    "C++": "#C084FC",
    "C": "#94A3B8",
    "Java": "#F97316",
    "HTML": "#F43F5E",
    "CSS": "#A855F7",
    "Shell": "#4ADE80",
    "3D SVG / Shaders": "#E879F9",
}


def github_get(url: str, token: str | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Flcvv-3D-Space-Arcade-Generator/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_avatar_data_uri(avatar_url: str) -> str:
    if not avatar_url:
        return ""
    try:
        sep = "&" if "?" in avatar_url else "?"
        sized_url = f"{avatar_url}{sep}s=200"
        req = urllib.request.Request(
            sized_url,
            headers={"User-Agent": "Flcvv-3D-Space-Arcade-Generator/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "image/png").split(";")[0]
            raw = resp.read()
            b64 = base64.b64encode(raw).decode("ascii")
            return f"data:{content_type};base64,{b64}"
    except Exception:
        return ""


def collect_profile_data(username: str, token: str | None) -> dict[str, Any]:
    user = github_get(f"https://api.github.com/users/{username}", token)
    repos = github_get(
        f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
        token,
    )

    total_stars = 0
    total_forks = 0
    lang_counts: dict[str, int] = {}

    if isinstance(repos, list):
        for repo in repos:
            total_stars += int(repo.get("stargazers_count", 0))
            total_forks += int(repo.get("forks_count", 0))
            lang = repo.get("language")
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + max(1, int(repo.get("size", 1)))

    if not lang_counts:
        lang_counts = {
            "Python": 55,
            "3D SVG / Shaders": 30,
            "Shell": 15,
        }

    total_lang_weight = sum(lang_counts.values()) or 1
    top_langs = sorted(lang_counts.items(), key=lambda item: item[1], reverse=True)[:3]
    languages = [
        {
            "name": name,
            "percent": round(weight * 100.0 / total_lang_weight, 1),
            "color": LANGUAGE_COLORS.get(name, "#38BDF8"),
        }
        for name, weight in top_langs
    ]
    if languages:
        diff = round(100.0 - sum(item["percent"] for item in languages), 1)
        languages[0]["percent"] = round(languages[0]["percent"] + diff, 1)

    try:
        created = dt.datetime.fromisoformat(user.get("created_at", "").replace("Z", "+00:00"))
    except Exception:
        created = dt.datetime.now(dt.timezone.utc)

    now = dt.datetime.now(dt.timezone.utc)
    days_active = max(1, (now - created).days + 1)
    public_repos = int(user.get("public_repos") or 1)
    followers = int(user.get("followers") or 0)

    # Arcade score derived from live GitHub activity + tenure
    arcade_score = (
        days_active * 1250
        + public_repos * 4500
        + total_stars * 10000
        + followers * 3000
        + total_forks * 2500
    )

    return {
        "login": user.get("login") or username,
        "id": int(user.get("id") or 347167228),
        "node_id": user.get("node_id") or "U_GITHUB",
        "public_repos": public_repos,
        "followers": followers,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "days_active": days_active,
        "arcade_score": arcade_score,
        "avatar_uri": fetch_avatar_data_uri(user.get("avatar_url", "")),
        "languages": languages,
        "synced_at": now.strftime("%Y.%m.%d // %H:%M UTC"),
    }


def build_warp_stars_svg(cx: int = 450, cy: int = 235) -> str:
    """Generates 3D radial warp-speed stars streaking out from the vanishing point."""
    elements: list[str] = []
    num_rays = 36
    for i in range(num_rays):
        angle = (i * 137.5) % 360
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)

        start_r = 18 + (i % 5) * 12
        end_r = 280 + (i % 4) * 95
        x1 = cx + dx * start_r
        y1 = cy + dy * start_r
        x2 = cx + dx * end_r
        y2 = cy + dy * end_r

        dur = 2.2 + (i % 7) * 0.45
        delay = -(i * 0.31)
        color = "#00F5D4" if i % 4 == 0 else ("#38BDF8" if i % 3 == 0 else "#E2E8F0")
        size = 1.2 + (i % 3) * 0.6

        elements.append(
            f'<circle r="{size:.1f}" fill="{color}">'
            f'<animate attributeName="cx" values="{x1:.1f};{x2:.1f}" dur="{dur:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite" />'
            f'<animate attributeName="cy" values="{y1:.1f};{y2:.1f}" dur="{dur:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite" />'
            f'<animate attributeName="opacity" values="0;0.95;0" keyTimes="0;0.7;1" dur="{dur:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite" />'
            f'<animate attributeName="r" values="0.4;{size * 1.9:.1f}" dur="{dur:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite" />'
            f"</circle>"
        )
    return "\n      ".join(elements)


def build_perspective_grid_svg(cx: int = 450, horizon_y: int = 250, bottom_y: int = 520) -> str:
    """Builds a 3D perspective synthwave/space floor grid receding to the horizon."""
    lines: list[str] = []
    # Radial perspective lines from vanishing point
    for offset in range(-10, 11):
        bottom_x = cx + offset * 68
        top_x = cx + offset * 8
        lines.append(
            f'<line x1="{top_x}" y1="{horizon_y}" x2="{bottom_x}" y2="{bottom_y}" '
            f'stroke="url(#gridRayGrad)" stroke-width="1.1" />'
        )
    return "\n      ".join(lines)


def render_svg(data: dict[str, Any]) -> str:
    login = html.escape(str(data["login"]).upper())
    user_id = f"{int(data['id']):09d}"
    score_str = f"{int(data['arcade_score']):08d}"
    repos_str = f"{int(data['public_repos']):02d}"
    stars_str = f"{int(data['total_stars']):02d}"
    followers_str = f"{int(data['followers']):02d}"
    forks_str = f"{int(data['total_forks']):02d}"
    synced_at = html.escape(str(data["synced_at"]))

    warp_stars = build_warp_stars_svg(cx=450, cy=220)
    perspective_rays = build_perspective_grid_svg(cx=450, horizon_y=255, bottom_y=520)

    avatar_uri = data.get("avatar_uri", "")
    if avatar_uri:
        avatar_svg = (
            f'<image x="34" y="106" width="68" height="68" '
            f'href="{avatar_uri}" clip-path="url(#pilotClip)" preserveAspectRatio="xMidYMid slice" />'
        )
    else:
        avatar_svg = (
            f'<circle cx="68" cy="140" r="34" fill="#0F172A" />'
            f'<text x="68" y="146" text-anchor="middle" class="hud-lg" fill="#00F5D4">{login[:2]}</text>'
        )

    lang_bars: list[str] = []
    for idx, lang in enumerate(data["languages"]):
        ly = 294 + idx * 24
        lname = html.escape(lang["name"][:12].upper())
        lpct = lang["percent"]
        lcolor = lang["color"]
        bar_w = max(8.0, round(lpct * 1.18, 1))
        lang_bars.append(
            f'<g transform="translate(716, {ly})">'
            f'<text x="0" y="0" class="hud-xs" fill="#94A3B8">{lname}</text>'
            f'<text x="148" y="0" text-anchor="end" class="hud-xs" fill="{lcolor}">{lpct:.0f}%</text>'
            f'<rect x="0" y="5" width="148" height="5" rx="2.5" fill="#0F172A" stroke="#1E293B" stroke-width="0.6" />'
            f'<rect x="0" y="5" width="{bar_w}" height="5" rx="2.5" fill="{lcolor}" />'
            f"</g>"
        )
    lang_bars_svg = "\n      ".join(lang_bars)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 540" width="100%" height="100%" role="img" aria-label="{login} 3D Space Arcade &amp; Automated Starfighter Simulation">
  <title>{login} — 3D Space Arcade &amp; Automated Cosmic Simulation (#{user_id})</title>
  <desc>Automated 3D space starfighter game and cosmic orbital simulation driven by live GitHub telemetry for @{login}.</desc>

  <defs>
    <!-- Deep Space Nebula Gradients -->
    <radialGradient id="deepSpaceBg" cx="50%" cy="42%" r="75%">
      <stop offset="0%" stop-color="#0B0726" />
      <stop offset="45%" stop-color="#050816" />
      <stop offset="100%" stop-color="#020308" />
    </radialGradient>

    <radialGradient id="nebulaCore" cx="50%" cy="40%" r="42%">
      <stop offset="0%" stop-color="#7C3AED" stop-opacity="0.34" />
      <stop offset="45%" stop-color="#00F5D4" stop-opacity="0.12" />
      <stop offset="100%" stop-color="#000000" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="planet3D" cx="35%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#67E8F9" />
      <stop offset="35%" stop-color="#2563EB" />
      <stop offset="72%" stop-color="#1E1B4B" />
      <stop offset="100%" stop-color="#020617" />
    </radialGradient>

    <radialGradient id="planetAtmosphere" cx="50%" cy="50%" r="50%">
      <stop offset="78%" stop-color="#38BDF8" stop-opacity="0" />
      <stop offset="93%" stop-color="#00F5D4" stop-opacity="0.45" />
      <stop offset="100%" stop-color="#00F5D4" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="sunBossCore" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#FEF08A" />
      <stop offset="40%" stop-color="#F97316" />
      <stop offset="80%" stop-color="#DC2626" />
      <stop offset="100%" stop-color="#7F1D1D" stop-opacity="0" />
    </radialGradient>

    <linearGradient id="SaturnRingGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F5D4" stop-opacity="0.1" />
      <stop offset="25%" stop-color="#38BDF8" stop-opacity="0.85" />
      <stop offset="50%" stop-color="#E879F9" stop-opacity="0.95" />
      <stop offset="75%" stop-color="#38BDF8" stop-opacity="0.85" />
      <stop offset="100%" stop-color="#00F5D4" stop-opacity="0.1" />
    </linearGradient>

    <linearGradient id="gridRayGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00F5D4" stop-opacity="0.0" />
      <stop offset="30%" stop-color="#00F5D4" stop-opacity="0.35" />
      <stop offset="100%" stop-color="#A855F7" stop-opacity="0.7" />
    </linearGradient>

    <linearGradient id="horizonGlow" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00F5D4" stop-opacity="0" />
      <stop offset="50%" stop-color="#00F5D4" stop-opacity="0.45" />
      <stop offset="100%" stop-color="#7C3AED" stop-opacity="0" />
    </linearGradient>

    <linearGradient id="hullMetal" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F8FAFC" />
      <stop offset="45%" stop-color="#94A3B8" />
      <stop offset="100%" stop-color="#1E293B" />
    </linearGradient>

    <linearGradient id="wingAccent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F5D4" />
      <stop offset="100%" stop-color="#3B82F6" />
    </linearGradient>

    <linearGradient id="hudFrameGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F5D4" stop-opacity="0.9" />
      <stop offset="50%" stop-color="#3B82F6" stop-opacity="0.5" />
      <stop offset="100%" stop-color="#E879F9" stop-opacity="0.9" />
    </linearGradient>

    <clipPath id="screenClip">
      <rect x="10" y="10" width="880" height="520" rx="22" />
    </clipPath>

    <clipPath id="floorClip">
      <rect x="10" y="255" width="880" height="275" />
    </clipPath>

    <clipPath id="pilotClip">
      <circle cx="68" cy="140" r="34" />
    </clipPath>

    <!-- Reusable Enemy Drone / Bug Asteroid Mesh -->
    <g id="enemyDrone">
      <!-- Outer spinning octo-ring -->
      <polygon points="0,-18 13,-13 18,0 13,13 0,18 -13,13 -18,0 -13,-13" fill="#1E1B4B" stroke="#F43F5E" stroke-width="1.6" />
      <polygon points="0,-11 11,0 0,11 -11,0" fill="#881337" stroke="#FB7185" stroke-width="1.2" />
      <circle cx="0" cy="0" r="4.5" fill="#FDE047" />
      <circle cx="-13" cy="-13" r="1.8" fill="#00F5D4" />
      <circle cx="13" cy="-13" r="1.8" fill="#00F5D4" />
    </g>

    <!-- Reusable Laser Plasma Bolt -->
    <g id="laserPair">
      <rect x="-26" y="-14" width="3.2" height="24" rx="1.6" fill="#00F5D4" />
      <rect x="-25" y="-10" width="1.2" height="16" fill="#FFFFFF" />
      <rect x="22.8" y="-14" width="3.2" height="24" rx="1.6" fill="#00F5D4" />
      <rect x="23.8" y="-10" width="1.2" height="16" fill="#FFFFFF" />
    </g>

    <style>
      .hud-title {{
        font-family: "JetBrains Mono", "Fira Code", "SFMono-Regular", Consolas, monospace;
        font-weight: 800;
        font-size: 15px;
        letter-spacing: 1.8px;
      }}
      .hud-score {{
        font-family: "JetBrains Mono", "Fira Code", "SFMono-Regular", Consolas, monospace;
        font-weight: 800;
        font-size: 20px;
        letter-spacing: 2px;
      }}
      .hud-lg {{
        font-family: "JetBrains Mono", "Fira Code", Consolas, monospace;
        font-weight: 800;
        font-size: 16px;
        letter-spacing: 0.8px;
      }}
      .hud-sm {{
        font-family: "JetBrains Mono", "Fira Code", Consolas, monospace;
        font-weight: 600;
        font-size: 11px;
        letter-spacing: 1px;
      }}
      .hud-xs {{
        font-family: "JetBrains Mono", "Fira Code", Consolas, monospace;
        font-weight: 600;
        font-size: 9.5px;
        letter-spacing: 1.1px;
      }}
      @keyframes pulseGlow {{
        0%, 100% {{ opacity: 0.95; }}
        50% {{ opacity: 0.35; }}
      }}
      @keyframes thrusterFlicker {{
        0%, 100% {{ transform: scaleY(1); opacity: 0.95; }}
        50% {{ transform: scaleY(1.32); opacity: 0.7; }}
      }}
      @keyframes radarSweep {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
      }}
      .blink-fast {{
        animation: pulseGlow 1.4s ease-in-out infinite;
      }}
      .thruster-flame {{
        animation: thrusterFlicker 0.18s ease-in-out infinite;
        transform-origin: center top;
        transform-box: fill-box;
      }}
      .radar-hand {{
        animation: radarSweep 3.6s linear infinite;
        transform-origin: 68px 432px;
      }}
    </style>
  </defs>

  <g clip-path="url(#screenClip)">
    <!-- 1. DEEP SPACE 3D BACKGROUND & NEBULA -->
    <rect x="10" y="10" width="880" height="520" fill="url(#deepSpaceBg)" />
    <ellipse cx="450" cy="215" rx="390" ry="210" fill="url(#nebulaCore)" />

    <!-- Distant Fixed Starfield -->
    <g fill="#E2E8F0" opacity="0.65">
      <circle cx="95" cy="78" r="1" /><circle cx="164" cy="128" r="1.4" /><circle cx="242" cy="68" r="0.9" />
      <circle cx="318" cy="108" r="1.2" /><circle cx="582" cy="74" r="1.3" /><circle cx="668" cy="118" r="0.9" />
      <circle cx="748" cy="64" r="1.5" /><circle cx="812" cy="144" r="1.1" /><circle cx="132" cy="215" r="1.2" />
      <circle cx="774" cy="212" r="1.3" /><circle cx="285" cy="182" r="0.8" /><circle cx="625" cy="176" r="1.1" />
    </g>

    <!-- 2. 3D RADIAL WARP-SPEED STAR TUNNEL -->
    <g>
      {warp_stars}
    </g>

    <!-- 3. 3D PERSPECTIVE MOVING SYNTHWAVE / CYBER HORIZON FLOOR -->
    <g clip-path="url(#floorClip)">
      <rect x="10" y="255" width="880" height="275" fill="#050314" fill-opacity="0.55" />
      {perspective_rays}

      <!-- Animated Horizontal Depth Lines Approaching Viewer in 3D Perspective -->
      <g stroke="#00F5D4" stroke-opacity="0.45" fill="none">
        <line x1="10" x2="890" y1="260" y2="260" stroke-width="0.7">
          <animate attributeName="y1" values="256;520" dur="3.2s" begin="0s" repeatCount="indefinite" />
          <animate attributeName="y2" values="256;520" dur="3.2s" begin="0s" repeatCount="indefinite" />
          <animate attributeName="stroke-opacity" values="0.05;0.65;0.1" dur="3.2s" begin="0s" repeatCount="indefinite" />
          <animate attributeName="stroke-width" values="0.4;2.2" dur="3.2s" begin="0s" repeatCount="indefinite" />
        </line>
        <line x1="10" x2="890" y1="260" y2="260" stroke-width="0.7">
          <animate attributeName="y1" values="256;520" dur="3.2s" begin="-0.8s" repeatCount="indefinite" />
          <animate attributeName="y2" values="256;520" dur="3.2s" begin="-0.8s" repeatCount="indefinite" />
          <animate attributeName="stroke-opacity" values="0.05;0.65;0.1" dur="3.2s" begin="-0.8s" repeatCount="indefinite" />
          <animate attributeName="stroke-width" values="0.4;2.2" dur="3.2s" begin="-0.8s" repeatCount="indefinite" />
        </line>
        <line x1="10" x2="890" y1="260" y2="260" stroke-width="0.7">
          <animate attributeName="y1" values="256;520" dur="3.2s" begin="-1.6s" repeatCount="indefinite" />
          <animate attributeName="y2" values="256;520" dur="3.2s" begin="-1.6s" repeatCount="indefinite" />
          <animate attributeName="stroke-opacity" values="0.05;0.65;0.1" dur="3.2s" begin="-1.6s" repeatCount="indefinite" />
          <animate attributeName="stroke-width" values="0.4;2.2" dur="3.2s" begin="-1.6s" repeatCount="indefinite" />
        </line>
        <line x1="10" x2="890" y1="260" y2="260" stroke-width="0.7">
          <animate attributeName="y1" values="256;520" dur="3.2s" begin="-2.4s" repeatCount="indefinite" />
          <animate attributeName="y2" values="256;520" dur="3.2s" begin="-2.4s" repeatCount="indefinite" />
          <animate attributeName="stroke-opacity" values="0.05;0.65;0.1" dur="3.2s" begin="-2.4s" repeatCount="indefinite" />
          <animate attributeName="stroke-width" values="0.4;2.2" dur="3.2s" begin="-2.4s" repeatCount="indefinite" />
        </line>
      </g>
    </g>

    <!-- Glowing Event Horizon Band -->
    <rect x="10" y="246" width="880" height="18" fill="url(#horizonGlow)" />
    <line x1="10" y1="255" x2="890" y2="255" stroke="#00F5D4" stroke-width="1.5" stroke-opacity="0.75" />

    <!-- 4. 3D ROTATING DYSON SPHERE / PLANETARY GYROSCOPE AT CENTER HORIZON -->
    <g transform="translate(450, 178)">
      <!-- Back planetary ring half -->
      <g transform="rotate(-16)">
        <path d="M -128 0 A 128 32 0 0 1 128 0" fill="none" stroke="url(#SaturnRingGrad)" stroke-width="7" stroke-opacity="0.55" />
        <path d="M -152 0 A 152 38 0 0 1 152 0" fill="none" stroke="#38BDF8" stroke-width="1.4" stroke-dasharray="8 6" stroke-opacity="0.5" />
      </g>

      <!-- 3D Shaded Planet Body -->
      <circle cx="0" cy="0" r="64" fill="url(#planetAtmosphere)" />
      <circle cx="0" cy="0" r="54" fill="url(#planet3D)" />

      <!-- 3D Rotating Wireframe Gyroscope Rings around Planet -->
      <ellipse cx="0" cy="0" rx="54" ry="18" fill="none" stroke="#00F5D4" stroke-width="1" stroke-opacity="0.45" stroke-dasharray="5 4">
        <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="18s" repeatCount="indefinite" />
      </ellipse>
      <ellipse cx="0" cy="0" rx="22" ry="54" fill="none" stroke="#38BDF8" stroke-width="1" stroke-opacity="0.4" stroke-dasharray="4 4">
        <animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="14s" repeatCount="indefinite" />
      </ellipse>
      <ellipse cx="0" cy="0" rx="76" ry="76" fill="none" stroke="#A855F7" stroke-width="1.1" stroke-opacity="0.35" stroke-dasharray="12 20">
        <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="10s" repeatCount="indefinite" />
      </ellipse>

      <!-- Front planetary ring half (occludes planet front!) -->
      <g transform="rotate(-16)">
        <path d="M -128 0 A 128 32 0 0 0 128 0" fill="none" stroke="url(#SaturnRingGrad)" stroke-width="7.5" />
        <path d="M -152 0 A 152 38 0 0 0 152 0" fill="none" stroke="#00F5D4" stroke-width="1.6" stroke-dasharray="10 6" />
        <!-- Orbiting Moon on 3D Ring Path -->
        <circle r="5.5" fill="#FDE047" stroke="#FEF08A" stroke-width="1.5">
          <animateMotion path="M -140 0 A 140 35 0 1 0 140 0 A 140 35 0 1 0 -140 0" dur="7.5s" repeatCount="indefinite" />
        </circle>
      </g>
    </g>

    <!-- 5. AUTOMATED SPACE ARCADE BATTLE (ENEMY WAVES + LASERS + EXPLOSIONS + STARFIGHTER) -->

    <!-- Enemy Wave A (Left-Center Lane) -->
    <g>
      <use href="#enemyDrone">
        <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="2.5s" repeatCount="indefinite" />
      </use>
      <animateMotion path="M 380 140 L 310 315" dur="2.4s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.15;0.72;0.76;1" dur="2.4s" repeatCount="indefinite" />
    </g>

    <!-- Explosion A at (325, 280) when Laser hits Wave A -->
    <g transform="translate(325, 280)">
      <circle cx="0" cy="0" r="4" fill="none" stroke="#00F5D4" stroke-width="3">
        <animate attributeName="r" values="2;36;42" keyTimes="0;0.8;1" dur="2.4s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0;0;1;0" keyTimes="0;0.70;0.75;1" dur="2.4s" repeatCount="indefinite" />
      </circle>
      <circle cx="0" cy="0" r="3" fill="#FDE047">
        <animate attributeName="r" values="1;20;0" keyTimes="0;0.76;1" dur="2.4s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0;0;0.95;0" keyTimes="0;0.70;0.75;1" dur="2.4s" repeatCount="indefinite" />
      </circle>
      <text x="26" y="-12" class="hud-xs" fill="#00F5D4">
        +1000 PTS
        <animate attributeName="opacity" values="0;0;1;0" keyTimes="0;0.72;0.80;1" dur="2.4s" repeatCount="indefinite" />
      </text>
    </g>

    <!-- Enemy Wave B (Right-Center Lane) -->
    <g>
      <use href="#enemyDrone">
        <animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="2.2s" repeatCount="indefinite" />
      </use>
      <animateMotion path="M 520 135 L 585 310" dur="2.4s" begin="-1.2s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.15;0.72;0.76;1" dur="2.4s" begin="-1.2s" repeatCount="indefinite" />
    </g>

    <!-- Explosion B at (570, 275) when Laser hits Wave B -->
    <g transform="translate(570, 275)">
      <circle cx="0" cy="0" r="4" fill="none" stroke="#E879F9" stroke-width="3">
        <animate attributeName="r" values="2;36;42" keyTimes="0;0.8;1" dur="2.4s" begin="-1.2s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0;0;1;0" keyTimes="0;0.70;0.75;1" dur="2.4s" begin="-1.2s" repeatCount="indefinite" />
      </circle>
      <circle cx="0" cy="0" r="3" fill="#FDE047">
        <animate attributeName="r" values="1;20;0" keyTimes="0;0.76;1" dur="2.4s" begin="-1.2s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0;0;0.95;0" keyTimes="0;0.70;0.75;1" dur="2.4s" begin="-1.2s" repeatCount="indefinite" />
      </circle>
      <text x="-75" y="-12" class="hud-xs" fill="#E879F9">
        CRITICAL HIT!
        <animate attributeName="opacity" values="0;0;1;0" keyTimes="0;0.72;0.80;1" dur="2.4s" begin="-1.2s" repeatCount="indefinite" />
      </text>
    </g>

    <!-- Enemy Wave C (Center Boss Drone Weaving) -->
    <g>
      <g transform="scale(1.25)">
        <use href="#enemyDrone" />
      </g>
      <animateMotion path="M 450 115 Q 370 210 450 245 Q 530 210 450 115" dur="4.8s" repeatCount="indefinite" />
    </g>

    <!-- Target Lock Reticle Tracking in Center -->
    <g>
      <rect x="-22" y="-22" width="44" height="44" rx="6" fill="none" stroke="#F43F5E" stroke-width="1.4" stroke-dasharray="8 6" />
      <line x1="-28" y1="0" x2="-16" y2="0" stroke="#F43F5E" stroke-width="1.4" />
      <line x1="16" y1="0" x2="28" y2="0" stroke="#F43F5E" stroke-width="1.4" />
      <text x="0" y="-27" text-anchor="middle" class="hud-xs" fill="#FB7185">LOCK // AUTO</text>
      <animateMotion path="M 450 115 Q 370 210 450 245 Q 530 210 450 115" dur="4.8s" repeatCount="indefinite" />
    </g>

    <!-- Automated Starfighter + Synchronized Laser Bolts -->
    <g>
      <!-- Smooth 3D Patrol Weaving Path Across the Arcade Arena -->
      <animateMotion
        path="M 450 430 C 310 425, 295 395, 345 405 C 405 415, 505 415, 555 405 C 605 395, 590 425, 450 430 Z"
        dur="4.8s"
        repeatCount="indefinite" />

      <!-- Continuous Rapid-Fire Laser Salvos Originating From Starfighter Wings -->
      <g>
        <use href="#laserPair" />
        <animateTransform attributeName="transform" type="translate" from="0 -25" to="0 -260" dur="0.6s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="1;0.9;0" keyTimes="0;0.8;1" dur="0.6s" repeatCount="indefinite" />
      </g>
      <g>
        <use href="#laserPair" />
        <animateTransform attributeName="transform" type="translate" from="0 -25" to="0 -260" dur="0.6s" begin="-0.3s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="1;0.9;0" keyTimes="0;0.8;1" dur="0.6s" begin="-0.3s" repeatCount="indefinite" />
      </g>

      <!-- 3D Starfighter Ship Mesh (USS FLCVV-01) -->
      <g>
        <!-- Slight banking tilt animation -->
        <animateTransform
          attributeName="transform"
          type="rotate"
          values="0;-10;0;10;0"
          keyTimes="0;0.25;0.5;0.75;1"
          dur="4.8s"
          repeatCount="indefinite" />

        <!-- Ship Drop Shadow on 3D Grid -->
        <ellipse cx="0" cy="42" rx="38" ry="9" fill="#000000" fill-opacity="0.55" />

        <!-- Dual Plasma Thruster Plumes -->
        <g class="thruster-flame">
          <polygon points="-16,24 -10,24 -13,56" fill="#00F5D4" />
          <polygon points="-15,24 -11,24 -13,44" fill="#FFFFFF" />
          <polygon points="10,24 16,24 13,56" fill="#00F5D4" />
          <polygon points="11,24 15,24 13,44" fill="#FFFFFF" />
        </g>

        <!-- Swept Outer 3D Wings -->
        <polygon points="0,-30 -56,22 -24,18 -14,26 14,26 24,18 56,22" fill="url(#hullMetal)" stroke="#475569" stroke-width="1.2" />
        <!-- Wing Neon Energy Channels -->
        <polygon points="-8,-14 -48,19 -34,19 -8,2" fill="url(#wingAccent)" />
        <polygon points="8,-14 48,19 34,19 8,2" fill="url(#wingAccent)" />

        <!-- Wingtip Laser Cannons -->
        <rect x="-28" y="-8" width="4" height="22" rx="2" fill="#E2E8F0" stroke="#00F5D4" stroke-width="0.8" />
        <rect x="24" y="-8" width="4" height="22" rx="2" fill="#E2E8F0" stroke="#00F5D4" stroke-width="0.8" />

        <!-- Center Fuselage & Armored Nose Cone -->
        <polygon points="0,-42 -14,16 0,28 14,16" fill="#F8FAFC" stroke="#64748B" stroke-width="1" />
        <!-- 3D Canopy Glass -->
        <polygon points="0,-24 -7,4 0,12 7,4" fill="#0284C7" stroke="#38BDF8" stroke-width="1" />
        <polygon points="0,-20 -3,-2 0,4 3,-2" fill="#BAE6FD" fill-opacity="0.7" />
      </g>
    </g>

    <!-- 6. 3D COCKPIT & ARCADE CABINET HUD OVERLAY -->
    <!-- Top Arcade Scoreboard Header -->
    <path d="M 10 10 H 890 V 58 L 855 70 H 45 L 10 58 Z" fill="#060B19" fill-opacity="0.86" stroke="#1E293B" stroke-width="1.4" />
    <line x1="45" y1="70" x2="855" y2="70" stroke="url(#hudFrameGrad)" stroke-width="2" />

    <!-- Top-Left: Player 1 Identity -->
    <circle cx="34" cy="34" r="5" fill="#10B981" class="blink-fast" />
    <text x="48" y="32" class="hud-title" fill="#F8FAFC">1UP // COMMANDER @{login}</text>
    <text x="48" y="49" class="hud-xs" fill="#00F5D4">GALACTIC ID #{user_id} • AUTO-PILOT ENGAGED</text>

    <!-- Top-Center: Arcade High Score Readout -->
    <rect x="352" y="18" width="196" height="42" rx="8" fill="#020617" stroke="#00F5D4" stroke-width="1.2" stroke-opacity="0.7" />
    <text x="450" y="32" text-anchor="middle" class="hud-xs" fill="#E879F9">GALACTIC HI-SCORE</text>
    <text x="450" y="53" text-anchor="middle" class="hud-score" fill="#FDE047">{score_str}</text>

    <!-- Top-Right: Stage & Hyperdrive Status -->
    <text x="862" y="33" text-anchor="end" class="hud-sm" fill="#38BDF8">SECTOR 07 // WARP 9.4</text>
    <text x="862" y="50" text-anchor="end" class="hud-xs" fill="#A855F7">MISSION DAY #{data['days_active']:03d}</text>

    <!-- LEFT HUD PANEL: Pilot Hologram & Shield/Weapon Systems -->
    <g opacity="0.92">
      <rect x="24" y="88" width="172" height="284" rx="14" fill="#060B19" fill-opacity="0.78" stroke="#1E293B" stroke-width="1.2" />
      <path d="M 24 108 V 98 A 10 10 0 0 1 34 88 H 85" fill="none" stroke="#00F5D4" stroke-width="2" />

      <!-- Pilot Avatar Hologram Ring -->
      <circle cx="68" cy="140" r="38" fill="none" stroke="#00F5D4" stroke-width="1.4" stroke-dasharray="8 5">
        <animateTransform attributeName="transform" type="rotate" from="0 68 140" to="360 68 140" dur="12s" repeatCount="indefinite" />
      </circle>
      {avatar_svg}

      <text x="114" y="124" class="hud-xs" fill="#64748B">PILOT</text>
      <text x="114" y="140" class="hud-sm" fill="#F8FAFC">{login[:8]}</text>
      <text x="114" y="156" class="hud-xs" fill="#10B981">ONLINE</text>

      <line x1="38" y1="190" x2="182" y2="190" stroke="#1E293B" stroke-width="1" />

      <!-- Hull & Shield Telemetry Bars -->
      <text x="38" y="210" class="hud-xs" fill="#94A3B8">DEFLECTOR SHIELDS</text>
      <text x="182" y="210" text-anchor="end" class="hud-xs" fill="#00F5D4">100%</text>
      <rect x="38" y="216" width="144" height="6" rx="3" fill="#0F172A" />
      <rect x="38" y="216" width="144" height="6" rx="3" fill="url(#wingAccent)" />

      <text x="38" y="244" class="hud-xs" fill="#94A3B8">PLASMA CANNONS</text>
      <text x="182" y="244" text-anchor="end" class="hud-xs" fill="#E879F9">MAX</text>
      <rect x="38" y="250" width="144" height="6" rx="3" fill="#0F172A" />
      <rect x="38" y="250" width="144" height="6" rx="3" fill="#E879F9">
        <animate attributeName="width" values="120;144;132;144" dur="1.2s" repeatCount="indefinite" />
      </rect>

      <text x="38" y="278" class="hud-xs" fill="#94A3B8">AI TARGETING</text>
      <text x="38" y="295" class="hud-sm" fill="#FDE047">LOCKED [3/3]</text>

      <!-- Live 3D Tactical Radar Scope (Bottom-Left) -->
      <rect x="24" y="382" width="172" height="102" rx="14" fill="#060B19" fill-opacity="0.82" stroke="#1E293B" stroke-width="1.2" />
      <circle cx="68" cy="432" r="34" fill="#020617" stroke="#00F5D4" stroke-width="1.2" stroke-opacity="0.7" />
      <circle cx="68" cy="432" r="22" fill="none" stroke="#1E293B" stroke-width="0.8" />
      <circle cx="68" cy="432" r="10" fill="none" stroke="#1E293B" stroke-width="0.8" />
      <line x1="34" y1="432" x2="102" y2="432" stroke="#1E293B" stroke-width="0.8" />
      <line x1="68" y1="398" x2="68" y2="466" stroke="#1E293B" stroke-width="0.8" />
      <!-- Rotating Radar Sweep Line -->
      <line x1="68" y1="432" x2="68" y2="398" stroke="#00F5D4" stroke-width="2" class="radar-hand" />
      <!-- Radar Enemy Blips -->
      <circle cx="56" cy="416" r="2.5" fill="#F43F5E" class="blink-fast" />
      <circle cx="82" cy="422" r="2.5" fill="#F43F5E" class="blink-fast" />
      <circle cx="68" cy="410" r="2.8" fill="#FDE047" class="blink-fast" />

      <text x="112" y="416" class="hud-xs" fill="#00F5D4">RADAR SWEEP</text>
      <text x="112" y="434" class="hud-xs" fill="#94A3B8">HOSTILES: 03</text>
      <text x="112" y="450" class="hud-xs" fill="#10B981">CLEARANCE: L5</text>
    </g>

    <!-- RIGHT HUD PANEL: Live GitHub Telemetry & Reactor Spectrum -->
    <g opacity="0.92">
      <rect x="702" y="88" width="174" height="396" rx="14" fill="#060B19" fill-opacity="0.78" stroke="#1E293B" stroke-width="1.2" />
      <path d="M 876 108 V 98 A 10 10 0 0 0 866 88 H 815" fill="none" stroke="#E879F9" stroke-width="2" />

      <text x="716" y="112" class="hud-xs" fill="#00F5D4">FLEET TELEMETRY</text>

      <!-- Stat Pod 1: Star Systems (Repos) -->
      <rect x="716" y="122" width="70" height="54" rx="8" fill="#0F172A" stroke="#1E293B" stroke-width="1" />
      <text x="724" y="138" class="hud-xs" fill="#64748B">SYSTEMS</text>
      <text x="724" y="164" class="hud-lg" fill="#00F5D4">{repos_str}</text>

      <!-- Stat Pod 2: Supernovas (Stars) -->
      <rect x="794" y="122" width="70" height="54" rx="8" fill="#0F172A" stroke="#1E293B" stroke-width="1" />
      <text x="802" y="138" class="hud-xs" fill="#64748B">STARS</text>
      <text x="802" y="164" class="hud-lg" fill="#FDE047">{stars_str}</text>

      <!-- Stat Pod 3: Wingmen (Followers) -->
      <rect x="716" y="184" width="70" height="54" rx="8" fill="#0F172A" stroke="#1E293B" stroke-width="1" />
      <text x="724" y="200" class="hud-xs" fill="#64748B">ALLIES</text>
      <text x="724" y="226" class="hud-lg" fill="#38BDF8">{followers_str}</text>

      <!-- Stat Pod 4: Warp Jumps (Forks) -->
      <rect x="794" y="184" width="70" height="54" rx="8" fill="#0F172A" stroke="#1E293B" stroke-width="1" />
      <text x="802" y="200" class="hud-xs" fill="#64748B">PORTALS</text>
      <text x="802" y="226" class="hud-lg" fill="#E879F9">{forks_str}</text>

      <line x1="716" y1="254" x2="864" y2="254" stroke="#1E293B" stroke-width="1" />

      <!-- Reactor Core Spectrum (Languages) -->
      <text x="716" y="274" class="hud-xs" fill="#E879F9">REACTOR SPECTRUM</text>
      {lang_bars_svg}

      <line x1="716" y1="374" x2="864" y2="374" stroke="#1E293B" stroke-width="1" />

      <!-- 3D Rotating Wireframe Cube Hologram inside Right HUD -->
      <text x="716" y="394" class="hud-xs" fill="#38BDF8">3D NAV-CORE</text>
      <g transform="translate(790, 436)">
        <polygon points="0,-24 22,-12 22,12 0,24 -22,12 -22,-12" fill="none" stroke="#00F5D4" stroke-width="1.3">
          <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="9s" repeatCount="indefinite" />
        </polygon>
        <polygon points="0,-16 14,-8 14,8 0,16 -14,8 -14,-8" fill="none" stroke="#E879F9" stroke-width="1.1">
          <animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="6s" repeatCount="indefinite" />
        </polygon>
        <circle cx="0" cy="0" r="3.5" fill="#FDE047" class="blink-fast" />
      </g>
    </g>

    <!-- Bottom Arcade Status Bar -->
    <rect x="10" y="496" width="880" height="34" fill="#040711" fill-opacity="0.9" />
    <line x1="10" y1="496" x2="890" y2="496" stroke="#1E293B" stroke-width="1.2" />
    <text x="30" y="517" class="hud-xs" fill="#00F5D4">INSERT COIN [FREE PLAY] // AUTO-BATTLE ENGINE ACTIVE</text>
    <text x="870" y="517" text-anchor="end" class="hud-xs" fill="#64748B">TELEMETRY SYNC: {synced_at}</text>
  </g>

  <!-- Outer Neon Arcade Bezel -->
  <rect x="10" y="10" width="880" height="520" rx="22" fill="none" stroke="url(#hudFrameGrad)" stroke-width="2.4" />
</svg>
"""


def main() -> None:
    username = os.environ.get("GITHUB_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or DEFAULT_USERNAME
    token = os.environ.get("GITHUB_TOKEN")
    data = collect_profile_data(username, token)
    svg_content = render_svg(data)
    OUTPUT_PATH.write_text(svg_content, encoding="utf-8")
    print(f"Generated 3D Space Arcade {OUTPUT_PATH} for @{data['login']} (Score {data['arcade_score']})")


if __name__ == "__main__":
    main()
