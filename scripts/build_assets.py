from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import base64
import html
import io

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "source-portrait.jpg"

BG = "#020603"
PANEL = "#061009"
PANEL_2 = "#08150c"
GREEN = "#42ff78"
GREEN_SOFT = "#c8ffd4"
GREEN_MID = "#27c957"
GREEN_DIM = "#12672d"
GREEN_FAINT = "#0a3218"
TEXT_DIM = "#75a982"
MONO = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def txt(x: float, y: float, value: object, size: float = 16, fill: str = GREEN_SOFT,
        weight: int = 400, anchor: str = "start", opacity: float = 1.0, cls: str = "") -> str:
    ca = f' class="{cls}"' if cls else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
        f'opacity="{opacity}"{ca}>{esc(value)}</text>'
    )


def data_uri(img: Image.Image, fmt: str = "PNG", quality: int = 85) -> str:
    out = io.BytesIO()
    if fmt == "JPEG":
        img.convert("RGB").save(out, format="JPEG", quality=quality, optimize=True, progressive=True)
        return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")
    img.save(out, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def prepare_portrait() -> tuple[str, list[tuple[int, int, str, float]]]:
    """Preserve the actual portrait, then add terminal treatment around it.

    The photo carries identity. Glyphs and edge highlights are deliberately secondary.
    """
    source = Image.open(SOURCE).convert("RGB")
    crop = ImageOps.fit(source, (560, 660), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    crop = ImageEnhance.Contrast(crop).enhance(1.08)
    crop = ImageEnhance.Color(crop).enhance(1.03)
    crop = ImageEnhance.Sharpness(crop).enhance(1.10)
    crop = ImageEnhance.Brightness(crop).enhance(0.98)

    # Keep the photograph recognizably photographic. Darken only the outer frame.
    rgba = crop.convert("RGBA")
    vignette = Image.new("L", crop.size, 0)
    px = vignette.load()
    cx, cy = crop.width / 2, crop.height / 2
    maxd = (cx * cx + cy * cy) ** 0.5
    for y in range(crop.height):
        for x in range(crop.width):
            d = (((x - cx) ** 2 + (y - cy) ** 2) ** 0.5) / maxd
            px[x, y] = max(0, min(150, int(max(0.0, d - 0.36) ** 1.55 * 340)))
    black = Image.new("RGBA", crop.size, (0, 5, 2, 255))
    rgba = Image.composite(black, rgba, vignette)

    # Fine green edge signal; source pixels still dominate.
    gray = ImageOps.grayscale(crop)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(2.2)
    edge_rgba = ImageOps.colorize(edges, black=(0, 0, 0), white=(66, 255, 120)).convert("RGBA")
    edge_rgba.putalpha(edges.point(lambda p: int(p * 0.28)))
    rgba = Image.alpha_composite(rgba, edge_rgba)

    # Gentle green ambient wash, stronger in the background than on the face.
    wash = Image.new("RGBA", crop.size, (20, 150, 65, 14))
    rgba = Image.alpha_composite(rgba, wash)

    # Encode the treated portrait as a compact progressive JPEG. The old build
    # embedded a ~520 KB PNG plus a 7k-node glyph overlay, which made the hero
    # SVG ~1.9 MB and janked scrolling on the profile page. The photo already
    # carries identity, so we keep it sharp and drop the glyph field entirely.
    glyphs: list[tuple[int, int, str, float]] = []
    return data_uri(rgba.convert("RGB"), fmt="JPEG", quality=82), glyphs


def shell(width: int, height: int, title: str, desc: str, body: list[str]) -> str:
    defs = f"""
<defs>
  <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
    <path d="M 28 0 L 0 0 0 28" fill="none" stroke="{GREEN}" stroke-opacity=".025"/>
  </pattern>
  <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="1" fill="{GREEN}" opacity=".025"/>
  </pattern>
  <linearGradient id="rightGlow" x1="0" y1="0" x2="1" y2="0">
    <stop stop-color="{GREEN}" stop-opacity="0"/>
    <stop offset="1" stop-color="{GREEN}" stop-opacity=".11"/>
  </linearGradient>
  <linearGradient id="scanFadeY" x1="0" y1="0" x2="0" y2="1">
    <stop stop-color="{GREEN}" stop-opacity=".38"/>
    <stop offset="1" stop-color="{GREEN}" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="2.5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <style>
    .blink{{animation:blink 1s steps(1,end) infinite}}
    .scan-y{{animation:scanY 6.5s linear infinite}}
    .global-scan{{animation:globalScan 11s linear infinite}}
    .dash{{stroke-dasharray:8 10;animation:dash 9s linear infinite}}
    .pulse{{animation:pulse 2.8s ease-in-out infinite}}
    .packet1{{animation:packet1 7.5s linear infinite}}
    .packet2{{animation:packet2 9.5s linear infinite}}
    @keyframes blink{{50%{{opacity:0}}}}
    @keyframes scanY{{from{{transform:translateY(-90px)}}to{{transform:translateY({height + 90}px)}}}}
    @keyframes globalScan{{from{{transform:translateY(-120px)}}to{{transform:translateY({height + 120}px)}}}}
    @keyframes dash{{to{{stroke-dashoffset:-180}}}}
    @keyframes pulse{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}
    @keyframes packet1{{0%{{transform:translateX(0)}}100%{{transform:translateX(1030px)}}}}
    @keyframes packet2{{0%{{transform:translateX(0)}}100%{{transform:translateX(-1030px)}}}}
    @media(prefers-reduced-motion:reduce){{.blink,.scan-y,.global-scan,.dash,.pulse,.packet1,.packet2{{animation:none!important}}}}
  </style>
</defs>
"""
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{esc(title)}</title>',
        f'<desc id="desc">{esc(desc)}</desc>',
        defs,
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
        f'<rect width="{width}" height="{height}" fill="url(#grid)"/>',
        f'<rect width="{width}" height="{height}" fill="url(#scanlines)"/>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" fill="none" stroke="{GREEN_DIM}"/>',
        *body,
        '</svg>',
    ])


def write_hero(portrait_uri: str, glyphs: list[tuple[int, int, str, float]]) -> None:
    w, h = 1400, 760
    x0, y0, pw, ph = 38, 72, 510, 640
    body: list[str] = [
        txt(28, 34, "yuvraj@runtime:~$ ./whoami --deep --live", 13, GREEN, 700),
        txt(1370, 34, "identity=locked  scanner=online", 11, GREEN_DIM, 650, "end"),
        f'<line x1="28" y1="49" x2="1372" y2="49" stroke="{GREEN_DIM}"/>',
        f'<rect x="570" y="50" width="830" height="710" fill="url(#rightGlow)"/>',
        f'<clipPath id="portrait"><rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" rx="2"/></clipPath>',
        f'<g clip-path="url(#portrait)">',
        f'<image x="{x0}" y="{y0}" width="{pw}" height="{ph}" preserveAspectRatio="xMidYMid slice" href="{portrait_uri}"/>',
    ]
    body += [
        f'<g class="scan-y"><rect x="{x0}" y="{y0}" width="{pw}" height="2" fill="{GREEN}" filter="url(#glow)"/><rect x="{x0}" y="{y0+2}" width="{pw}" height="72" fill="url(#scanFadeY)"/></g>',
        '</g>',
        f'<rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" fill="none" stroke="{GREEN_MID}"/>',
        f'<path d="M{x0} {y0+24}V{y0}H{x0+24} M{x0+pw-24} {y0}H{x0+pw}V{y0+24} M{x0} {y0+ph-24}V{y0+ph}H{x0+24} M{x0+pw-24} {y0+ph}H{x0+pw}V{y0+ph-24}" fill="none" stroke="{GREEN}" stroke-width="2"/>',
        txt(38, 735, "source=uploaded_portrait  color=preserved  scanner=active", 10, GREEN_DIM, 600),

        txt(600, 102, "$ identity", 15, GREEN, 800),
        txt(600, 166, "YUVRAJ SINGH", 48, GREEN_SOFT, 850),
        txt(600, 222, "CHOWDHARY", 48, GREEN_SOFT, 850),
        txt(603, 261, "FOUNDER / INFRASTRUCTURE ENGINEER / 0-TO-1 BUILDER", 14, GREEN, 800),
        f'<line x1="600" y1="286" x2="1350" y2="286" stroke="{GREEN_DIM}"/>',

        txt(600, 335, "I follow systems past the point", 23, GREEN_SOFT, 650),
        txt(600, 374, "where the original ticket ends.", 27, GREEN, 850),
        txt(600, 420, "from request edge to ledger · exchange to operator", 13, TEXT_DIM, 650),
        txt(600, 447, "AI runtime · quant · blockchain · Linux · control planes", 13, TEXT_DIM, 650),

        txt(600, 508, "$ operating_principle", 14, GREEN, 800),
        txt(600, 547, "OWN THE PATH AFTER 200 OK", 22, GREEN_SOFT, 850),
        txt(600, 580, "state / money / latency / recovery / evidence", 12, GREEN_MID, 650),

        txt(600, 636, "$ current_build", 14, GREEN, 800),
        txt(600, 676, "SYNVOLV", 24, GREEN_SOFT, 850),
        txt(740, 676, "one of the fastest AI gateway control paths", 13, GREEN_MID, 650),
        txt(600, 711, "runtime authority before provider spend", 12, GREEN_DIM, 650),
        txt(600, 742, "yuvraj@runtime:~$", 12, GREEN, 700),
        f'<rect x="781" y="728" width="9" height="16" fill="{GREEN}" class="blink"/>',

        f'<g class="global-scan"><rect x="0" y="0" width="{w}" height="1" fill="{GREEN}" opacity=".20"/><rect x="0" y="1" width="{w}" height="48" fill="url(#scanFadeY)" opacity=".14"/></g>',
    ]
    (ASSETS / "hero-terminal.svg").write_text(
        shell(w, h, "Yuvraj Singh Chowdhary — founder and infrastructure engineer", "A color-preserving terminal portrait with animated scanners and a broad systems-engineering identity." , body),
        encoding="utf-8",
    )


def node(x: int, y: int, title: str, lines: list[str], width: int = 240) -> list[str]:
    out = [
        f'<rect x="{x}" y="{y}" width="{width}" height="142" rx="4" fill="{PANEL}" stroke="{GREEN_DIM}"/>',
        txt(x + 18, y + 28, title, 13, GREEN, 800),
        f'<line x1="{x+18}" y1="{y+40}" x2="{x+width-18}" y2="{y+40}" stroke="{GREEN_FAINT}"/>',
    ]
    yy = y + 67
    for line in lines:
        out.append(txt(x + 18, yy, line, 11, GREEN_SOFT, 600))
        yy += 23
    return out


def write_systems_overview() -> None:
    w, h = 1400, 650
    body: list[str] = [
        txt(28, 34, "yuvraj@runtime:~$ ./map --career --eagle-view", 13, GREEN, 700),
        txt(1370, 34, "one builder / many layers", 11, GREEN_DIM, 650, "end"),
        f'<line x1="28" y1="49" x2="1372" y2="49" stroke="{GREEN_DIM}"/>',
        txt(42, 83, "# different domains; the same engineering instinct", 12, GREEN_DIM, 650),
    ]

    positions = [46, 316, 586, 856, 1126]
    titles = ["PRODUCT / AUTOMATION", "BLOCKCHAIN / DEFI", "QUANT / FINANCIAL", "LINUX / PLATFORM", "AI RUNTIME"]
    data = [
        ["ship from zero", "workflows + integrations", "operator-facing products"],
        ["signing + replay", "irreversible state", "on-chain correctness"],
        ["orders + fills", "ledger + reconciliation", "risk + control rooms"],
        ["CI + release safety", "diagnostics + images", "reproducible systems"],
        ["gateway + streaming", "policy + economics", "routing + evidence"],
    ]
    for x, title, lines in zip(positions, titles, data):
        body += node(x, 112, title, lines, 228)

    # Converging paths.
    for x in [160, 430, 700, 970, 1240]:
        body.append(f'<path d="M{x} 254 V324" fill="none" stroke="{GREEN_DIM}" stroke-width="2" class="dash"/>')
    body += [
        f'<rect x="120" y="324" width="1160" height="124" rx="4" fill="{PANEL_2}" stroke="{GREEN_MID}"/>',
        txt(700, 360, "THE COMMON LAYER", 13, GREEN, 800, "middle"),
        txt(700, 400, "CONTROL  ·  STATE  ·  MONEY  ·  LATENCY  ·  RECOVERY  ·  OPERATOR", 20, GREEN_SOFT, 850, "middle"),
        txt(700, 430, "the system is only finished when the consequence is owned", 12, GREEN_MID, 650, "middle"),
        f'<path id="flow1" d="M170 386 H1230" fill="none" stroke="{GREEN_DIM}" stroke-width="1"/>',
        f'<circle cx="170" cy="386" r="5" fill="{GREEN}" filter="url(#glow)" class="packet1"/>',
        f'<circle cx="1230" cy="386" r="4" fill="{GREEN_MID}" class="packet2"/>',

        f'<path d="M700 448 V505" fill="none" stroke="{GREEN_DIM}" stroke-width="2" class="dash"/>',
        f'<rect x="255" y="505" width="890" height="92" rx="4" fill="{PANEL}" stroke="{GREEN_DIM}"/>',
        txt(282, 540, "$ builder_mode", 13, GREEN, 800),
        txt(282, 575, "understand the business -> find the invariant -> build -> operate -> rewrite what reality disproves", 14, GREEN_SOFT, 650),
        txt(42, 625, "breadth is not the point; end-to-end ownership is", 11, GREEN_DIM, 650),
        f'<g class="global-scan"><rect x="0" y="0" width="{w}" height="1" fill="{GREEN}" opacity=".16"/><rect x="0" y="1" width="{w}" height="42" fill="url(#scanFadeY)" opacity=".11"/></g>',
    ]
    (ASSETS / "systems-overview.svg").write_text(
        shell(w, h, "Systems overview", "A terminal map connecting product, blockchain, quantitative finance, Linux platform engineering and AI runtime work through shared systems principles.", body),
        encoding="utf-8",
    )


def write_placeholder_contributions() -> None:
    w, h = 1400, 390
    body = [
        txt(28, 34, "github://contributions/$GITHUB_REPOSITORY_OWNER", 13, GREEN, 700),
        txt(1370, 34, "self-hosted signal", 10, GREEN_DIM, 650, "end"),
        f'<line x1="28" y1="49" x2="1372" y2="49" stroke="{GREEN_DIM}"/>',
        txt(42, 82, "$ gh api graphql --field query=contributionsCollection", 13, GREEN, 800),
        txt(42, 108, "run Actions → Refresh profile signal once; this panel becomes your real public history", 11, GREEN_DIM, 600),
    ]
    sx, sy, cell, gap = 44, 142, 15, 5
    levels = [GREEN_FAINT, "#0d4520", GREEN_DIM, GREEN_MID, GREEN]
    for col in range(53):
        for row in range(7):
            n = (col * 11 + row * 5 + col // 3) % 21
            level = 0 if n < 9 else min(4, 1 + (n - 9) // 3)
            body.append(f'<rect x="{sx + col*(cell+gap)}" y="{sy + row*(cell+gap)}" width="{cell}" height="{cell}" rx="2" fill="{levels[level]}"/>')
    body += [
        f'<g class="packet1"><rect x="44" y="138" width="3" height="158" fill="{GREEN}" opacity=".25"/></g>',
        txt(44, 326, "commits=--  pull_requests=--  reviews=--  issues=--  streak=--", 12, GREEN_SOFT, 650),
        txt(44, 354, "generated in this repository · no external stats service", 10, GREEN_DIM, 600),
    ]
    (ASSETS / "github-contributions.svg").write_text(
        shell(w, h, "GitHub contribution history", "A terminal contribution panel replaced by real GitHub data after the included workflow runs.", body), encoding="utf-8")


def write_placeholder_activity() -> None:
    w, h = 1400, 350
    rows = [
        (116, "0000-00-00", "waiting for the first workflow run"),
        (154, "0000-00-00", "pushes, pull requests, reviews and releases appear here"),
        (192, "0000-00-00", "recent repository movement is read from the public event stream"),
        (230, "0000-00-00", "SVG is generated and committed by this profile repository"),
        (268, "0000-00-00", "nothing is fetched by the README at view time"),
    ]
    body = [
        txt(28, 34, "github://events/public?tail=6", 13, GREEN, 700),
        f'<line x1="28" y1="49" x2="1372" y2="49" stroke="{GREEN_DIM}"/>',
        txt(42, 82, "$ tail -f public-engineering.log", 13, GREEN, 800),
    ]
    for y, stamp, message in rows:
        body += [txt(44, y, stamp, 11, GREEN_DIM, 650), txt(160, y, "|", 11, GREEN_DIM), txt(186, y, message, 12, GREEN_SOFT, 600)]
    body += [txt(44, 322, "yuvraj@runtime:~$", 11, GREEN, 700), f'<rect x="206" y="309" width="9" height="16" fill="{GREEN}" class="blink"/>']
    (ASSETS / "github-activity.svg").write_text(
        shell(w, h, "Recent GitHub activity", "Recent public GitHub activity populated by the included GitHub Action.", body), encoding="utf-8")


def write_social_preview(portrait_uri: str) -> None:
    w, h = 1280, 640
    body = [
        txt(28, 36, "yuvraj@runtime:~$ ./whoami --deep", 13, GREEN, 700),
        f'<line x1="28" y1="51" x2="1252" y2="51" stroke="{GREEN_DIM}"/>',
        f'<image x="38" y="82" width="420" height="512" preserveAspectRatio="xMidYMid slice" href="{portrait_uri}"/>',
        f'<rect x="38" y="82" width="420" height="512" fill="none" stroke="{GREEN_MID}"/>',
        f'<g class="scan-y"><rect x="38" y="82" width="420" height="2" fill="{GREEN}"/><rect x="38" y="84" width="420" height="54" fill="url(#scanFadeY)"/></g>',
        txt(505, 148, "YUVRAJ SINGH", 47, GREEN_SOFT, 850),
        txt(505, 204, "CHOWDHARY", 47, GREEN_SOFT, 850),
        txt(508, 246, "FOUNDER / INFRASTRUCTURE ENGINEER", 15, GREEN, 800),
        txt(505, 328, "I follow systems past the point", 23, GREEN_SOFT, 650),
        txt(505, 369, "where the original ticket ends.", 26, GREEN, 850),
        txt(505, 423, "AI runtime · quant · blockchain · Linux · control planes", 13, TEXT_DIM, 650),
        txt(505, 495, "$ principle", 14, GREEN, 800),
        txt(505, 535, "OWN THE PATH AFTER 200 OK", 22, GREEN_SOFT, 850),
        txt(28, 618, "state -> money -> latency -> recovery -> evidence -> operator", 12, GREEN_DIM, 650),
    ]
    (ASSETS / "social-preview.svg").write_text(
        shell(w, h, "Yuvraj Singh Chowdhary", "Social preview for Yuvraj's systems engineering GitHub profile." , body), encoding="utf-8")


def render(svg_name: str, png_name: str, width: int | None = None) -> None:
    import cairosvg  # imported lazily so the SVG pipeline works without it
    kwargs = {"url": str(ASSETS / svg_name), "write_to": str(ASSETS / png_name)}
    if width:
        kwargs["output_width"] = width
    cairosvg.svg2png(**kwargs)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    portrait_uri, glyphs = prepare_portrait()
    write_hero(portrait_uri, glyphs)
    write_systems_overview()
    write_placeholder_contributions()
    write_placeholder_activity()
    write_social_preview(portrait_uri)
    for name in ["hero-terminal", "systems-overview", "github-contributions", "github-activity", "social-preview"]:
        render(f"{name}.svg", f"{name}.png")
    print("built terminal assets")


if __name__ == "__main__":
    main()
