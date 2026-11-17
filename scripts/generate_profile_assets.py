#!/usr/bin/env python3
"""Generate dark/light GitHub telemetry SVG cards for Yuuki-git's profile README."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

USERNAME = os.getenv("GITHUB_USERNAME", "Yuuki-git")
EXCLUDED_LANGUAGE_REPOS = {USERNAME.lower(), "project"}
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"

LANG_COLORS: dict[str, str] = {
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "C++": "#f34b7d",
    "C": "#555555",
    "Shell": "#89e051",
    "Vue": "#41b883",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Dockerfile": "#384d54",
    "Other": "#8b949e",
}

THEMES: dict[str, dict[str, Any]] = {
    "dark": {
        "bg_start": "#0d1117",
        "bg_end": "#111823",
        "card_bg": "#161b22",
        "tile_bg": "#0d1117",
        "border": "#30363d",
        "text_primary": "#f0f6fc",
        "text_secondary": "#c9d1d9",
        "text_muted": "#8b949e",
        "accent": "#58a6ff",
        "accent_green": "#3fb950",
        "accent_purple": "#d2a8ff",
        "heatmap": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "heatmap_stroke": "#21262d",
    },
    "light": {
        "bg_start": "#ffffff",
        "bg_end": "#f6f8fa",
        "card_bg": "#f6f8fa",
        "tile_bg": "#ffffff",
        "border": "#d0d7de",
        "text_primary": "#1f2328",
        "text_secondary": "#24292f",
        "text_muted": "#57606a",
        "accent": "#0969da",
        "accent_green": "#1a7f37",
        "accent_purple": "#8250df",
        "heatmap": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "heatmap_stroke": "#d8dee4",
    },
}


def http_request(
    url: str,
    *,
    accept: str = "application/vnd.github+json",
    body: dict[str, Any] | None = None,
) -> str:
    headers = {
        "User-Agent": "Yuuki-git-profile-generator/1.0",
        "Accept": accept,
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_contributions(username: str) -> tuple[int, list[list[int | None]]]:
    contrib_html = http_request(
        f"https://github.com/users/{username}/contributions",
        accept="text/html",
    )
    total_match = re.search(
        r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", contrib_html
    )
    total_contribs = int(total_match.group(1).replace(",", "")) if total_match else 0

    day_pairs = re.findall(
        r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"', contrib_html
    )
    day_levels: dict[dt.date, int] = {}
    for date_str, lvl_str in day_pairs:
        day_levels[dt.date.fromisoformat(date_str)] = int(lvl_str)

    today = max(day_levels.keys()) if day_levels else dt.date.today()
    today_sun_idx = (today.weekday() + 1) % 7
    current_week_sunday = today - dt.timedelta(days=today_sun_idx)
    num_weeks = 51
    start_sunday = current_week_sunday - dt.timedelta(weeks=num_weeks - 1)

    grid: list[list[int | None]] = []
    for w in range(num_weeks):
        col: list[int | None] = []
        for d in range(7):
            cur = start_sunday + dt.timedelta(weeks=w, days=d)
            col.append(None if cur > today else day_levels.get(cur, 0))
        grid.append(col)

    return total_contribs, grid


def fetch_via_graphql(username: str) -> dict[str, Any]:
    query = """
    query($login: String!) {
      user(login: $login) {
        createdAt
        allPublic: repositories(privacy: PUBLIC, ownerAffiliations: OWNER) {
          totalCount
        }
        owned: repositories(
          first: 100
          isFork: false
          privacy: PUBLIC
          ownerAffiliations: OWNER
          orderBy: {field: PUSHED_AT, direction: DESC}
        ) {
          nodes {
            name
            pushedAt
            stargazerCount
            primaryLanguage { name }
            languages(first: 15, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node { name }
              }
            }
          }
        }
      }
    }
    """
    raw = http_request(
        "https://api.github.com/graphql",
        body={"query": query, "variables": {"login": username}},
    )
    payload = json.loads(raw)
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")

    user = payload["data"]["user"]
    owned_nodes = [
        n
        for n in user["owned"]["nodes"]
        if n["name"].lower() != username.lower()
    ]
    active_owned = [
        n for n in owned_nodes if n["name"].lower() not in EXCLUDED_LANGUAGE_REPOS
    ]

    lang_totals: dict[str, int] = {}
    for repo in active_owned:
        for edge in repo["languages"]["edges"]:
            lang_name = edge["node"]["name"]
            lang_totals[lang_name] = lang_totals.get(lang_name, 0) + int(edge["size"])

    total_contribs, grid = fetch_contributions(username)
    return {
        "username": username,
        "public_repos": int(user["allPublic"]["totalCount"]),
        "owned_repos_count": len(owned_nodes),
        "total_stars": sum(int(r.get("stargazerCount", 0)) for r in owned_nodes),
        "created_year": int(user["createdAt"][:4]),
        "total_contribs": total_contribs,
        "grid": grid,
        "lang_totals": lang_totals,
        "recent_repos": [
            {
                "name": r["name"],
                "language": (r.get("primaryLanguage") or {}).get("name") or "Code",
                "updated": (r.get("pushedAt") or "")[:7],
            }
            for r in active_owned[:3]
        ],
        "generated_date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
    }


def fetch_via_rest(username: str) -> dict[str, Any]:
    user = json.loads(http_request(f"https://api.github.com/users/{username}"))
    repos = json.loads(
        http_request(
            f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100"
        )
    )

    owned_repos = [
        r for r in repos if not r.get("fork") and r["name"].lower() != username.lower()
    ]
    active_owned = [
        r for r in owned_repos if r["name"].lower() not in EXCLUDED_LANGUAGE_REPOS
    ]

    lang_totals: dict[str, int] = {}
    for repo in active_owned:
        langs = json.loads(http_request(repo["languages_url"]))
        for lang, size in langs.items():
            lang_totals[lang] = lang_totals.get(lang, 0) + int(size)

    total_contribs, grid = fetch_contributions(username)
    recent_repos = sorted(
        active_owned,
        key=lambda r: r.get("pushed_at") or r.get("updated_at") or "",
        reverse=True,
    )[:3]

    return {
        "username": username,
        "public_repos": int(user.get("public_repos", len(repos))),
        "owned_repos_count": len(owned_repos),
        "total_stars": sum(int(r.get("stargazers_count", 0)) for r in owned_repos),
        "created_year": int(user["created_at"][:4]) if user.get("created_at") else 2020,
        "total_contribs": total_contribs,
        "grid": grid,
        "lang_totals": lang_totals,
        "recent_repos": [
            {
                "name": r["name"],
                "language": r.get("language") or "Code",
                "updated": (r.get("pushed_at") or r.get("updated_at") or "")[:7],
            }
            for r in recent_repos
        ],
        "generated_date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
    }


def fetch_github_data(username: str) -> dict[str, Any]:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        try:
            return fetch_via_graphql(username)
        except Exception as exc:
            print(f"GraphQL fallback to REST due to: {exc}")
    return fetch_via_rest(username)


def prepare_languages(lang_totals: dict[str, int], max_items: int = 5) -> list[dict[str, Any]]:
    total_bytes = sum(lang_totals.values())
    if total_bytes <= 0:
        return [{"name": "Python", "pct": 100.0, "color": LANG_COLORS["Python"]}]

    sorted_langs = sorted(lang_totals.items(), key=lambda item: -item[1])
    top = sorted_langs[:max_items]
    rest_bytes = sum(size for _, size in sorted_langs[max_items:])

    result: list[dict[str, Any]] = []
    for name, size in top:
        result.append(
            {
                "name": name,
                "pct": size * 100.0 / total_bytes,
                "color": LANG_COLORS.get(name, LANG_COLORS["Other"]),
            }
        )
    if rest_bytes > 0:
        result.append(
            {
                "name": "Other",
                "pct": rest_bytes * 100.0 / total_bytes,
                "color": LANG_COLORS["Other"],
            }
        )
    return result


def render_svg(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    langs = prepare_languages(data["lang_totals"], max_items=5)
    uid = theme_name

    kpis = [
        ("Public Repos", str(data["public_repos"]), t["accent"]),
        ("Original", str(data["owned_repos_count"]), t["accent_green"]),
        ("1Y Contribs", str(data["total_contribs"]), t["accent_purple"]),
        ("Since", str(data["created_year"]), t["text_primary"]),
    ]
    kpi_svg: list[str] = []
    for idx, (label, val, val_color) in enumerate(kpis):
        x = 36 + idx * 104
        kpi_svg.append(
            f'<rect x="{x}" y="62" width="96" height="54" rx="8" fill="{t["tile_bg"]}" stroke="{t["border"]}" stroke-width="1"/>'
            f'<text x="{x + 12}" y="82" fill="{t["text_muted"]}" font-family="\'Segoe UI\',-apple-system,sans-serif" font-size="10.5">{html.escape(label)}</text>'
            f'<text x="{x + 12}" y="105" fill="{val_color}" font-family="\'Consolas\',\'SFMono-Regular\',monospace" font-size="17" font-weight="700">{html.escape(val)}</text>'
        )

    heatmap_svg: list[str] = []
    for w_idx, col in enumerate(data["grid"]):
        cx = 36 + w_idx * 8
        for d_idx, level in enumerate(col):
            if level is None:
                continue
            cy = 152 + d_idx * 8
            lvl = max(0, min(4, level))
            fill = t["heatmap"][lvl]
            stroke_attr = f' stroke="{t["heatmap_stroke"]}" stroke-width="0.5"' if lvl == 0 else ""
            heatmap_svg.append(
                f'<rect x="{cx}" y="{cy}" width="6" height="6" rx="1.4" fill="{fill}"{stroke_attr}/>'
            )

    legend_svg: list[str] = []
    for lvl in range(5):
        lx = 374 + lvl * 8
        stroke_attr = f' stroke="{t["heatmap_stroke"]}" stroke-width="0.5"' if lvl == 0 else ""
        legend_svg.append(
            f'<rect x="{lx}" y="222" width="6" height="6" rx="1.4" fill="{t["heatmap"][lvl]}"{stroke_attr}/>'
        )

    bar_width = 346.0
    bar_segments: list[str] = []
    cur_x = 496.0
    for idx, lang in enumerate(langs):
        seg_w = bar_width * (lang["pct"] / 100.0)
        if idx == len(langs) - 1:
            seg_w = max(0.0, 496.0 + bar_width - cur_x)
        if seg_w > 0.3:
            bar_segments.append(
                f'<rect x="{cur_x:.2f}" y="64" width="{seg_w:.2f}" height="10" fill="{lang["color"]}"/>'
            )
            cur_x += seg_w

    lang_items_svg: list[str] = []
    for idx, lang in enumerate(langs[:6]):
        col = idx % 2
        row = idx // 2
        lx = 496 + col * 188
        ly = 96 + row * 20
        lang_items_svg.append(
            f'<circle cx="{lx + 4}" cy="{ly - 4}" r="4" fill="{lang["color"]}"/>'
            f'<text x="{lx + 14}" y="{ly}" fill="{t["text_secondary"]}" font-family="\'Segoe UI\',-apple-system,sans-serif" font-size="11.5" font-weight="600">{html.escape(lang["name"])}</text>'
            f'<text x="{lx + 158}" y="{ly}" text-anchor="end" fill="{t["text_muted"]}" font-family="\'Consolas\',\'SFMono-Regular\',monospace" font-size="11">{lang["pct"]:.1f}%</text>'
        )

    recent_svg: list[str] = []
    for idx, repo in enumerate(data["recent_repos"]):
        ry = 194 + idx * 20
        r_name = repo["name"]
        if len(r_name) > 22:
            r_name = r_name[:20] + ".."
        r_lang = repo["language"]
        r_color = LANG_COLORS.get(r_lang, LANG_COLORS["Other"])
        recent_svg.append(
            f'<circle cx="500" cy="{ry - 4}" r="3.5" fill="{r_color}"/>'
            f'<text x="510" y="{ry}" fill="{t["text_primary"]}" font-family="\'Consolas\',\'SFMono-Regular\',monospace" font-size="11.5" font-weight="600">{html.escape(r_name)}</text>'
            f'<text x="842" y="{ry}" text-anchor="end" fill="{t["text_muted"]}" font-family="\'Consolas\',\'SFMono-Regular\',monospace" font-size="10.5">{html.escape(r_lang)} · {html.escape(repo["updated"])}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 268" width="880" height="268" role="img" aria-label="GitHub telemetry for {html.escape(data['username'])}">
  <defs>
    <linearGradient id="stats-bg-{uid}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{t['bg_start']}"/>
      <stop offset="100%" stop-color="{t['bg_end']}"/>
    </linearGradient>
    <clipPath id="lang-bar-clip-{uid}">
      <rect x="496" y="64" width="346" height="10" rx="5"/>
    </clipPath>
  </defs>

  <rect x="1" y="1" width="878" height="266" rx="16" fill="url(#stats-bg-{uid})" stroke="{t['border']}" stroke-width="1.2"/>

  <!-- Left Panel: Activity & Heatmap -->
  <rect x="20" y="20" width="444" height="228" rx="12" fill="{t['card_bg']}" fill-opacity="0.72" stroke="{t['border']}" stroke-width="1"/>
  <text x="36" y="46" fill="{t['text_primary']}" font-family="'Segoe UI',-apple-system,sans-serif" font-size="13.5" font-weight="700">GitHub Telemetry</text>
  <text x="444" y="46" text-anchor="end" fill="{t['text_muted']}" font-family="'Consolas','SFMono-Regular',monospace" font-size="11">@{html.escape(data['username'])}</text>

  {''.join(kpi_svg)}

  <text x="36" y="140" fill="{t['text_secondary']}" font-family="'Segoe UI',-apple-system,sans-serif" font-size="11.5" font-weight="600">Contribution Activity (Last 51 Weeks)</text>
  <text x="444" y="140" text-anchor="end" fill="{t['text_muted']}" font-family="'Consolas','SFMono-Regular',monospace" font-size="10.5">{data['total_contribs']} total</text>

  <g>{''.join(heatmap_svg)}</g>

  <text x="36" y="229" fill="{t['text_muted']}" font-family="'Consolas','SFMono-Regular',monospace" font-size="10">Updated {html.escape(data['generated_date'])} UTC</text>
  <text x="368" y="229" text-anchor="end" fill="{t['text_muted']}" font-family="'Segoe UI',-apple-system,sans-serif" font-size="10">Less</text>
  <g>{''.join(legend_svg)}</g>
  <text x="418" y="229" fill="{t['text_muted']}" font-family="'Segoe UI',-apple-system,sans-serif" font-size="10">More</text>

  <!-- Right Panel: Language Footprint & Recent Repos -->
  <rect x="478" y="20" width="382" height="228" rx="12" fill="{t['card_bg']}" fill-opacity="0.72" stroke="{t['border']}" stroke-width="1"/>
  <text x="496" y="46" fill="{t['text_primary']}" font-family="'Segoe UI',-apple-system,sans-serif" font-size="13.5" font-weight="700">Language Footprint</text>
  <text x="842" y="46" text-anchor="end" fill="{t['text_muted']}" font-family="'Consolas','SFMono-Regular',monospace" font-size="10.5">Active originals</text>

  <rect x="496" y="64" width="346" height="10" rx="5" fill="{t['tile_bg']}" stroke="{t['border']}" stroke-width="0.6"/>
  <g clip-path="url(#lang-bar-clip-{uid})">
    {''.join(bar_segments)}
  </g>

  <g>{''.join(lang_items_svg)}</g>

  <line x1="496" y1="152" x2="842" y2="152" stroke="{t['border']}" stroke-width="1"/>
  <text x="496" y="172" fill="{t['text_secondary']}" font-family="'Segoe UI',-apple-system,sans-serif" font-size="11.5" font-weight="700">Recently Updated Repositories</text>

  <g>{''.join(recent_svg)}</g>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate GitHub profile SVG telemetry cards.")
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=None,
        help="Optional pre-fetched JSON data file (used offline or when rate-limited).",
    )
    args = parser.parse_args()

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if args.snapshot is not None:
        data = json.loads(args.snapshot.read_text(encoding="utf-8"))
        if "grid" not in data or "total_contribs" not in data:
            total_contribs, grid = fetch_contributions(data["username"])
            data["total_contribs"] = total_contribs
            data["grid"] = grid
    else:
        data = fetch_github_data(USERNAME)

    for theme in ("dark", "light"):
        out_path = ASSETS_DIR / f"stats-{theme}.svg"
        out_path.write_text(render_svg(data, theme), encoding="utf-8")
        print(
            f"Generated {out_path} ({data['total_contribs']} contribs, {data['public_repos']} public repos)"
        )


if __name__ == "__main__":
    main()
