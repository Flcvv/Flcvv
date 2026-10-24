#!/usr/bin/env python3
"""
Automatic GitHub Profile ID SVG Generator for @Flcvv.

Fetches live profile & repository metrics from the GitHub REST API (zero external
dependencies) and renders an animated Cyber-Glass Developer ID Card (`profile-id.svg`).
"""

from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_USERNAME = "Flcvv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "profile.svg"

# Optional overrides via environment variables or defaults when GitHub profile fields are blank
DEFAULT_ROLE = os.environ.get("PROFILE_ROLE", "Software Engineer & Open Source Builder")
DEFAULT_BIO = os.environ.get(
    "PROFILE_BIO",
    "Building clean systems, creative code, and automated workflows on GitHub.",
)
DEFAULT_LOCATION = os.environ.get("PROFILE_LOCATION", "Earth // Cloud Native")

LANGUAGE_COLORS: dict[str, str] = {
    "Python": "#3572A5",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Rust": "#DEA584",
    "Go": "#00ADD8",
    "C++": "#F34B7D",
    "C": "#555555",
    "Java": "#B07219",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Shell": "#89E051",
    "SVG / Automation": "#00F5D4",
}


def github_get(url: str, token: str | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Flcvv-Profile-ID-Generator/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_avatar_data_uri(avatar_url: str) -> str:
    """Downloads avatar and encodes as base64 data URI so GitHub's SVG proxy renders it."""
    if not avatar_url:
        return ""
    try:
        sep = "&" if "?" in avatar_url else "?"
        sized_url = f"{avatar_url}{sep}s=240"
        req = urllib.request.Request(
            sized_url,
            headers={"User-Agent": "Flcvv-Profile-ID-Generator/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "image/png").split(";")[0]
            raw = resp.read()
            b64 = base64.b64encode(raw).decode("ascii")
            return f"data:{content_type};base64,{b64}"
    except Exception:
        return ""


def compute_account_age(created_at_iso: str) -> tuple[str, str]:
    try:
        created = dt.datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
    except Exception:
        created = dt.datetime.now(dt.timezone.utc)

    now = dt.datetime.now(dt.timezone.utc)
    days = max(0, (now - created).days)
    issued_str = created.strftime("%Y.%m.%d")
    if days < 1:
        age_str = "DAY 01 // GENESIS"
    elif days < 30:
        age_str = f"{days}D UPTIME"
    elif days < 365:
        months = max(1, days // 30)
        age_str = f"{months}MO ({days}D) UPTIME"
    else:
        years = days / 365.25
        age_str = f"{years:.1f}Y ({days}D) UPTIME"
    return issued_str, age_str


def collect_profile_data(username: str, token: str | None) -> dict[str, Any]:
    user = github_get(f"https://api.github.com/users/{username}", token)
    repos = github_get(
        f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
        token,
    )

    total_stars = 0
    total_forks = 0
    total_size_kb = 0
    lang_counts: dict[str, int] = {}

    if isinstance(repos, list):
        for repo in repos:
            total_stars += int(repo.get("stargazers_count", 0))
            total_forks += int(repo.get("forks_count", 0))
            total_size_kb += int(repo.get("size", 0))
            lang = repo.get("language")
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + max(1, int(repo.get("size", 1)))

    # If the account is freshly created and has no detected language bytes yet,
    # seed with the stack powering this repo so the telemetry bar looks great immediately.
    if not lang_counts:
        lang_counts = {
            "Python": 55,
            "SVG / Automation": 30,
            "Shell": 15,
        }

    total_lang_weight = sum(lang_counts.values()) or 1
    top_langs = sorted(lang_counts.items(), key=lambda item: item[1], reverse=True)[:4]
    languages = [
        {
            "name": name,
            "percent": round(weight * 100.0 / total_lang_weight, 1),
            "color": LANGUAGE_COLORS.get(name, "#7C3AED"),
        }
        for name, weight in top_langs
    ]

    # Normalize percentages to sum to 100% for the bar width
    if languages:
        diff = round(100.0 - sum(item["percent"] for item in languages), 1)
        languages[0]["percent"] = round(languages[0]["percent"] + diff, 1)

    issued_date, uptime_str = compute_account_age(user.get("created_at", ""))
    avatar_uri = fetch_avatar_data_uri(user.get("avatar_url", ""))

    return {
        "login": user.get("login") or username,
        "id": user.get("id") or 0,
        "node_id": user.get("node_id") or "U_GITHUB",
        "name": user.get("name") or user.get("login") or username,
        "role": user.get("company") or DEFAULT_ROLE,
        "bio": user.get("bio") or DEFAULT_BIO,
        "location": user.get("location") or DEFAULT_LOCATION,
        "public_repos": int(user.get("public_repos") or 0),
        "public_gists": int(user.get("public_gists") or 0),
        "followers": int(user.get("followers") or 0),
        "following": int(user.get("following") or 0),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "total_size_kb": total_size_kb,
        "issued_date": issued_date,
        "uptime_str": uptime_str,
        "avatar_uri": avatar_uri,
        "languages": languages,
        "synced_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def wrap_text(text: str, max_chars: int = 54, max_lines: int = 2) -> list[str]:
    words = text.strip().split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines - 1:
                break
    remaining_index = sum(len(line.split()) for line in lines) + len(current.split())
    if remaining_index < len(words):
        rest = " ".join(words[remaining_index:])
        combined = f"{current} {rest}".strip()
        if len(combined) > max_chars:
            current = combined[: max_chars - 1].rstrip() + "…"
        else:
            current = combined
    lines.append(current)
    return lines[:max_lines]


def build_barcode_svg(seed_text: str, start_x: int, start_y: int, height: int = 28) -> str:
    bars: list[str] = []
    x = start_x
    seed_bytes = seed_text.encode("utf-8")
    for idx in range(42):
        b = seed_bytes[idx % len(seed_bytes)]
        width = 1 + ((b + idx * 7) % 3)
        gap = 2 + ((b >> 2) % 2)
        opacity = 0.45 + (((b ^ idx) % 5) * 0.12)
        color = "#00F5D4" if idx % 7 == 0 else "#94A3B8"
        bars.append(
            f'<rect x="{x}" y="{start_y}" width="{width}" height="{height}" '
            f'rx="0.5" fill="{color}" fill-opacity="{opacity:.2f}" />'
        )
        x += width + gap
    return "\n      ".join(bars)


def render_svg(data: dict[str, Any]) -> str:
    login = html.escape(str(data["login"]))
    display_name = html.escape(str(data["name"]))
    role = html.escape(str(data["role"]))
    location = html.escape(str(data["location"]))
    user_id = f"{int(data['id']):09d}"
    node_id = html.escape(str(data["node_id"]))
    issued_date = html.escape(str(data["issued_date"]))
    uptime_str = html.escape(str(data["uptime_str"]))
    synced_at = html.escape(str(data["synced_at"]))

    bio_lines = [html.escape(line) for line in wrap_text(str(data["bio"]), max_chars=52, max_lines=2)]
    while len(bio_lines) < 2:
        bio_lines.append("")

    # Language spectrum bar segments
    bar_x = 340.0
    bar_total_w = 468.0
    lang_rects: list[str] = []
    lang_legends: list[str] = []

    for idx, lang in enumerate(data["languages"]):
        seg_w = max(8.0, round((lang["percent"] / 100.0) * bar_total_w, 2))
        if idx == len(data["languages"]) - 1:
            seg_w = max(8.0, round(340.0 + bar_total_w - bar_x, 2))
        lang_rects.append(
            f'<rect x="{bar_x:.2f}" y="302" width="{seg_w:.2f}" height="10" '
            f'fill="{lang["color"]}" />'
        )
        bar_x += seg_w

        col = idx % 2
        row = idx // 2
        lx = 340 + col * 238
        ly = 332 + row * 22
        lname = html.escape(lang["name"])
        lcolor = lang["color"]
        lpct = lang["percent"]
        lang_legends.append(
            f'<g transform="translate({lx}, {ly})">'
            f'<circle cx="6" cy="-4" r="4.5" fill="{lcolor}" />'
            f'<text x="16" y="0" class="mono-sm" fill="#E2E8F0">{lname}</text>'
            f'<text x="215" y="0" text-anchor="end" class="mono-sm" fill="#94A3B8">{lpct:.1f}%</text>'
            f"</g>"
        )

    lang_rects_svg = "\n        ".join(lang_rects)
    lang_legends_svg = "\n      ".join(lang_legends)
    barcode_svg = build_barcode_svg(f"{login}-{user_id}-{node_id}", start_x=575, start_y=438, height=24)

    avatar_uri = data.get("avatar_uri", "")
    if avatar_uri:
        avatar_element = (
            f'<image x="72" y="108" width="144" height="144" '
            f'href="{avatar_uri}" clip-path="url(#avatarClip)" preserveAspectRatio="xMidYMid slice" />'
        )
    else:
        initials = html.escape(login[:2].upper())
        avatar_element = (
            f'<rect x="72" y="108" width="144" height="144" fill="url(#avatarFallbackGrad)" clip-path="url(#avatarClip)" />'
            f'<text x="144" y="195" text-anchor="middle" class="title-lg" fill="#FFFFFF">{initials}</text>'
        )

    repos_val = f"{data['public_repos']:02d}"
    stars_val = f"{data['total_stars']:02d}"
    followers_val = f"{data['followers']:02d}"
    forks_val = f"{data['total_forks']:02d}"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 500" width="100%" height="100%" role="img" aria-label="{login} GitHub Developer ID Card">
  <title>{login} — GitHub Developer Identity Card (#{user_id})</title>
  <desc>Automated SVG Developer Profile ID for @{login}, featuring live GitHub metrics, language telemetry, and verification metadata.</desc>

  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#070913" />
      <stop offset="45%" stop-color="#0D1326" />
      <stop offset="100%" stop-color="#080B16" />
    </linearGradient>

    <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F5D4" stop-opacity="0.85" />
      <stop offset="50%" stop-color="#7C3AED" stop-opacity="0.65" />
      <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.85" />
    </linearGradient>

    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F5D4" />
      <stop offset="55%" stop-color="#3B82F6" />
      <stop offset="100%" stop-color="#A855F7" />
    </linearGradient>

    <linearGradient id="chipGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FDE68A" />
      <stop offset="50%" stop-color="#F59E0B" />
      <stop offset="100%" stop-color="#B45309" />
    </linearGradient>

    <linearGradient id="scanBeam" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00F5D4" stop-opacity="0" />
      <stop offset="50%" stop-color="#00F5D4" stop-opacity="0.09" />
      <stop offset="100%" stop-color="#00F5D4" stop-opacity="0" />
    </linearGradient>

    <linearGradient id="avatarFallbackGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1E293B" />
      <stop offset="100%" stop-color="#334155" />
    </linearGradient>

    <radialGradient id="glowCyan" cx="18%" cy="32%" r="45%">
      <stop offset="0%" stop-color="#00F5D4" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#00F5D4" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="glowViolet" cx="85%" cy="75%" r="50%">
      <stop offset="0%" stop-color="#7C3AED" stop-opacity="0.18" />
      <stop offset="100%" stop-color="#7C3AED" stop-opacity="0" />
    </radialGradient>

    <pattern id="cyberGrid" width="28" height="28" patternUnits="userSpaceOnUse">
      <path d="M 28 0 L 0 0 0 28" fill="none" stroke="#1E293B" stroke-width="0.7" stroke-opacity="0.55" />
      <circle cx="28" cy="28" r="0.9" fill="#334155" fill-opacity="0.6" />
    </pattern>

    <clipPath id="cardClip">
      <rect x="12" y="12" width="836" height="476" rx="22" />
    </clipPath>

    <clipPath id="avatarClip">
      <rect x="72" y="108" width="144" height="144" rx="26" />
    </clipPath>

    <clipPath id="langBarClip">
      <rect x="340" y="302" width="468" height="10" rx="5" />
    </clipPath>

    <style>
      .sans-title {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, sans-serif;
        font-weight: 800;
        font-size: 26px;
        letter-spacing: -0.4px;
      }}
      .sans-role {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, sans-serif;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.2px;
      }}
      .sans-bio {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, sans-serif;
        font-weight: 400;
        font-size: 12.5px;
      }}
      .mono-xs {{
        font-family: "JetBrains Mono", "Fira Code", "SFMono-Regular", Consolas, monospace;
        font-size: 10px;
        letter-spacing: 1.2px;
        font-weight: 600;
      }}
      .mono-sm {{
        font-family: "JetBrains Mono", "Fira Code", "SFMono-Regular", Consolas, monospace;
        font-size: 11.5px;
        font-weight: 500;
      }}
      .mono-stat {{
        font-family: "JetBrains Mono", "Fira Code", "SFMono-Regular", Consolas, monospace;
        font-size: 22px;
        font-weight: 800;
      }}
      .title-lg {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 44px;
        font-weight: 800;
      }}
      @keyframes pulseDot {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.35; transform: scale(0.88); }}
      }}
      @keyframes blinkCursor {{
        0%, 49% {{ opacity: 1; }}
        50%, 100% {{ opacity: 0; }}
      }}
      @keyframes orbitSpin {{
        from {{ stroke-dashoffset: 0; }}
        to {{ stroke-dashoffset: -120; }}
      }}
      @keyframes scanSweep {{
        0% {{ transform: translateY(-480px); }}
        100% {{ transform: translateY(520px); }}
      }}
      .pulse-dot {{
        animation: pulseDot 2.4s ease-in-out infinite;
        transform-origin: center;
        transform-box: fill-box;
      }}
      .cursor-blink {{
        animation: blinkCursor 1.1s step-end infinite;
      }}
      .hud-ring {{
        stroke-dasharray: 18 12;
        animation: orbitSpin 8s linear infinite;
      }}
      .scan-bar {{
        animation: scanSweep 9s linear infinite;
      }}
    </style>
  </defs>

  <!-- Card Base & Ambient Lighting -->
  <g clip-path="url(#cardClip)">
    <rect x="12" y="12" width="836" height="476" rx="22" fill="url(#bgGrad)" />
    <rect x="12" y="12" width="836" height="476" fill="url(#cyberGrid)" />
    <rect x="12" y="12" width="836" height="476" fill="url(#glowCyan)" />
    <rect x="12" y="12" width="836" height="476" fill="url(#glowViolet)" />

    <!-- Subtle Vertical Holographic Scanline -->
    <rect x="12" y="12" width="836" height="90" fill="url(#scanBeam)" class="scan-bar" />

    <!-- Top Identity Header Bar -->
    <rect x="12" y="12" width="836" height="58" fill="#0B1120" fill-opacity="0.82" />
    <line x1="12" y1="70" x2="848" y2="70" stroke="#1E293B" stroke-width="1.5" />
    <rect x="12" y="69" width="290" height="2" fill="url(#accentGrad)" />

    <!-- Header Left: GitHub Emblem + Credential Type -->
    <g transform="translate(36, 30)">
      <path fill="#00F5D4" d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
      <text x="36" y="11" class="mono-xs" fill="#00F5D4">GITHUB DEVELOPER CREDENTIAL // VERIFIED ID</text>
      <text x="36" y="24" class="mono-xs" fill="#64748B">SERIAL #{user_id} • NODE {node_id}</text>
    </g>

    <!-- Header Right: Live Status Pill -->
    <g transform="translate(664, 27)">
      <rect x="0" y="0" width="154" height="28" rx="14" fill="#0F172A" stroke="#1E293B" stroke-width="1.2" />
      <circle cx="18" cy="14" r="4.5" fill="#10B981" class="pulse-dot" />
      <text x="31" y="18" class="mono-xs" fill="#A7F3D0">STATUS: ACTIVE</text>
    </g>

    <!-- LEFT IDENTITY COLUMN (Badge Photo + Chip + Core Metadata) -->
    <rect x="34" y="90" width="276" height="330" rx="16" fill="#0F172A" fill-opacity="0.72" stroke="#1E293B" stroke-width="1.2" />

    <!-- Animated HUD Frame Around Avatar -->
    <rect x="66" y="102" width="156" height="156" rx="30" fill="none" stroke="url(#accentGrad)" stroke-width="1.8" class="hud-ring" />
    <rect x="70" y="106" width="148" height="148" rx="27" fill="none" stroke="#334155" stroke-width="1" />
    {avatar_element}

    <!-- Verified Check Badge on Avatar Corner -->
    <g transform="translate(196, 232)">
      <circle cx="14" cy="14" r="14" fill="#0B1120" />
      <circle cx="14" cy="14" r="11" fill="#00F5D4" />
      <path d="M9.5 14.2L12.5 17.2L18.8 10.9" fill="none" stroke="#070913" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
    </g>

    <!-- Metallic Smart Card Chip -->
    <g transform="translate(242, 118)">
      <rect x="0" y="0" width="44" height="34" rx="6" fill="url(#chipGrad)" stroke="#FEF3C7" stroke-width="0.6" stroke-opacity="0.6" />
      <path d="M0 11 H44 M0 23 H44 M15 0 V34 M29 0 V34" stroke="#78350F" stroke-width="1" stroke-opacity="0.55" fill="none" />
      <rect x="15" y="11" width="14" height="12" rx="2" fill="none" stroke="#78350F" stroke-width="1" stroke-opacity="0.65" />
    </g>

    <!-- Vertical Side Readout on Left Column -->
    <text x="266" y="232" transform="rotate(90 266,232)" class="mono-xs" fill="#475569">CLEARANCE // L4</text>

    <!-- Handle & Name inside Left Column -->
    <text x="54" y="290" class="sans-title" fill="#F8FAFC">{display_name}</text>
    <text x="54" y="311" class="mono-sm" fill="#00F5D4">@{login}</text>

    <line x1="54" y1="326" x2="290" y2="326" stroke="#1E293B" stroke-width="1" />

    <!-- Issued / Uptime / Location Key-Values -->
    <text x="54" y="348" class="mono-xs" fill="#64748B">ISSUED</text>
    <text x="290" y="348" text-anchor="end" class="mono-sm" fill="#E2E8F0">{issued_date}</text>

    <text x="54" y="372" class="mono-xs" fill="#64748B">TENURE</text>
    <text x="290" y="372" text-anchor="end" class="mono-sm" fill="#38BDF8">{uptime_str}</text>

    <text x="54" y="396" class="mono-xs" fill="#64748B">SECTOR</text>
    <text x="290" y="396" text-anchor="end" class="mono-sm" fill="#CBD5E1">{location}</text>

    <!-- RIGHT TELEMETRY COLUMN -->
    <!-- Profile Summary Banner -->
    <rect x="328" y="90" width="494" height="92" rx="14" fill="#0F172A" fill-opacity="0.68" stroke="#1E293B" stroke-width="1.2" />
    <text x="348" y="114" class="mono-xs" fill="#A855F7">ROLE // DESIGNATION</text>
    <text x="348" y="134" class="sans-role" fill="#F1F5F9">{role}</text>
    <text x="348" y="155" class="sans-bio" fill="#94A3B8">{bio_lines[0]}</text>
    <text x="348" y="172" class="sans-bio" fill="#94A3B8">{bio_lines[1]}</text>

    <!-- 4 Live Telemetry Stat Pods -->
    <g transform="translate(328, 194)">
      <!-- Pod 1: Repositories -->
      <rect x="0" y="0" width="114" height="74" rx="12" fill="#0F172A" fill-opacity="0.78" stroke="#1E293B" stroke-width="1.2" />
      <path d="M0 12 A12 12 0 0 1 12 0 H40" fill="none" stroke="#00F5D4" stroke-width="2" />
      <text x="16" y="25" class="mono-xs" fill="#64748B">REPOS</text>
      <text x="16" y="56" class="mono-stat" fill="#F8FAFC">{repos_val}</text>

      <!-- Pod 2: Stars Earned -->
      <rect x="126" y="0" width="114" height="74" rx="12" fill="#0F172A" fill-opacity="0.78" stroke="#1E293B" stroke-width="1.2" />
      <path d="M126 12 A12 12 0 0 1 138 0 H166" fill="none" stroke="#F59E0B" stroke-width="2" />
      <text x="142" y="25" class="mono-xs" fill="#64748B">STARS</text>
      <text x="142" y="56" class="mono-stat" fill="#FDE68A">{stars_val}</text>

      <!-- Pod 3: Followers -->
      <rect x="252" y="0" width="114" height="74" rx="12" fill="#0F172A" fill-opacity="0.78" stroke="#1E293B" stroke-width="1.2" />
      <path d="M252 12 A12 12 0 0 1 264 0 H292" fill="none" stroke="#38BDF8" stroke-width="2" />
      <text x="268" y="25" class="mono-xs" fill="#64748B">FOLLOWERS</text>
      <text x="268" y="56" class="mono-stat" fill="#E0F2FE">{followers_val}</text>

      <!-- Pod 4: Network Forks -->
      <rect x="378" y="0" width="116" height="74" rx="12" fill="#0F172A" fill-opacity="0.78" stroke="#1E293B" stroke-width="1.2" />
      <path d="M378 12 A12 12 0 0 1 390 0 H418" fill="none" stroke="#A855F7" stroke-width="2" />
      <text x="394" y="25" class="mono-xs" fill="#64748B">FORKS</text>
      <text x="394" y="56" class="mono-stat" fill="#F3E8FF">{forks_val}</text>
    </g>

    <!-- Language & Tech Spectrum Panel -->
    <rect x="328" y="280" width="494" height="86" rx="14" fill="#0F172A" fill-opacity="0.68" stroke="#1E293B" stroke-width="1.2" />
    <text x="340" y="296" class="mono-xs" fill="#64748B">LANGUAGE TELEMETRY // CODE DISTRIBUTION</text>

    <g clip-path="url(#langBarClip)">
      {lang_rects_svg}
    </g>
    {lang_legends_svg}

    <!-- Terminal Verification Console -->
    <rect x="328" y="376" width="494" height="44" rx="10" fill="#050811" stroke="#1E293B" stroke-width="1.2" />
    <circle cx="346" cy="398" r="4" fill="#EF4444" />
    <circle cx="360" cy="398" r="4" fill="#F59E0B" />
    <circle cx="374" cy="398" r="4" fill="#10B981" />
    <text x="392" y="402" class="mono-sm" fill="#94A3B8">
      <tspan fill="#00F5D4">{login}@github</tspan>:<tspan fill="#38BDF8">~</tspan>$ id --verify --sync-auto
      <tspan fill="#10B981"> [OK]</tspan>
    </text>
    <rect x="748" y="390" width="7" height="14" fill="#00F5D4" class="cursor-blink" />

    <!-- Footer Bar: Auto-Sync Timestamp & Scannable Barcode -->
    <line x1="34" y1="432" x2="822" y2="432" stroke="#1E293B" stroke-width="1" />
    <text x="36" y="452" class="mono-xs" fill="#64748B">AUTO-GENERATED VIA GITHUB ACTIONS // SVG PROFILE ID ENGINE</text>
    <text x="36" y="467" class="mono-xs" fill="#475569">LAST SYNC: {synced_at} • HTTPS://GITHUB.COM/{login.upper()}</text>

    <!-- Deterministic Barcode -->
    {barcode_svg}
  </g>

  <!-- Outer Holographic Frame Border -->
  <rect x="12" y="12" width="836" height="476" rx="22" fill="none" stroke="url(#borderGrad)" stroke-width="2" />

  <!-- Corner HUD Brackets -->
  <path d="M 12 44 V 28 A 16 16 0 0 1 28 12 H 48" fill="none" stroke="#00F5D4" stroke-width="3" stroke-linecap="round" />
  <path d="M 848 44 V 28 A 16 16 0 0 0 832 12 H 812" fill="none" stroke="#00F5D4" stroke-width="3" stroke-linecap="round" />
  <path d="M 12 456 V 472 A 16 16 0 0 0 28 488 H 48" fill="none" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" />
  <path d="M 848 456 V 472 A 16 16 0 0 1 832 488 H 812" fill="none" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" />
</svg>
"""


def main() -> None:
    username = os.environ.get("GITHUB_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or DEFAULT_USERNAME
    token = os.environ.get("GITHUB_TOKEN")
    data = collect_profile_data(username, token)
    svg_content = render_svg(data)
    OUTPUT_PATH.write_text(svg_content, encoding="utf-8")
    print(f"Generated {OUTPUT_PATH} for @{data['login']} (ID #{data['id']})")


if __name__ == "__main__":
    main()
