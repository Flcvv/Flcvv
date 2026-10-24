#!/usr/bin/env python3
"""
Automatic Cottagecore GitHub Profile ID SVG Generator for @Flcvv.

Fetches live profile & repository metrics from the GitHub REST API and renders
a warm, botanical Cottagecore Atelier & Library Identity Card (`profile.svg`).
"""

from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_USERNAME = "Flcvv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "profile.svg"

DEFAULT_ROLE = os.environ.get("PROFILE_ROLE", "Software Artisan & Woodland Tinkerer")
DEFAULT_BIO = os.environ.get(
    "PROFILE_BIO",
    "Tending digital gardens, crafting cozy code, and brewing quiet automations by the hearth.",
)
DEFAULT_LOCATION = os.environ.get("PROFILE_LOCATION", "Sunlit Meadow • Cloud Cottage")

# Warm Cottagecore & Botanical language palette
LANGUAGE_COLORS: dict[str, str] = {
    "Python": "#5E8C6A",          # Sage Moss
    "TypeScript": "#6A8D9B",      # Misty Lake Blue
    "JavaScript": "#D9A441",      # Wildflower Honey
    "Rust": "#C47457",            # Terracotta Clay
    "Go": "#7BA098",              # Lichen Teal
    "C++": "#B86B77",             # Pressed Rose
    "C": "#7D7068",               # River Stone
    "Java": "#B07C4F",            # Cinnamon Bark
    "HTML": "#CE7955",            # Autumn Persimmon
    "CSS": "#8E7394",             # Dried Lavender
    "Shell": "#7E9960",           # Fern Leaf
    "Botanical SVG": "#D49B54",   # Golden Chamomile
}


def github_get(url: str, token: str | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Flcvv-Cottage-Profile-Generator/1.0",
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
            headers={"User-Agent": "Flcvv-Cottage-Profile-Generator/1.0"},
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
    issued_str = created.strftime("%b %d, %Y")
    if days < 1:
        age_str = "First Sprout • Day 1"
    elif days < 30:
        age_str = f"{days} Sunrises"
    elif days < 365:
        months = max(1, days // 30)
        age_str = f"{months} Mo ({days} Days)"
    else:
        years = days / 365.25
        age_str = f"{years:.1f} Seasons ({days}d)"
    return issued_str, age_str


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
            "Botanical SVG": 30,
            "Shell": 15,
        }

    total_lang_weight = sum(lang_counts.values()) or 1
    top_langs = sorted(lang_counts.items(), key=lambda item: item[1], reverse=True)[:4]
    languages = [
        {
            "name": name,
            "percent": round(weight * 100.0 / total_lang_weight, 1),
            "color": LANGUAGE_COLORS.get(name, "#8E7394"),
        }
        for name, weight in top_langs
    ]

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
        "followers": int(user.get("followers") or 0),
        "following": int(user.get("following") or 0),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "issued_date": issued_date,
        "uptime_str": uptime_str,
        "avatar_uri": avatar_uri,
        "languages": languages,
        "synced_at": dt.datetime.now(dt.timezone.utc).strftime("%b %d, %Y • %H:%M UTC"),
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


def build_library_barcode(seed_text: str, start_x: int, start_y: int, height: int = 22) -> str:
    bars: list[str] = []
    x = start_x
    seed_bytes = seed_text.encode("utf-8")
    palette = ["#5E8C6A", "#8C5E45", "#A68A71", "#C47457"]
    for idx in range(38):
        b = seed_bytes[idx % len(seed_bytes)]
        width = 1 + ((b + idx * 5) % 3)
        gap = 2 + ((b >> 2) % 2)
        opacity = 0.45 + (((b ^ idx) % 5) * 0.1)
        color = palette[idx % len(palette)]
        bars.append(
            f'<rect x="{x}" y="{start_y}" width="{width}" height="{height}" '
            f'rx="0.8" fill="{color}" fill-opacity="{opacity:.2f}" />'
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

    # Botanical language bar
    bar_x = 344.0
    bar_total_w = 456.0
    lang_rects: list[str] = []
    lang_legends: list[str] = []

    for idx, lang in enumerate(data["languages"]):
        seg_w = max(8.0, round((lang["percent"] / 100.0) * bar_total_w, 2))
        if idx == len(data["languages"]) - 1:
            seg_w = max(8.0, round(344.0 + bar_total_w - bar_x, 2))
        lang_rects.append(
            f'<rect x="{bar_x:.2f}" y="305" width="{seg_w:.2f}" height="11" '
            f'fill="{lang["color"]}" />'
        )
        bar_x += seg_w

        col = idx % 2
        row = idx // 2
        lx = 344 + col * 232
        ly = 336 + row * 22
        lname = html.escape(lang["name"])
        lcolor = lang["color"]
        lpct = lang["percent"]
        lang_legends.append(
            f'<g transform="translate({lx}, {ly})">'
            f'<path d="M2 -4 C2 -8, 8 -8, 10 -4 C8 0, 2 0, 2 -4 Z" fill="{lcolor}" />'
            f'<text x="16" y="0" class="typewriter-sm" fill="#4A3B32">{lname}</text>'
            f'<text x="210" y="0" text-anchor="end" class="typewriter-sm" fill="#847062">{lpct:.1f}%</text>'
            f"</g>"
        )

    lang_rects_svg = "\n        ".join(lang_rects)
    lang_legends_svg = "\n      ".join(lang_legends)
    barcode_svg = build_library_barcode(f"{login}-{user_id}-{node_id}", start_x=580, start_y=436, height=22)

    avatar_uri = data.get("avatar_uri", "")
    if avatar_uri:
        avatar_element = (
            f'<image x="82" y="114" width="136" height="136" '
            f'href="{avatar_uri}" clip-path="url(#avatarClip)" preserveAspectRatio="xMidYMid slice" />'
        )
    else:
        initials = html.escape(login[:2].upper())
        avatar_element = (
            f'<rect x="82" y="114" width="136" height="136" fill="#E6DEC8" clip-path="url(#avatarClip)" />'
            f'<text x="150" y="196" text-anchor="middle" class="serif-initials" fill="#5E8C6A">{initials}</text>'
        )

    repos_val = f"{data['public_repos']}"
    stars_val = f"{data['total_stars']}"
    followers_val = f"{data['followers']}"
    forks_val = f"{data['total_forks']}"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 500" width="100%" height="100%" role="img" aria-label="{login} Cottagecore Guild Identity Card">
  <title>{login} — Woodland Atelier &amp; Guild Identity Card (#{user_id})</title>
  <desc>Aesthetic cottagecore botanical profile card for @{login}, automatically tended via GitHub Actions.</desc>

  <defs>
    <!-- Warm Linen & Pressed Parchment Gradients -->
    <linearGradient id="parchmentBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FCF8F0" />
      <stop offset="50%" stop-color="#F6EFE2" />
      <stop offset="100%" stop-color="#EFE5D4" />
    </linearGradient>

    <linearGradient id="cardstockPanel" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFDF9" stop-opacity="0.88" />
      <stop offset="100%" stop-color="#F7F0E4" stop-opacity="0.88" />
    </linearGradient>

    <linearGradient id="sageHeader" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#4A6B53" />
      <stop offset="50%" stop-color="#5E8066" />
      <stop offset="100%" stop-color="#4F6F58" />
    </linearGradient>

    <linearGradient id="waxSealGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#D47A63" />
      <stop offset="55%" stop-color="#B85A43" />
      <stop offset="100%" stop-color="#8F3F2B" />
    </linearGradient>

    <linearGradient id="washiTape" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#A8C2A5" stop-opacity="0.72" />
      <stop offset="50%" stop-color="#BBD1B8" stop-opacity="0.82" />
      <stop offset="100%" stop-color="#A2BCA0" stop-opacity="0.72" />
    </linearGradient>

    <radialGradient id="sunlightGlow" cx="15%" cy="20%" r="55%">
      <stop offset="0%" stop-color="#FCE8B2" stop-opacity="0.38" />
      <stop offset="100%" stop-color="#FCE8B2" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="meadowGlow" cx="88%" cy="82%" r="45%">
      <stop offset="0%" stop-color="#C5DAC1" stop-opacity="0.35" />
      <stop offset="100%" stop-color="#C5DAC1" stop-opacity="0" />
    </radialGradient>

    <!-- Subtle Linen & Botanical Dot Grid Pattern -->
    <pattern id="linenGrid" width="24" height="24" patternUnits="userSpaceOnUse">
      <circle cx="12" cy="12" r="0.8" fill="#C7B8A3" fill-opacity="0.45" />
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#E5DAC8" stroke-width="0.5" stroke-opacity="0.55" />
    </pattern>

    <clipPath id="cardClip">
      <rect x="12" y="12" width="836" height="476" rx="22" />
    </clipPath>

    <clipPath id="avatarClip">
      <rect x="82" y="114" width="136" height="136" rx="68" />
    </clipPath>

    <clipPath id="langBarClip">
      <rect x="344" y="305" width="456" height="11" rx="5.5" />
    </clipPath>

    <style>
      .serif-title {{
        font-family: Georgia, "Playfair Display", "Palatino Linotype", "Book Antiqua", serif;
        font-weight: 700;
        font-size: 25px;
        letter-spacing: 0.2px;
      }}
      .serif-italic {{
        font-family: Georgia, "Playfair Display", "Palatino Linotype", serif;
        font-style: italic;
        font-weight: 400;
        font-size: 13.5px;
      }}
      .serif-role {{
        font-family: Georgia, "Playfair Display", "Palatino Linotype", serif;
        font-weight: 700;
        font-size: 14.5px;
      }}
      .serif-bio {{
        font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif;
        font-size: 12.5px;
      }}
      .serif-stat {{
        font-family: Georgia, "Playfair Display", serif;
        font-weight: 700;
        font-size: 23px;
      }}
      .serif-initials {{
        font-family: Georgia, serif;
        font-weight: 700;
        font-size: 42px;
      }}
      .typewriter-xs {{
        font-family: "Courier Prime", "Courier New", Courier, monospace;
        font-size: 10px;
        letter-spacing: 1.1px;
        font-weight: 700;
      }}
      .typewriter-sm {{
        font-family: "Courier Prime", "Courier New", Courier, monospace;
        font-size: 11.5px;
        font-weight: 600;
      }}
      @keyframes swayBreeze {{
        0%, 100% {{ transform: rotate(0deg); }}
        50% {{ transform: rotate(2.5deg); }}
      }}
      @keyframes fireflyGlow {{
        0%, 100% {{ opacity: 0.25; transform: translateY(0px) scale(0.9); }}
        50% {{ opacity: 0.9; transform: translateY(-3px) scale(1.15); }}
      }}
      @keyframes gentlePulse {{
        0%, 100% {{ opacity: 0.95; }}
        50% {{ opacity: 0.45; }}
      }}
      .botanical-sway {{
        animation: swayBreeze 6s ease-in-out infinite;
        transform-origin: center;
        transform-box: fill-box;
      }}
      .firefly-1 {{
        animation: fireflyGlow 4.2s ease-in-out infinite;
      }}
      .firefly-2 {{
        animation: fireflyGlow 5.5s ease-in-out 1.4s infinite;
      }}
      .hearth-pulse {{
        animation: gentlePulse 3s ease-in-out infinite;
      }}
    </style>
  </defs>

  <!-- Main Pressed Parchment Card -->
  <g clip-path="url(#cardClip)">
    <rect x="12" y="12" width="836" height="476" rx="22" fill="url(#parchmentBg)" />
    <rect x="12" y="12" width="836" height="476" fill="url(#linenGrid)" />
    <rect x="12" y="12" width="836" height="476" fill="url(#sunlightGlow)" />
    <rect x="12" y="12" width="836" height="476" fill="url(#meadowGlow)" />

    <!-- Inner Vintage Stitched Border -->
    <rect x="20" y="20" width="820" height="460" rx="16" fill="none" stroke="#C7B69E" stroke-width="1.2" stroke-dasharray="5 4" />

    <!-- Top Sage Botanical Header Banner -->
    <rect x="12" y="12" width="836" height="60" fill="url(#sageHeader)" />
    <line x1="12" y1="72" x2="848" y2="72" stroke="#D49B54" stroke-width="2" />
    <line x1="12" y1="75" x2="848" y2="75" stroke="#8C6D46" stroke-width="0.7" stroke-dasharray="3 3" />

    <!-- Header Left: Botanical Leaf Emblem + Guild Title -->
    <g transform="translate(36, 26)">
      <!-- Hand-drawn Oak/Sage Sprig Icon -->
      <path d="M4 26 C8 16, 16 8, 26 4 C22 14, 15 22, 4 26 Z" fill="#E9DFC9" />
      <path d="M4 26 C12 24, 20 16, 26 4" fill="none" stroke="#4A6B53" stroke-width="1.3" />
      <circle cx="24" cy="6" r="2.2" fill="#F3C978" />
      <circle cx="9" cy="14" r="1.8" fill="#F3C978" />
      <text x="38" y="13" class="typewriter-xs" fill="#FAF5EB">WOODLAND ATELIER &amp; CODING GUILD // REGISTRY CARD</text>
      <text x="38" y="27" class="serif-italic" fill="#DFD5C0">Folio No. {user_id} • Herbarium Node {node_id}</text>
    </g>

    <!-- Header Right: Cozy Hearth Status Pill -->
    <g transform="translate(642, 28)">
      <rect x="0" y="0" width="176" height="28" rx="14" fill="#3A5441" stroke="#8FA98F" stroke-width="1.2" />
      <circle cx="18" cy="14" r="4.5" fill="#F3C978" class="hearth-pulse" />
      <text x="30" y="18" class="typewriter-xs" fill="#FAF5EB">AT THE HEARTH • COZY</text>
    </g>

    <!-- Decorative Background Botanical Vines (Top-Right & Bottom-Left) -->
    <g class="botanical-sway" opacity="0.28" transform="translate(770, 78)">
      <path d="M40 0 Q20 35 0 65" fill="none" stroke="#5E8C6A" stroke-width="1.8" />
      <path d="M28 18 C15 12, 8 20, 22 26 Z" fill="#5E8C6A" />
      <path d="M18 36 C32 32, 36 42, 20 44 Z" fill="#5E8C6A" />
      <path d="M8 52 C-4 46, -6 56, 6 60 Z" fill="#5E8C6A" />
      <circle cx="0" cy="65" r="4" fill="#D49B54" />
    </g>

    <!-- Floating Golden Pollen / Fireflies -->
    <circle cx="318" cy="112" r="2.5" fill="#D9A441" class="firefly-1" />
    <circle cx="808" cy="272" r="2.2" fill="#D9A441" class="firefly-2" />
    <circle cx="52" cy="410" r="2.4" fill="#D9A441" class="firefly-1" />

    <!-- LEFT COLUMN: Pressed Botanical Portrait & Library Metadata -->
    <rect x="36" y="92" width="268" height="330" rx="14" fill="url(#cardstockPanel)" stroke="#D5C7B2" stroke-width="1.4" />
    <rect x="42" y="98" width="256" height="318" rx="10" fill="none" stroke="#E5DAC8" stroke-width="0.9" />

    <!-- Sage Washi Tape holding the portrait at top -->
    <g transform="translate(115, 94) rotate(-3)">
      <rect x="0" y="0" width="72" height="18" rx="2" fill="url(#washiTape)" stroke="#8FA98F" stroke-width="0.6" stroke-dasharray="2 2" />
      <line x1="8" y1="0" x2="8" y2="18" stroke="#FAF5EB" stroke-width="0.8" stroke-opacity="0.5" />
      <line x1="24" y1="0" x2="24" y2="18" stroke="#FAF5EB" stroke-width="0.8" stroke-opacity="0.5" />
      <line x1="40" y1="0" x2="40" y2="18" stroke="#FAF5EB" stroke-width="0.8" stroke-opacity="0.5" />
      <line x1="56" y1="0" x2="56" y2="18" stroke="#FAF5EB" stroke-width="0.8" stroke-opacity="0.5" />
    </g>

    <!-- Botanical Laurel Wreath & Cameo Frame Around Avatar -->
    <circle cx="150" cy="182" r="74" fill="none" stroke="#8FA98F" stroke-width="1.4" stroke-dasharray="6 4" />
    <circle cx="150" cy="182" r="70" fill="#EFE5D4" stroke="#B8A68E" stroke-width="1.6" />
    {avatar_element}

    <!-- Left & Right Pressed Fern Sprigs hugging the Cameo -->
    <path d="M74 205 C64 185, 66 160, 78 140" fill="none" stroke="#5E8C6A" stroke-width="1.5" />
    <ellipse cx="68" cy="188" rx="6" ry="3" transform="rotate(-35 68 188)" fill="#6B8E73" />
    <ellipse cx="67" cy="170" rx="6" ry="3" transform="rotate(-15 67 170)" fill="#6B8E73" />
    <ellipse cx="72" cy="152" rx="5.5" ry="2.8" transform="rotate(10 72 152)" fill="#6B8E73" />

    <path d="M226 205 C236 185, 234 160, 222 140" fill="none" stroke="#5E8C6A" stroke-width="1.5" />
    <ellipse cx="232" cy="188" rx="6" ry="3" transform="rotate(35 232 188)" fill="#6B8E73" />
    <ellipse cx="233" cy="170" rx="6" ry="3" transform="rotate(15 233 170)" fill="#6B8E73" />
    <ellipse cx="228" cy="152" rx="5.5" ry="2.8" transform="rotate(-10 228 152)" fill="#6B8E73" />

    <!-- Terracotta Wax Seal Stamp on Portrait Corner -->
    <g transform="translate(192, 224)">
      <circle cx="18" cy="18" r="18" fill="url(#waxSealGrad)" />
      <circle cx="18" cy="18" r="13.5" fill="none" stroke="#F4C7B8" stroke-width="0.9" stroke-dasharray="3 2" />
      <!-- Tiny Wildflower inside Wax Seal -->
      <circle cx="18" cy="18" r="2.6" fill="#FDE68A" />
      <circle cx="18" cy="12" r="2.2" fill="#FAF5EB" fill-opacity="0.85" />
      <circle cx="18" cy="24" r="2.2" fill="#FAF5EB" fill-opacity="0.85" />
      <circle cx="12" cy="18" r="2.2" fill="#FAF5EB" fill-opacity="0.85" />
      <circle cx="24" cy="18" r="2.2" fill="#FAF5EB" fill-opacity="0.85" />
    </g>

    <!-- Name & Handle in Warm Espresso Ink -->
    <text x="170" y="286" text-anchor="middle" class="serif-title" fill="#3A2E28">{display_name}</text>
    <text x="170" y="306" text-anchor="middle" class="serif-italic" fill="#5E8C6A">@{login} • Guild Member</text>

    <!-- Decorative Divider with Chamomile Bud -->
    <line x1="60" y1="320" x2="156" y2="320" stroke="#D5C7B2" stroke-width="1" />
    <circle cx="170" cy="320" r="3.5" fill="#D49B54" />
    <circle cx="170" cy="320" r="1.5" fill="#FAF5EB" />
    <line x1="184" y1="320" x2="280" y2="320" stroke="#D5C7B2" stroke-width="1" />

    <!-- Cottage Ledger Entries -->
    <text x="58" y="344" class="typewriter-xs" fill="#8C7765">PLANTED ON</text>
    <text x="282" y="344" text-anchor="end" class="typewriter-sm" fill="#3A2E28">{issued_date}</text>

    <text x="58" y="368" class="typewriter-xs" fill="#8C7765">SEASONS</text>
    <text x="282" y="368" text-anchor="end" class="typewriter-sm" fill="#5E8C6A">{uptime_str}</text>

    <text x="58" y="392" class="typewriter-xs" fill="#8C7765">DWELLING</text>
    <text x="282" y="392" text-anchor="end" class="typewriter-sm" fill="#6E5A4C">{location}</text>

    <!-- RIGHT COLUMN: Field Notes, Apothecary Stat Tickets & Herbarium -->
    <!-- Journal Entry Box -->
    <rect x="324" y="92" width="496" height="92" rx="14" fill="url(#cardstockPanel)" stroke="#D5C7B2" stroke-width="1.4" />
    <!-- Corner Brass Pin -->
    <circle cx="340" cy="108" r="3.2" fill="#D49B54" stroke="#8C6D46" stroke-width="0.8" />
    <circle cx="804" cy="108" r="3.2" fill="#D49B54" stroke="#8C6D46" stroke-width="0.8" />

    <text x="352" y="114" class="typewriter-xs" fill="#B85A43">CRAFT &amp; CALLING // FIELD NOTES</text>
    <text x="344" y="135" class="serif-role" fill="#3A2E28">{role}</text>
    <text x="344" y="155" class="serif-bio" fill="#6E5A4C">“{bio_lines[0]}</text>
    <text x="344" y="172" class="serif-bio" fill="#6E5A4C">{bio_lines[1]}”</text>

    <!-- 4 Apothecary / Seed Packet Stat Labels -->
    <g transform="translate(324, 196)">
      <!-- Ticket 1: Repos -->
      <rect x="0" y="0" width="115" height="74" rx="12" fill="url(#cardstockPanel)" stroke="#D5C7B2" stroke-width="1.3" />
      <rect x="6" y="6" width="103" height="62" rx="8" fill="none" stroke="#E5DAC8" stroke-width="0.8" />
      <circle cx="98" cy="18" r="4" fill="#5E8C6A" fill-opacity="0.25" />
      <path d="M95 21 C97 16, 100 15, 102 14" stroke="#5E8C6A" stroke-width="1.2" fill="none" />
      <text x="16" y="25" class="typewriter-xs" fill="#8C7765">NOTEBOOKS</text>
      <text x="16" y="55" class="serif-stat" fill="#3A2E28">{repos_val}</text>

      <!-- Ticket 2: Stars -->
      <rect x="127" y="0" width="115" height="74" rx="12" fill="url(#cardstockPanel)" stroke="#D5C7B2" stroke-width="1.3" />
      <rect x="133" y="6" width="103" height="62" rx="8" fill="none" stroke="#E5DAC8" stroke-width="0.8" />
      <circle cx="225" cy="18" r="4.5" fill="#D9A441" fill-opacity="0.3" />
      <circle cx="225" cy="18" r="2" fill="#D9A441" />
      <text x="143" y="25" class="typewriter-xs" fill="#8C7765">WILDFLOWERS</text>
      <text x="143" y="55" class="serif-stat" fill="#B87D2B">{stars_val}</text>

      <!-- Ticket 3: Followers -->
      <rect x="254" y="0" width="115" height="74" rx="12" fill="url(#cardstockPanel)" stroke="#D5C7B2" stroke-width="1.3" />
      <rect x="260" y="6" width="103" height="62" rx="8" fill="none" stroke="#E5DAC8" stroke-width="0.8" />
      <circle cx="352" cy="18" r="4" fill="#C47457" fill-opacity="0.25" />
      <text x="270" y="25" class="typewriter-xs" fill="#8C7765">KINDRED</text>
      <text x="270" y="55" class="serif-stat" fill="#4A6B53">{followers_val}</text>

      <!-- Ticket 4: Forks -->
      <rect x="381" y="0" width="115" height="74" rx="12" fill="url(#cardstockPanel)" stroke="#D5C7B2" stroke-width="1.3" />
      <rect x="387" y="6" width="103" height="62" rx="8" fill="none" stroke="#E5DAC8" stroke-width="0.8" />
      <circle cx="479" cy="18" r="4" fill="#8E7394" fill-opacity="0.25" />
      <text x="397" y="25" class="typewriter-xs" fill="#8C7765">CUTTINGS</text>
      <text x="397" y="55" class="serif-stat" fill="#7A5C75">{forks_val}</text>
    </g>

    <!-- Herbarium Specimen Language Bar -->
    <rect x="324" y="282" width="496" height="86" rx="14" fill="url(#cardstockPanel)" stroke="#D5C7B2" stroke-width="1.4" />
    <text x="344" y="298" class="typewriter-xs" fill="#6E5A4C">HERBARIUM SPECIMENS // CRAFT &amp; LANGUAGES</text>

    <rect x="343" y="304" width="458" height="13" rx="6.5" fill="none" stroke="#D5C7B2" stroke-width="1" />
    <g clip-path="url(#langBarClip)">
      {lang_rects_svg}
    </g>
    {lang_legends_svg}

    <!-- Cozy Postscript / Typewriter Note Ribbon -->
    <rect x="324" y="378" width="496" height="44" rx="11" fill="#EFE5D4" stroke="#C7B69E" stroke-width="1.2" />
    <!-- Vintage Quill / Tea Cup Motif -->
    <g transform="translate(340, 390)">
      <path d="M2 14 C2 6, 12 2, 18 2 C16 8, 12 14, 2 14 Z" fill="#5E8C6A" />
      <path d="M0 16 L6 12" stroke="#8C5E45" stroke-width="1.5" stroke-linecap="round" />
    </g>
    <text x="368" y="405" class="serif-italic" fill="#4A3B32">
      “Inked &amp; tended automatically by the woodland courier — all tallies verified.”
    </text>
    <text x="804" y="404" text-anchor="end" class="typewriter-xs" fill="#5E8C6A">[SEALED ✓]</text>

    <!-- Footer: Library Postmark & Botanical Barcode -->
    <line x1="36" y1="432" x2="820" y2="432" stroke="#D5C7B2" stroke-width="1" />
    <text x="38" y="450" class="typewriter-xs" fill="#7D6B5D">POSTMARKED BY GITHUB ACTIONS • WOODLAND PARCEL SERVICE</text>
    <text x="38" y="465" class="serif-italic" fill="#8C7765">Last pressed: {synced_at} • github.com/{login}</text>

    <!-- Herbarium Stem Barcode -->
    {barcode_svg}
  </g>

  <!-- Outer Warm Walnut & Sage Frame -->
  <rect x="12" y="12" width="836" height="476" rx="22" fill="none" stroke="#8C6D46" stroke-width="2.2" />

  <!-- Corner Botanical Flourishes -->
  <path d="M 12 42 V 28 A 16 16 0 0 1 28 12 H 44" fill="none" stroke="#D49B54" stroke-width="2.8" stroke-linecap="round" />
  <path d="M 848 42 V 28 A 16 16 0 0 0 832 12 H 816" fill="none" stroke="#D49B54" stroke-width="2.8" stroke-linecap="round" />
  <path d="M 12 458 V 472 A 16 16 0 0 0 28 488 H 44" fill="none" stroke="#5E8C6A" stroke-width="2.8" stroke-linecap="round" />
  <path d="M 848 458 V 472 A 16 16 0 0 1 832 488 H 816" fill="none" stroke="#5E8C6A" stroke-width="2.8" stroke-linecap="round" />
</svg>
"""


def main() -> None:
    username = os.environ.get("GITHUB_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or DEFAULT_USERNAME
    token = os.environ.get("GITHUB_TOKEN")
    data = collect_profile_data(username, token)
    svg_content = render_svg(data)
    OUTPUT_PATH.write_text(svg_content, encoding="utf-8")
    print(f"Generated cottagecore {OUTPUT_PATH} for @{data['login']} (ID #{data['id']})")


if __name__ == "__main__":
    main()
