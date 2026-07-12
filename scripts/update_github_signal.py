from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
import os
import urllib.request

from build_assets import (
    INK_PANEL, LINE, LINE_SOFT, CREAM, PARCHMENT, MUTED, CLAY, CLAY_BRIGHT, CLAY_DIM,
    SAGE, SAGE_BRIGHT, SANS, esc, txt, shell, frame_brackets,
)

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

LANG_COLORS = [CLAY, SAGE, CLAY_BRIGHT, SAGE_BRIGHT, "#B0A695"]


def api(url: str, token: str, payload: dict | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("User-Agent", "yuvraj-profile-signal")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_profile(owner: str, token: str) -> dict:
    query = """
    query($login: String!) {
      user(login: $login) {
        login
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, orderBy: {field: UPDATED_AT, direction: DESC}) {
          totalCount
          nodes { name url isFork stargazerCount forkCount updatedAt primaryLanguage { name } }
        }
        contributionsCollection {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date weekday contributionCount } }
          }
        }
      }
    }
    """
    result = api("https://api.github.com/graphql", token, {"query": query, "variables": {"login": owner}})
    if result.get("errors"):
        raise RuntimeError(result["errors"])
    user = result.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user not found: {owner}")
    return user


def load_events(owner: str, token: str) -> list[dict]:
    return api(f"https://api.github.com/users/{owner}/events/public?per_page=100", token)


def streaks(days: list[dict]) -> tuple[int, int]:
    values = {date.fromisoformat(d["date"]): int(d["contributionCount"]) for d in days}
    if not values:
        return 0, 0
    longest = run = 0
    previous: date | None = None
    for day in sorted(values):
        if values[day] > 0:
            run = run + 1 if previous and day == previous + timedelta(days=1) else 1
            longest = max(longest, run)
        else:
            run = 0
        previous = day
    today = datetime.now(timezone.utc).date()
    pointer = today if values.get(today, 0) else today - timedelta(days=1)
    current = 0
    while values.get(pointer, 0) > 0:
        current += 1
        pointer -= timedelta(days=1)
    return current, longest


def kpi_tile(x: float, y: float, w: float, value: str, label: str, delay: float = 0.0) -> list[str]:
    return [
        f'<g class="rise" style="animation-delay:{delay:.2f}s">',
        f'<rect x="{x}" y="{y}" width="{w}" height="88" rx="8" fill="url(#panelGrad)" stroke="{LINE}"/>',
        txt(x + 16, y + 42, value, 27, CREAM, 800, family=SANS),
        txt(x + 16, y + 68, label, 10.5, MUTED, 650, family=SANS),
        '</g>',
    ]


def sparkline(x: float, y: float, w: float, h: float, weekly: list[int]) -> list[str]:
    if not weekly:
        return [txt(x, y + h / 2, "no recent activity window", 12, MUTED, 600)]
    top = max(weekly) or 1
    n = len(weekly)
    step = w / max(1, n - 1)
    pts = [(x + i * step, y + h - (v / top) * h) for i, v in enumerate(weekly)]
    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = f"{x:.1f},{y+h:.1f} " + line + f" {x+w:.1f},{y+h:.1f}"
    last_x, last_y = pts[-1]
    out = [
        f'<polyline points="{area}" fill="{CLAY}" opacity=".12"/>',
        f'<polyline points="{line}" fill="none" stroke="{CLAY_BRIGHT}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>',
        f'<line x1="{x}" y1="{y+h}" x2="{x+w}" y2="{y+h}" stroke="{LINE_SOFT}"/>',
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="4.5" fill="{CLAY_BRIGHT}"/>',
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="4.5" fill="none" stroke="{CLAY_BRIGHT}" stroke-width="1.4" class="pulse-ring"/>',
    ]
    return out


def language_bar(x: float, y: float, w: float, h: float, languages: list[tuple[str, int]]) -> list[str]:
    total = sum(c for _, c in languages) or 1
    out = []
    cx = x
    legend = []
    for i, (name, count) in enumerate(languages):
        seg_w = w * count / total
        color = LANG_COLORS[i % len(LANG_COLORS)]
        out.append(f'<rect x="{cx:.1f}" y="{y}" width="{max(seg_w,2):.1f}" height="{h}" fill="{color}"/>')
        legend.append((name, count, color))
        cx += seg_w
    ly = y + h + 24
    lx = x
    for name, count, color in legend:
        out.append(f'<circle cx="{lx+5}" cy="{ly-4}" r="4" fill="{color}"/>')
        label = f"{name} ({count})"
        out.append(txt(lx + 16, ly, label, 11.5, PARCHMENT, 600, family=SANS))
        lx += 20 + len(label) * 7.2
    return out


def build_signal_panel(user: dict) -> None:
    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    weeks_raw = calendar["weeks"]
    days = [d for week in weeks_raw for d in week["contributionDays"]]
    current, longest = streaks(days)
    repos = [r for r in user["repositories"]["nodes"] if not r["isFork"] and r["name"] != user["login"]]
    stars = sum(int(r["stargazerCount"]) for r in repos)
    languages = Counter(r["primaryLanguage"]["name"] for r in repos if r.get("primaryLanguage"))
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    weekly = [sum(int(d["contributionCount"]) for d in wk["contributionDays"]) for wk in weeks_raw[-14:]]

    w, h = 1400, 390
    body = [
        txt(28, 34, f"github://signal/@{user['login']}", 13, CLAY, 700),
        txt(1370, 34, updated, 10, MUTED, 600, "end"),
        f'<line x1="28" y1="48" x2="1372" y2="48" stroke="{LINE}"/>',
        frame_brackets(14, 14, w - 28, h - 28, CLAY_DIM, corner=20),
    ]

    tiles = [
        (f"{calendar['totalContributions']:,}", "CONTRIBUTIONS / YR"),
        (f"{current}d", "CURRENT STREAK"),
        (f"{longest}d", "LONGEST STREAK"),
        (f"{user['repositories']['totalCount']}", "PUBLIC REPOS"),
        (f"{stars}", "STARS EARNED"),
        (f"{user['followers']['totalCount']}", "FOLLOWERS"),
    ]
    tile_w, gap, sx, sy = 206, 16, 42, 68
    for i, (value, label) in enumerate(tiles):
        body += kpi_tile(sx + i * (tile_w + gap), sy, tile_w, value, label, delay=0.06 * i)

    body += [
        txt(42, 196, f"$ momentum --weeks {len(weekly)}", 13, SAGE, 800),
        *sparkline(44, 210, 1312, 76, weekly),
    ]

    top_langs = languages.most_common(5)
    body += [txt(42, 328, "$ languages --top 5", 13, SAGE, 800)]
    if top_langs:
        body += language_bar(44, 340, 1312, 14, top_langs)
    else:
        body += [txt(44, 355, "no public repositories with a detected primary language yet", 12, MUTED, 600)]

    (ASSETS / "github-contributions.svg").write_text(
        shell(w, h, "GitHub KPI signal",
              "Real GitHub KPI tiles, a 14-week momentum sparkline and a language mix, generated by GitHub Actions.", body),
        encoding="utf-8",
    )


def event_line(event: dict) -> tuple[str, str] | None:
    typ = event.get("type", "Event")
    repo = event.get("repo", {}).get("name", "unknown")
    payload = event.get("payload", {})
    when = event.get("created_at", "")[:10]
    if typ == "PushEvent":
        count = len(payload.get("commits", []))
        if count == 0:
            return None
        branch = str(payload.get("ref", "")).split("/")[-1]
        return when, f"push {count} commit{'s' if count != 1 else ''} -> {repo}:{branch}"
    if typ == "PullRequestEvent":
        return when, f"pull request {payload.get('action', 'updated')} -> {repo}#{payload.get('number', '?')}"
    if typ == "PullRequestReviewEvent":
        return when, f"review {payload.get('action', 'submitted')} -> {repo}"
    if typ == "IssuesEvent":
        return when, f"issue {payload.get('action', 'updated')} -> {repo}#{payload.get('issue', {}).get('number', '?')}"
    if typ == "CreateEvent":
        return when, f"created {payload.get('ref_type', 'ref')} -> {repo}"
    if typ == "ReleaseEvent":
        tag = payload.get("release", {}).get("tag_name", "release")
        return when, f"released {tag} -> {repo}"
    if typ == "WatchEvent":
        return when, f"starred -> {repo}"
    if typ in ("DeleteEvent", "ForkEvent", "MemberEvent"):
        return None  # housekeeping noise, not engineering signal
    return when, f"{typ.removesuffix('Event').lower()} -> {repo}"


def repo_card(x: float, y: float, w: float, repo: dict, accent: str) -> list[str]:
    h = 64
    lang = (repo.get("primaryLanguage") or {}).get("name") or "—"
    stars = int(repo.get("stargazerCount") or 0)
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="url(#panelGrad)" stroke="{LINE}"/>',
        f'<rect x="{x}" y="{y}" width="4" height="{h}" rx="2" fill="{accent}"/>',
        txt(x + 16, y + 26, repo["name"][:24], 12.5, CREAM, 700, family=SANS),
        f'<circle cx="{x+18}" cy="{y+43}" r="3.5" fill="{accent}"/>',
        txt(x + 28, y + 47, lang, 10.5, MUTED, 600, family=SANS),
    ]
    if stars:
        out.append(txt(x + w - 14, y + 47, f"★ {stars}", 10.5, MUTED, 600, family=SANS, anchor="end"))
    return out


def build_activity(user: dict, events: list[dict]) -> None:
    owner = user["login"]
    profile_repo = f"{owner}/{owner}"
    lines: list[tuple[str, str]] = []
    seen: set[str] = set()
    for event in events:
        if event.get("repo", {}).get("name") == profile_repo:
            continue  # editing this profile repo isn't the engineering signal we're showing
        parsed = event_line(event)
        if parsed is None:
            continue
        when, message = parsed
        key = f"{when}:{message}"
        if key in seen:
            continue
        seen.add(key)
        lines.append((when, message))
        if len(lines) == 6:
            break
    quiet = not lines
    if quiet:
        lines = [("--", "quiet on public channels right now -- most current work is in private repos / on Synvolv")]

    repos = [r for r in user["repositories"]["nodes"] if not r["isFork"] and r["name"] != owner]
    repos = sorted(repos, key=lambda r: r["updatedAt"], reverse=True)[:5]

    w, h = 1400, 420
    body = [
        txt(28, 34, f"github://events/@{owner}?tail=6", 13, CLAY, 700),
        f'<line x1="28" y1="48" x2="1372" y2="48" stroke="{LINE}"/>',
        txt(42, 80, "$ tail -f public-engineering.log", 13, CLAY, 800),
    ]
    y = 112
    for when, message in lines:
        body += [txt(44, y, when, 11, MUTED, 650), txt(160, y, "|", 11, MUTED), txt(186, y, message[:118], 12, PARCHMENT, 600)]
        y += 30
    if quiet:
        body.append(txt(186, y + 4, "the repositories below are where it's actually happening", 11, SAGE_BRIGHT, 600))

    body += [
        txt(42, 296, "$ ls -la ~/repos --recent --updated", 13, SAGE, 800),
        frame_brackets(42, 306, 1316, 90, CLAY_DIM, corner=14),
    ]
    if repos:
        card_w, gap, sx = 246, 17, 42
        accents = [CLAY, SAGE, CLAY_BRIGHT, SAGE_BRIGHT, PARCHMENT]
        for i, repo in enumerate(repos):
            body += repo_card(sx + i * (card_w + gap), 312, card_w, repo, accents[i % len(accents)])
    else:
        body.append(txt(58, 355, "no public repositories yet", 12, MUTED, 600))

    body += [txt(44, 404, "yuvraj@runtime:~$", 11, CLAY, 700), f'<rect x="180" y="391" width="9" height="15" fill="{CLAY_BRIGHT}" class="blink"/>']
    (ASSETS / "github-activity.svg").write_text(
        shell(w, h, "Recent GitHub activity",
              "Recent public GitHub events plus recently updated repositories, generated by GitHub Actions.", body),
        encoding="utf-8",
    )


def main() -> None:
    token = (os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "").strip()
    if not token or not owner:
        raise SystemExit("GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER are required")
    user = load_profile(owner, token)
    events = load_events(owner, token)
    build_signal_panel(user)
    build_activity(user, events)
    print(f"updated GitHub signal for @{owner}")


if __name__ == "__main__":
    main()
