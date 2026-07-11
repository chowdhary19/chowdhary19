from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import html
import json
import os
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BG = "#010401"
GREEN = "#39ff6a"
GREEN_SOFT = "#b8ffc5"
GREEN_MID = "#22b94a"
GREEN_DIM = "#126329"
GREEN_FAINT = "#082f15"
MONO = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(x: float, y: float, value: object, size: float = 16, fill: str = GREEN_SOFT,
         weight: int = 400, anchor: str = "start") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(value)}</text>'
    )


def shell(width: int, height: int, title: str, desc: str, body: list[str]) -> str:
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{esc(title)}</title>',
        f'<desc id="desc">{esc(desc)}</desc>',
        '<defs>',
        f'<pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="{GREEN}" opacity=".022"/></pattern>',
        '<style>.blink{animation:blink 1s steps(1,end) infinite}.sweep{animation:sweep 8.5s linear infinite}@keyframes blink{50%{opacity:0}}@keyframes sweep{from{transform:translateX(-200px)}to{transform:translateX(1600px)}}@media(prefers-reduced-motion:reduce){.blink,.sweep{animation:none!important}}</style>',
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
        f'<rect width="{width}" height="{height}" fill="url(#scanlines)"/>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" fill="none" stroke="{GREEN_DIM}"/>',
        *body,
        '</svg>',
    ])


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
    return api(f"https://api.github.com/users/{owner}/events/public?per_page=50", token)


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


def color(count: int, maximum: int) -> str:
    if count <= 0:
        return GREEN_FAINT
    ratio = count / max(1, maximum)
    if ratio < .20:
        return "#0d4520"
    if ratio < .45:
        return GREEN_DIM
    if ratio < .72:
        return GREEN_MID
    return GREEN


def build_contributions(user: dict) -> None:
    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    weeks = calendar["weeks"][-53:]
    days = [d for week in weeks for d in week["contributionDays"]]
    maximum = max([int(d["contributionCount"]) for d in days] or [1])
    current, longest = streaks(days)
    repos = [r for r in user["repositories"]["nodes"] if not r["isFork"]]
    stars = sum(int(r["stargazerCount"]) for r in repos)
    languages = Counter(r["primaryLanguage"]["name"] for r in repos if r.get("primaryLanguage"))
    language_line = " / ".join(name for name, _ in languages.most_common(5)) or "public work in progress"
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    w, h = 1400, 390
    body = [
        text(28, 34, f"github://contributions/@{user['login']}", 13, GREEN, 700),
        text(1370, 34, updated, 10, GREEN_DIM, 600, "end"),
        f'<line x1="28" y1="48" x2="1372" y2="48" stroke="{GREEN_DIM}"/>',
        text(42, 82, f"$ {calendar['totalContributions']:,} contributions in the last year", 15, GREEN, 800),
    ]
    sx, sy, cell, gap = 44, 116, 15, 5
    for column, week in enumerate(weeks):
        for item in week["contributionDays"]:
            row = int(item["weekday"])
            count = int(item["contributionCount"])
            x, y = sx + column * (cell + gap), sy + row * (cell + gap)
            body.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color(count, maximum)}">'
                f'<title>{count} contributions on {esc(item["date"])}</title></rect>'
            )
    body += [
        f'<g class="sweep"><rect x="0" y="112" width="3" height="158" fill="{GREEN}" opacity=".28"/></g>',
        text(44, 306, f"commits={collection['totalCommitContributions']}  pull_requests={collection['totalPullRequestContributions']}  reviews={collection['totalPullRequestReviewContributions']}  issues={collection['totalIssueContributions']}", 12, GREEN_SOFT, 650),
        text(44, 332, f"streak={current}d  longest={longest}d  public_repos={user['repositories']['totalCount']}  stars={stars}  followers={user['followers']['totalCount']}", 12, GREEN_SOFT, 650),
        text(44, 358, f"languages={language_line}", 11, GREEN_DIM, 600),
        text(1356, 358, "generated in-repo", 10, GREEN_DIM, 600, "end"),
    ]
    (ASSETS / "github-contributions.svg").write_text(
        shell(w, h, "GitHub contribution history", "Real GitHub contribution history generated by GitHub Actions.", body),
        encoding="utf-8",
    )


def event_line(event: dict) -> tuple[str, str]:
    typ = event.get("type", "Event")
    repo = event.get("repo", {}).get("name", "unknown")
    payload = event.get("payload", {})
    when = event.get("created_at", "")[:10]
    if typ == "PushEvent":
        count = len(payload.get("commits", []))
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
    return when, f"{typ.removesuffix('Event').lower()} -> {repo}"


def build_activity(user: dict, events: list[dict]) -> None:
    lines: list[tuple[str, str]] = []
    seen: set[str] = set()
    for event in events:
        when, message = event_line(event)
        key = f"{when}:{message}"
        if key in seen:
            continue
        seen.add(key)
        lines.append((when, message))
        if len(lines) == 6:
            break
    if not lines:
        lines = [("--", "no recent public events returned by GitHub")]

    repos = [r for r in user["repositories"]["nodes"] if not r["isFork"]][:4]
    w, h = 1400, 360
    body = [
        text(28, 34, f"github://events/@{user['login']}?tail=6", 13, GREEN, 700),
        f'<line x1="28" y1="48" x2="1372" y2="48" stroke="{GREEN_DIM}"/>',
        text(42, 80, "$ tail -f public-engineering.log", 13, GREEN, 800),
    ]
    y = 118
    for when, message in lines:
        body += [text(44, y, when, 11, GREEN_DIM, 650), text(160, y, "|", 11, GREEN_DIM), text(186, y, message[:118], 12, GREEN_SOFT, 600)]
        y += 34
    if repos:
        body += [text(44, 326, "recent_repositories=" + "  ".join(r["name"] for r in repos), 10, GREEN_DIM, 600)]
    body += [f'<rect x="44" y="338" width="9" height="15" fill="{GREEN}" class="blink"/>']
    (ASSETS / "github-activity.svg").write_text(
        shell(w, h, "Recent GitHub activity", "Recent public GitHub events and repository movement generated by GitHub Actions.", body),
        encoding="utf-8",
    )


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "").strip()
    if not token or not owner:
        raise SystemExit("GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER are required")
    user = load_profile(owner, token)
    events = load_events(owner, token)
    build_contributions(user)
    build_activity(user, events)
    print(f"updated GitHub signal for @{owner}")


if __name__ == "__main__":
    main()
