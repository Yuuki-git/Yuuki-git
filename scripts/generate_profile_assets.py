#!/usr/bin/env python3
"""Generate minimalist dark/light GitHub telemetry SVG strips for Yuuki-git."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
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
        "bg": "#0d1117",
        "surface": "#161b22",
        "border": "#21262d",
        "text_primary": "#f0f6fc",
        "text_secondary": "#9198a1",
        "text_muted": "#6e7681",
        "accent": "#e3b341",
        "heatmap": ["#161b22", "#3b2f13", "#6e5619", "#a88323", "#e3b341"],
        "heatmap_stroke": "#21262d",
    },
    "light": {
        "bg": "#ffffff",
        "surface": "#f6f8fa",
        "border": "#e5e7eb",
        "text_primary": "#111827",
        "text_secondary": "#4b5563",
        "text_muted": "#6b7280",
        "accent": "#9a6700",
        "heatmap": ["#f3f4f6", "#fde68a", "#f59e0b", "#d97706", "#9a6700"],
        "heatmap_stroke": "#e5e7eb",
    },
}


def http_request(
    url: str,
    *,
    accept: str = "application/vnd.github+json",
    body: dict[str, Any] | None = None,
) -> str:
    headers = {
        "User-Agent": "Yuuki-git-profile-generator/2.0",
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
        "created_year": int(user["createdAt"][:4]),
        "total_contribs": total_contribs,
        "grid": grid,
        "lang_totals": lang_totals,
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
    return {
        "username": username,
        "public_repos": int(user.get("public_repos", len(repos))),
        "owned_repos_count": len(owned_repos),
        "created_year": int(user["created_at"][:4]) if user.get("created_at") else 2020,
        "total_contribs": total_contribs,
        "grid": grid,
        "lang_totals": lang_totals,
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

    # Compact KPI row (left side: x=24..456)
    kpis = [
        (str(data["public_repos"]), "repos"),
        (str(data["owned_repos_count"]), "original"),
        (str(data["total_contribs"]), "contribs / 1y"),
        (str(data["created_year"]), "since"),
    ]
    kpi_svg: list[str] = []
    for idx, (val, label) in enumerate(kpis):
        kx = 24 + idx * 108
        kpi_svg.append(
            f'<text x="{kx}" y="60" fill="{t["text_primary"]}" font-family="\'Consolas\',\'SFMono-Regular\',monospace" font-size="16" font-weight="700">{html.escape(val)}</text>'
            f'<text x="{kx}" y="74" fill="{t["text_muted"]}" font-family="\'Segoe UI\',-apple-system,sans-serif" font-size="10">{html.escape(label)}</text>'
        )

    # Compact 51-week heatmap (x=24..328, y=88..121; cell 4px, pitch 6px/5px)
    heatmap_svg: list[str] = []
    for w_idx, col in enumerate(data["grid"]):
        cx = 24 + w_idx * 6
        for d_idx, level in enumerate(col):
            if level is None:
                continue
            cy = 86 + d_idx * 5
            lvl = max(0, min(4, level))
            fill = t["heatmap"][lvl]
            stroke_attr = f' stroke="{t["heatmap_stroke"]}" stroke-width="0.4"' if lvl == 0 else ""
            heatmap_svg.append(
                f'<rect x="{cx}" y="{cy}" width="4" height="4" rx="1" fill="{fill}"{stroke_attr}/>'
            )

    legend_svg: list[str] = []
    for lvl in range(5):
        lx = 398 + lvl * 6
        stroke_attr = f' stroke="{t["heatmap_stroke"]}" stroke-width="0.4"' if lvl == 0 else ""
        legend_svg.append(
            f'<rect x="{lx}" y="114" width="4" height="4" rx="1" fill="{t["heatmap"][lvl]}"{stroke_attr}/>'
        )

    # Stacked language bar (right side: x=508..856, width=348)
    bar_width = 348.0
    bar_segments: list[str] = []
    cur_x = 508.0
    for idx, lang in enumerate(langs):
        seg_w = bar_width * (lang["pct"] / 100.0)
        if idx == len(langs) - 1:
            seg_w = max(0.0, 508.0 + bar_width - cur_x)
        if seg_w > 0.3:
            bar_segments.append(
                f'<rect x="{cur_x:.2f}" y="50" width="{seg_w:.2f}" height="7" fill="{lang["color"]}"/>'
            )
            cur_x += seg_w

    # 2x3 compact language breakdown
    lang_items_svg: list[str] = []
    for idx, lang in enumerate(langs[:6]):
        col = idx % 2
        row = idx // 2
        lx = 508 + col * 188
        ly = 78 + row * 19
        lang_items_svg.append(
            f'<circle cx="{lx + 3.5}" cy="{ly - 3.5}" r="3.5" fill="{lang["color"]}"/>'
            f'<text x="{lx + 12}" y="{ly}" fill="{t["text_secondary"]}" font-family="\'Segoe UI\',-apple-system,sans-serif" font-size="11" font-weight="600">{html.escape(lang["name"])}</text>'
            f'<text x="{lx + 160}" y="{ly}" text-anchor="end" fill="{t["text_muted"]}" font-family="\'Consolas\',\'SFMono-Regular\',monospace" font-size="10.5">{lang["pct"]:.1f}%</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 138" width="880" height="138" role="img" aria-label="GitHub telemetry strip for {html.escape(data['username'])}">
  <defs>
    <clipPath id="lang-clip-{uid}">
      <rect x="508" y="50" width="348" height="7" rx="3.5"/>
    </clipPath>
  </defs>

  <rect x="1" y="1" width="878" height="136" rx="12" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1"/>

  <!-- Left: Minimal Metrics + 51W Ribbon -->
  <text x="24" y="32" fill="{t['accent']}" font-family="'Consolas','SFMono-Regular',monospace" font-size="10.5" font-weight="700" letter-spacing="0.8">ACTIVITY</text>
  <text x="456" y="32" text-anchor="end" fill="{t['text_muted']}" font-family="'Consolas','SFMono-Regular',monospace" font-size="10">Updated {html.escape(data['generated_date'])} UTC</text>

  {''.join(kpi_svg)}
  <g>{''.join(heatmap_svg)}</g>

  <text x="392" y="118" text-anchor="end" fill="{t['text_muted']}" font-family="'Segoe UI',-apple-system,sans-serif" font-size="9.5">Less</text>
  <g>{''.join(legend_svg)}</g>
  <text x="433" y="118" fill="{t['text_muted']}" font-family="'Segoe UI',-apple-system,sans-serif" font-size="9.5">More</text>

  <!-- Vertical Divider -->
  <line x1="484" y1="22" x2="484" y2="116" stroke="{t['border']}" stroke-width="1"/>

  <!-- Right: Language Footprint -->
  <text x="508" y="32" fill="{t['accent']}" font-family="'Consolas','SFMono-Regular',monospace" font-size="10.5" font-weight="700" letter-spacing="0.8">LANGUAGES</text>
  <text x="856" y="32" text-anchor="end" fill="{t['text_muted']}" font-family="'Consolas','SFMono-Regular',monospace" font-size="10">Active originals</text>

  <rect x="508" y="50" width="348" height="7" rx="3.5" fill="{t['surface']}"/>
  <g clip-path="url(#lang-clip-{uid})">
    {''.join(bar_segments)}
  </g>
  <g>{''.join(lang_items_svg)}</g>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate minimalist GitHub telemetry SVGs.")
    parser.add_argument("--snapshot", type=Path, default=None, help="Optional pre-fetched JSON file.")
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
        print(f"Generated {out_path} ({data['total_contribs']} contribs, {data['public_repos']} public repos)")


if __name__ == "__main__":
    main()
