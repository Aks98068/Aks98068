#!/usr/bin/env python3
"""Render animated SVG cards for the Aks98068 GitHub profile README.

Requires Python 3.11+ and a GitHub token with read access to public profile data.
Run: python scripts/render_readme_cards.py
Static preview: STATIC=1 python scripts/render_readme_cards.py
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
DATA = ROOT / "data"
USERNAME = os.getenv("GITHUB_USERNAME", "Aks98068")
TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
STATIC = os.getenv("STATIC", "0") == "1"

BG = "#F7F4EE"
PAPER = "#FFFEFA"
INK = "#202124"
MUTED = "#77736C"
LINE = "#E6DED2"
ORANGE = "#F97316"
ORANGE_DARK = "#C94F0B"
ORANGE_PALE = "#FFF0E3"
GREEN = "#0F766E"


def graphql(query: str) -> dict:
    if not TOKEN:
        raise RuntimeError("Missing GH_TOKEN. Set GH_TOKEN or GITHUB_TOKEN before running.")
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Aks98068-profile-card-renderer",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}: {detail}") from exc
    if result.get("errors"):
        raise RuntimeError("GitHub GraphQL error: " + json.dumps(result["errors"]))
    return result["data"]


def fetch_data() -> dict:
    query = f"""
    query {{
      user(login: "{USERNAME}") {{
        name
        login
        contributionsCollection(from: "{(date.today()-timedelta(days=365)).isoformat()}T00:00:00Z",
                                to: "{date.today().isoformat()}T23:59:59Z") {{
          contributionCalendar {{
            totalContributions
            weeks {{
              contributionDays {{ date contributionCount weekday }}
            }}
          }}
        }}
        pinnedItems(first: 4, types: REPOSITORY) {{
          nodes {{
            ... on Repository {{
              name
              description
              url
              stargazerCount
              primaryLanguage {{ name color }}
            }}
          }}
        }}
      }}
    }}
    """
    user = graphql(query)["user"]
    calendar_data = user["contributionsCollection"]["contributionCalendar"]
    days = [day for week in calendar_data["weeks"] for day in week["contributionDays"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "username": user["login"],
        "name": user.get("name") or "Abhishekh Kumar Sah",
        "total_contributions": calendar_data["totalContributions"],
        "days": days,
        "pinned_repositories": user["pinnedItems"]["nodes"],
    }


def stats(data: dict) -> dict:
    days = data["days"]
    active = [d for d in days if d["contributionCount"] > 0]
    best = max(days, key=lambda d: d["contributionCount"], default={"date": "", "contributionCount": 0})
    streak = longest = 0
    previous = None
    for item in days:
        current = date.fromisoformat(item["date"])
        if item["contributionCount"]:
            if previous and current == previous + timedelta(days=1):
                streak += 1
            else:
                streak = 1
            longest = max(longest, streak)
        else:
            streak = 0
        previous = current

    monthly = defaultdict(int)
    for item in days:
        monthly[item["date"][:7]] += item["contributionCount"]
    last_months = []
    today = date.today().replace(day=1)
    for offset in range(11, -1, -1):
        month_index = today.month - 1 - offset
        year = today.year + month_index // 12
        month = month_index % 12 + 1
        key = f"{year:04d}-{month:02d}"
        last_months.append({"key": key, "label": calendar.month_abbr[month], "count": monthly[key]})
    weekdays = defaultdict(int)
    for item in active:
        weekdays[date.fromisoformat(item["date"]).strftime("%A")] += item["contributionCount"]
    busiest = max(weekdays, key=weekdays.get) if weekdays else "—"
    return {
        "active_days": len(active),
        "longest_streak": longest,
        "busiest_day": busiest,
        "busiest_day_count": weekdays.get(busiest, 0),
        "best_date": best["date"],
        "best_count": best["contributionCount"],
        "months": last_months,
    }


def animation_css(delay: float = 0) -> str:
    if STATIC:
        return ""
    return f"""
    <style>
      @keyframes rise {{ from {{ opacity:0; transform:translateY(16px); }} to {{ opacity:1; transform:translateY(0); }} }}
      @keyframes grow {{ from {{ transform:scaleY(.05); opacity:.25; }} to {{ transform:scaleY(1); opacity:1; }} }}
      @keyframes sweep {{ 0%,65% {{ transform:translateX(-160%); }} 100% {{ transform:translateX(260%); }} }}
      @keyframes pulse {{ 0%,100% {{ opacity:.35; }} 50% {{ opacity:1; }} }}
      .enter {{ animation:rise .8s cubic-bezier(.2,.8,.2,1) both; animation-delay:{delay}s; }}
      .bar {{ transform-box:fill-box; transform-origin:bottom; animation:grow .75s ease-out both; }}
      .shine {{ animation:sweep 5s ease-in-out infinite; }}
      .pulse {{ animation:pulse 2s ease-in-out infinite; }}
      @media (prefers-reduced-motion: reduce) {{
        *,*::before,*::after {{ animation:none !important; transition:none !important; }}
      }}
    </style>"""


def svg_start(width: int, height: int, delay: float = 0) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img">{animation_css(delay)}')


def write_card(name: str, content: str) -> None:
    (CARDS / name).write_text(content + "</svg>\n", encoding="utf-8")


def hero(data: dict) -> None:
    name = escape(data["name"])
    content = svg_start(1100, 270, 0)
    content += f"""
    <rect width="1100" height="270" rx="22" fill="{BG}"/>
    <rect x="28" y="28" width="1044" height="214" rx="16" fill="{PAPER}" stroke="{LINE}"/>
    <path d="M850 28H1056Q1072 28 1072 44V226Q1072 242 1056 242H930Z" fill="{ORANGE_PALE}"/>
    <circle cx="962" cy="111" r="59" fill="none" stroke="{ORANGE}" stroke-width="1.5" opacity=".45"/>
    <circle cx="962" cy="111" r="42" fill="none" stroke="{ORANGE}" stroke-width="1" opacity=".35"/>
    <path d="M962 38V184M889 111H1035" stroke="{ORANGE}" opacity=".18"/>
    <g class="enter">
      <text x="76" y="83" fill="{ORANGE_DARK}" font-family="Arial,sans-serif" font-size="14" font-weight="700" letter-spacing="3">CYBERSECURITY / DIGITAL FORENSICS</text>
      <text x="72" y="151" fill="{INK}" font-family="Georgia,serif" font-size="53">{name}</text>
      <text x="76" y="190" fill="{MUTED}" font-family="Arial,sans-serif" font-size="17">Security researcher · Go developer · Software builder</text>
      <text x="76" y="218" fill="{ORANGE_DARK}" font-family="Arial,sans-serif" font-size="12" letter-spacing="2">INVESTIGATE  /  BUILD  /  SECURE</text>
    </g>
    <rect x="914" y="63" width="96" height="96" rx="48" fill="{ORANGE}" opacity=".10"/>
    <path d="M962 74l28 11v23c0 20-13 34-28 42-15-8-28-22-28-42V85z" fill="none" stroke="{ORANGE_DARK}" stroke-width="3"/>
    <path d="M949 108l9 9 18-21" fill="none" stroke="{ORANGE_DARK}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    """
    write_card("hero.svg", content)


def tile(name: str, eyebrow: str, title: str, desc: str, number: str, accent: str) -> None:
    content = svg_start(350, 150, 0.35)
    content += f"""
    <rect x="1" y="1" width="348" height="148" rx="15" fill="{PAPER}" stroke="{LINE}"/>
    <rect x="1" y="1" width="7" height="148" rx="3" fill="{accent}"/>
    <g class="enter">
      <text x="27" y="34" fill="{MUTED}" font-family="Arial,sans-serif" font-size="11" font-weight="700" letter-spacing="2">{escape(eyebrow)}</text>
      <text x="27" y="76" fill="{INK}" font-family="Georgia,serif" font-size="29">{escape(title)}</text>
      <text x="27" y="103" fill="{MUTED}" font-family="Arial,sans-serif" font-size="13">{escape(desc)}</text>
      <text x="305" y="40" fill="{accent}" font-family="Arial,sans-serif" font-size="16" font-weight="700">{number}</text>
      <path d="M300 119h20m-8-8 8 8-8 8" fill="none" stroke="{accent}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </g>
    """
    write_card(name, content)


def activity(data: dict, calculated: dict) -> None:
    months = calculated["months"]
    max_value = max((m["count"] for m in months), default=1) or 1
    content = svg_start(1100, 310, 0.6)
    content += f"""
    <rect x="1" y="1" width="1098" height="308" rx="18" fill="{PAPER}" stroke="{LINE}"/>
    <text x="34" y="43" fill="{INK}" font-family="Georgia,serif" font-size="26">A year of showing up.</text>
    <text x="35" y="68" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">MONTHLY CONTRIBUTIONS · LAST 12 MONTHS</text>
    <text x="35" y="125" fill="{ORANGE_DARK}" font-family="Georgia,serif" font-size="42">{data["total_contributions"]:,}</text>
    <text x="36" y="148" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">TOTAL CONTRIBUTIONS</text>
    <text x="260" y="125" fill="{INK}" font-family="Georgia,serif" font-size="32">{calculated["active_days"]}</text>
    <text x="260" y="148" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">ACTIVE DAYS</text>
    <text x="435" y="125" fill="{INK}" font-family="Georgia,serif" font-size="32">{calculated["longest_streak"]}</text>
    <text x="435" y="148" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">LONGEST STREAK · DAYS</text>
    <text x="675" y="125" fill="{INK}" font-family="Georgia,serif" font-size="25">{escape(calculated["busiest_day"])}</text>
    <text x="675" y="148" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">BUSIEST WEEKDAY</text>
    <line x1="34" y1="171" x2="1066" y2="171" stroke="{LINE}"/>
    """
    x0, base, bar_w, gap = 42, 260, 48, 34
    for i, month in enumerate(months):
        height = max(3, 67 * month["count"] / max_value)
        x = x0 + i * (bar_w + gap)
        color = ORANGE if month["count"] == max_value and max_value > 0 else "#E8B18D"
        content += f'<rect class="bar" style="animation-delay:{0.75+i*.045:.2f}s" x="{x}" y="{base-height:.1f}" width="{bar_w}" height="{height:.1f}" rx="5" fill="{color}"/>'
        content += f'<text x="{x+bar_w/2}" y="284" text-anchor="middle" fill="{MUTED}" font-family="Arial,sans-serif" font-size="11">{month["label"]}</text>'
    content += f'<text x="1064" y="43" text-anchor="end" fill="{MUTED}" font-family="Arial,sans-serif" font-size="11">UPDATED {escape(data["generated_at"][:10])}</text>'
    write_card("activity.svg", content)


def heatmap(data: dict) -> None:
    days = data["days"]
    content = svg_start(1100, 190, 0.95)
    content += f"""
    <rect x="1" y="1" width="1098" height="188" rx="18" fill="{PAPER}" stroke="{LINE}"/>
    <text x="34" y="39" fill="{INK}" font-family="Georgia,serif" font-size="24">Consistency, in colour.</text>
    <text x="35" y="61" fill="{MUTED}" font-family="Arial,sans-serif" font-size="11" letter-spacing="1">DAILY CONTRIBUTIONS · ORANGE EDITION</text>
    """
    start_x, start_y, cell, gap = 35, 83, 11, 4
    for i, item in enumerate(days):
        col, row = i // 7, i % 7
        count = item["contributionCount"]
        if count == 0:
            fill = "#F0ECE5"
        elif count <= 2:
            fill = "#FBD7C0"
        elif count <= 5:
            fill = "#F8B184"
        elif count <= 9:
            fill = "#F97316"
        else:
            fill = "#B9470B"
        x, y = start_x + col * (cell + gap), start_y + row * (cell + gap)
        content += f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fill}"><title>{item["date"]}: {count} contributions</title></rect>'
    content += f"""
    <text x="35" y="174" fill="{MUTED}" font-family="Arial,sans-serif" font-size="10">LESS</text>
    """
    for i, color in enumerate(["#F0ECE5", "#FBD7C0", "#F8B184", "#F97316", "#B9470B"]):
        content += f'<rect x="{930+i*17}" y="164" width="12" height="12" rx="2" fill="{color}"/>'
    content += '<text x="1020" y="174" fill="#77736C" font-family="Arial,sans-serif" font-size="10">MORE</text>'
    write_card("heatmap.svg", content)


def repo_card(filename: str, repo: dict | None, fallback_title: str, fallback_desc: str) -> None:
    if repo:
        title = repo["name"]
        description = repo.get("description") or "A project from my GitHub workspace."
        language = (repo.get("primaryLanguage") or {}).get("name") or "Open source"
        stars = repo.get("stargazerCount", 0)
        url = repo.get("url", f"https://github.com/{USERNAME}")
    else:
        title, description, language, stars, url = fallback_title, fallback_desc, "Explore", 0, f"https://github.com/{USERNAME}?tab=repositories"
    content = svg_start(540, 166, 1.15)
    content += f"""
    <rect x="1" y="1" width="538" height="164" rx="16" fill="{PAPER}" stroke="{LINE}"/>
    <rect x="1" y="1" width="6" height="164" rx="3" fill="{ORANGE}"/>
    <g class="enter">
      <text x="27" y="38" fill="{ORANGE_DARK}" font-family="Arial,sans-serif" font-size="11" font-weight="700" letter-spacing="1.5">{escape(language.upper())}</text>
      <text x="27" y="76" fill="{INK}" font-family="Georgia,serif" font-size="28">{escape(title[:28])}</text>
      <text x="27" y="104" fill="{MUTED}" font-family="Arial,sans-serif" font-size="13">{escape(description[:58])}</text>
      <text x="27" y="137" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">★ {stars}  ·  VIEW REPOSITORY ↗</text>
    </g>
    """
    write_card(filename, content)
    return url


def main() -> None:
    CARDS.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    data = fetch_data()
    calculated = stats(data)
    (DATA / "contributions.json").write_text(
        json.dumps({"profile": data, "summary": calculated}, indent=2), encoding="utf-8"
    )
    hero(data)
    tile("security.svg", "WORLD 01", "Cybersecurity", "Understand. Detect. Defend.", "01", ORANGE)
    tile("forensics.svg", "WORLD 02", "Digital Forensics", "Preserve. Examine. Explain.", "02", GREEN)
    tile("build.svg", "WORLD 03", "Software Development", "Design. Engineer. Ship.", "03", "#52627A")
    activity(data, calculated)
    heatmap(data)
    pinned = data.get("pinned_repositories", [])
    repo_card("repo-1.svg", pinned[0] if len(pinned) > 0 else {
        "name": "Zebra", "description": "Go-based security and reconnaissance toolkit.",
        "primaryLanguage": {"name": "Go"}, "stargazerCount": 0, "url": f"https://github.com/{USERNAME}/zebra"
    }, "Zebra", "Go security and reconnaissance toolkit.")
    repo_card("repo-2.svg", pinned[1] if len(pinned) > 1 else None,
              "More projects", "Explore my cybersecurity, forensics and development work.")
    print(f"Rendered SVG cards for @{USERNAME} in {CARDS}")


if __name__ == "__main__":
    main()
