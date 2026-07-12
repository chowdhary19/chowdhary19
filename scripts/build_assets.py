from __future__ import annotations

from pathlib import Path
import base64
import html
import io

from tech_icons import ICONS, BRAND_ICONS

# Pillow is only needed by prepare_portrait() below. Kept out of the module-level
# imports so callers that just want the shared palette/txt()/shell() helpers
# (e.g. update_github_signal.py, which runs in a workflow that never installs
# Pillow) don't need it installed at all.

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "source-portrait.jpg"

# --- palette -----------------------------------------------------------
# Warm ink base (not neon-hacker-black), a clay/terracotta primary accent and
# a muted sage secondary -- two deliberate accents instead of one monochrome
# green, in the spirit of Anthropic's own warm-neutral + clay grading.
INK = "#15130F"
INK_PANEL = "#1C1914"
INK_PANEL_2 = "#211D17"
LINE = "#332E27"
LINE_SOFT = "#28241E"
CREAM = "#F3EEE4"
CREAM_BRIGHT = "#FFFDF8"
PARCHMENT = "#C9C0B2"
MUTED = "#8A8175"
CLAY = "#D97757"
CLAY_BRIGHT = "#E8977A"
CLAY_DIM = "#5A3626"
SAGE = "#8FA888"
SAGE_BRIGHT = "#A8C29F"
SAGE_DIM = "#3A4536"

SERIF = "Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Times New Roman', serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def txt(x: float, y: float, value: object, size: float = 16, fill: str = CREAM,
        weight: int = 400, anchor: str = "start", opacity: float = 1.0,
        family: str = MONO, cls: str = "") -> str:
    ca = f' class="{cls}"' if cls else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
        f'opacity="{opacity}"{ca}>{esc(value)}</text>'
    )


def data_uri(img: Image.Image, fmt: str = "JPEG", quality: int = 82) -> str:
    out = io.BytesIO()
    if fmt == "JPEG":
        img.convert("RGB").save(out, format="JPEG", quality=quality, optimize=True, progressive=True)
        return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")
    img.save(out, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def prepare_portrait() -> str:
    """Preserve the actual portrait; treat the frame around it, not the face."""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    source = Image.open(SOURCE).convert("RGB")
    crop = ImageOps.fit(source, (560, 660), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    crop = ImageEnhance.Contrast(crop).enhance(1.06)
    crop = ImageEnhance.Color(crop).enhance(1.02)
    crop = ImageEnhance.Sharpness(crop).enhance(1.08)
    crop = ImageEnhance.Brightness(crop).enhance(0.99)

    rgba = crop.convert("RGBA")
    vignette = Image.new("L", crop.size, 0)
    px = vignette.load()
    cx, cy = crop.width / 2, crop.height / 2
    maxd = (cx * cx + cy * cy) ** 0.5
    for y in range(crop.height):
        for x in range(crop.width):
            d = (((x - cx) ** 2 + (y - cy) ** 2) ** 0.5) / maxd
            px[x, y] = max(0, min(140, int(max(0.0, d - 0.38) ** 1.6 * 320)))
    black = Image.new("RGBA", crop.size, (14, 11, 9, 255))
    rgba = Image.composite(black, rgba, vignette)

    # Faint warm edge signal (clay, not neon green) -- still secondary to the photo.
    gray = ImageOps.grayscale(crop)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(1.8)
    edge_rgba = ImageOps.colorize(edges, black=(0, 0, 0), white=(217, 119, 87)).convert("RGBA")
    edge_rgba.putalpha(edges.point(lambda p: int(p * 0.16)))
    rgba = Image.alpha_composite(rgba, edge_rgba)

    wash = Image.new("RGBA", crop.size, (200, 120, 80, 10))
    rgba = Image.alpha_composite(rgba, wash)

    return data_uri(rgba.convert("RGB"), fmt="JPEG", quality=82)


def shell(width: int, height: int, title: str, desc: str, body: list[str]) -> str:
    defs = f"""
<defs>
  <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
    <path d="M 30 0 L 0 0 0 30" fill="none" stroke="{CREAM}" stroke-opacity=".018"/>
  </pattern>
  <linearGradient id="rightGlow" x1="0" y1="0" x2="1" y2="0">
    <stop stop-color="{CLAY}" stop-opacity="0"/>
    <stop offset="1" stop-color="{CLAY}" stop-opacity=".07"/>
  </linearGradient>
  <linearGradient id="scanFadeY" x1="0" y1="0" x2="0" y2="1">
    <stop stop-color="{CLAY_BRIGHT}" stop-opacity=".45"/>
    <stop offset="1" stop-color="{CLAY_BRIGHT}" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="2.5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <style>
    .blink{{animation:blink 1.1s steps(1,end) infinite}}
    .scan-y{{animation:scanY 7s linear infinite}}
    .global-scan{{animation:globalScan 13s linear infinite}}
    .dash{{stroke-dasharray:8 10;animation:dash 9s linear infinite}}
    .pulse{{animation:pulse 2.6s ease-in-out infinite}}
    .pulse-ring{{animation:pulseRing 2.6s ease-out infinite}}
    .packet1{{animation:packet1 7.5s linear infinite}}
    .packet2{{animation:packet2 9.5s linear infinite}}
    .rise{{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}}
    .sheen{{animation:sheen 6s ease-in-out infinite}}
    @keyframes blink{{50%{{opacity:0}}}}
    @keyframes scanY{{from{{transform:translateY(-90px)}}to{{transform:translateY({height + 90}px)}}}}
    @keyframes globalScan{{from{{transform:translateY(-120px)}}to{{transform:translateY({height + 120}px)}}}}
    @keyframes dash{{to{{stroke-dashoffset:-180}}}}
    @keyframes pulse{{0%,100%{{opacity:.4}}50%{{opacity:1}}}}
    @keyframes pulseRing{{0%{{opacity:.6;transform:scale(1)}}100%{{opacity:0;transform:scale(2.4)}}}}
    @keyframes packet1{{0%{{transform:translateX(0)}}100%{{transform:translateX(1030px)}}}}
    @keyframes packet2{{0%{{transform:translateX(0)}}100%{{transform:translateX(-1030px)}}}}
    @keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
    @keyframes sheen{{0%,35%{{transform:translateX(-120%)}}65%,100%{{transform:translateX(120%)}}}}
    @media(prefers-reduced-motion:reduce){{.blink,.scan-y,.global-scan,.dash,.pulse,.pulse-ring,.packet1,.packet2,.rise,.sheen{{animation:none!important}}}}
  </style>
</defs>
"""
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{esc(title)}</title>',
        f'<desc id="desc">{esc(desc)}</desc>',
        defs,
        f'<rect width="{width}" height="{height}" fill="{INK}"/>',
        f'<rect width="{width}" height="{height}" fill="url(#grid)"/>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" fill="none" stroke="{LINE}"/>',
        *body,
        '</svg>',
    ])


def pill(x: float, y: float, w: float, h: float, label: str, accent: str, filled: bool = False) -> list[str]:
    fill = accent if filled else INK_PANEL_2
    text_fill = INK if filled else CREAM
    dot = CREAM if filled else accent
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{fill}" stroke="{accent if not filled else "none"}" stroke-width="1.2"/>',
        f'<circle cx="{x+16}" cy="{y+h/2}" r="3.2" fill="{dot}"/>',
        txt(x + 27, y + h / 2 + 4, label, 11.5, text_fill, 700, family=SANS),
    ]
    return out


def icon_glyph(kind: str, x: float, y: float, size: float, color: str) -> str:
    """Small hand-drawn or vendored-brand icon centered at (x, y), box `size`."""
    half = size / 2
    if kind == "terminal":
        return (
            f'<g stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M{x-half} {y-half} L{x-half+size*0.35} {y} L{x-half} {y+half}"/>'
            f'<line x1="{x-half+size*0.4}" y1="{y+half}" x2="{x+half}" y2="{y+half}"/>'
            f'</g>'
        )
    if kind == "calendar":
        r = size * 0.12
        return (
            f'<g stroke="{color}" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<rect x="{x-half}" y="{y-half+2}" width="{size}" height="{size-2}" rx="{r}"/>'
            f'<line x1="{x-half}" y1="{y-half+size*0.32}" x2="{x+half}" y2="{y-half+size*0.32}"/>'
            f'<line x1="{x-half+size*0.24}" y1="{y-half-1}" x2="{x-half+size*0.24}" y2="{y-half+size*0.14}"/>'
            f'<line x1="{x+half-size*0.24}" y1="{y-half-1}" x2="{x+half-size*0.24}" y2="{y-half+size*0.14}"/>'
            f'</g>'
        )
    if kind == "envelope":
        return (
            f'<g stroke="{color}" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<rect x="{x-half}" y="{y-half*0.75}" width="{size}" height="{size*0.75}" rx="2"/>'
            f'<path d="M{x-half} {y-half*0.7} L{x} {y+size*0.03} L{x+half} {y-half*0.7}"/>'
            f'</g>'
        )
    if kind.startswith("brand:"):
        label, d = BRAND_ICONS[kind.split(":", 1)[1]]
        scale = size / 24
        return f'<g transform="translate({x-half},{y-half}) scale({scale:.4f})"><path d="{d}" fill="{color}"/></g>'
    return ""


def button(slug: str, label: str, icon_kind: str, width: int, primary: bool = False,
           accent: str = CLAY) -> None:
    h = 52
    bg = CLAY if primary else INK_PANEL
    border = "none" if primary else LINE
    text_color = INK if primary else CREAM
    icon_color = INK if primary else accent
    body = [
        f'<rect x="1" y="1" width="{width-2}" height="{h-2}" rx="12" fill="{bg}" stroke="{border}" stroke-width="1.3"/>',
        icon_glyph(icon_kind, 30, h / 2, 20, icon_color),
        txt(50, h / 2 + 5, label, 14, text_color, 700, family=SANS),
    ]
    if primary:
        body.append(f'<rect x="1" y="1" width="{width-2}" height="{h-2}" rx="12" fill="none" stroke="{CLAY_BRIGHT}" stroke-width="1" opacity=".5" class="pulse"/>')
    svg = "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}" role="img" aria-label="{esc(label)}">',
        f'<rect width="{width}" height="{h}" fill="none"/>',
        '<style>@media(prefers-reduced-motion:reduce){.pulse{animation:none!important}}.pulse{animation:btnpulse 2.6s ease-in-out infinite}@keyframes btnpulse{0%,100%{opacity:.15}50%{opacity:.6}}</style>',
        *body,
        '</svg>',
    ])
    (ASSETS / f"button-{slug}.svg").write_text(svg, encoding="utf-8")


def write_buttons() -> None:
    button("synvolv", "SYNVOLV", "terminal", 160, primary=True)
    button("call", "SCHEDULE A CALL", "calendar", 214, accent=SAGE)
    button("email", "EMAIL", "envelope", 128, accent=CLAY)
    button("linkedin", "LINKEDIN", "brand:linkedin", 152, accent=SAGE)
    button("github", "GITHUB", "brand:github", 138, accent=CLAY)


def write_tech_stack() -> None:
    order = ["go", "python", "rust", "typescript", "postgresql", "redis", "apachekafka",
             "rabbitmq", "docker", "kubernetes", "amazonaws", "githubactions", "linux",
             "react", "nextdotjs", "terraform", "grafana", "prometheus"]
    cols, tile_w, tile_h = 9, 155, 138
    rows = (len(order) + cols - 1) // cols
    w, h = cols * tile_w, rows * tile_h + 60

    body = [
        txt(28, 34, "yuvraj@runtime:~$ ls stack/ --logos", 13, CLAY, 700),
        txt(w - 28, 34, "the tools; not the identity", 11, MUTED, 650, anchor="end"),
        f'<line x1="28" y1="49" x2="{w-28}" y2="49" stroke="{LINE}"/>',
    ]
    for i, slug in enumerate(order):
        label, d = ICONS[slug]
        col, row = i % cols, i // cols
        cx = col * tile_w + tile_w / 2
        cy = 60 + row * tile_h + tile_h / 2
        tint = CREAM if (i % 2 == 0) else PARCHMENT
        delay = 0.05 * i
        body += [
            f'<g class="rise" style="animation-delay:{delay:.2f}s">',
            f'<rect x="{col*tile_w+10}" y="{60+row*tile_h+8}" width="{tile_w-20}" height="{tile_h-16}" rx="10" fill="{INK_PANEL}" stroke="{LINE_SOFT}"/>',
            f'<g transform="translate({cx-19},{cy-30}) scale({38/24:.4f})"><path d="{d}" fill="{tint}"/></g>',
            txt(cx, cy + 38, label, 11.5, MUTED, 600, anchor="middle", family=SANS),
            '</g>',
        ]
    (ASSETS / "tech-stack.svg").write_text(
        shell(w, h, "Tech stack", "Logos for the languages and infrastructure Yuvraj builds with.", body),
        encoding="utf-8",
    )


def write_hero(portrait_uri: str) -> None:
    w, h = 1400, 760
    x0, y0, pw, ph = 38, 72, 510, 640
    body: list[str] = [
        txt(28, 34, "yuvraj@runtime:~$ ./whoami --deep --live", 13, CLAY, 700),
        txt(1370, 34, "identity=locked  scanner=online", 11, MUTED, 650, "end"),
        f'<line x1="28" y1="49" x2="1372" y2="49" stroke="{LINE}"/>',
        f'<rect x="570" y="50" width="830" height="710" fill="url(#rightGlow)"/>',
        f'<clipPath id="portrait"><rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" rx="2"/></clipPath>',
        f'<g clip-path="url(#portrait)">',
        f'<image x="{x0}" y="{y0}" width="{pw}" height="{ph}" preserveAspectRatio="xMidYMid slice" href="{portrait_uri}"/>',
        f'<g class="scan-y"><rect x="{x0}" y="{y0}" width="{pw}" height="2" fill="{CLAY_BRIGHT}" filter="url(#glow)"/><rect x="{x0}" y="{y0+2}" width="{pw}" height="72" fill="url(#scanFadeY)"/></g>',
        '</g>',
        f'<rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" fill="none" stroke="{CLAY}"/>',
        f'<path d="M{x0} {y0+24}V{y0}H{x0+24} M{x0+pw-24} {y0}H{x0+pw}V{y0+24} M{x0} {y0+ph-24}V{y0+ph}H{x0+24} M{x0+pw-24} {y0+ph}H{x0+pw}V{y0+ph-24}" fill="none" stroke="{CLAY_BRIGHT}" stroke-width="2"/>',
        txt(38, 735, "source=uploaded_portrait  color=preserved  scanner=active", 10, MUTED, 600),

        txt(600, 102, "$ identity", 15, CLAY, 800),
    ]

    body += [
        f'<text x="600" y="166" font-family="{SERIF}" font-size="50" font-weight="700" fill="{CREAM}">YUVRAJ SINGH</text>',
        f'<text x="600" y="222" font-family="{SERIF}" font-size="50" font-weight="700" fill="{CREAM}">CHOWDHARY</text>',
        f'<clipPath id="sheenClip"><rect x="595" y="120" width="620" height="115"/></clipPath>',
        f'<g clip-path="url(#sheenClip)">',
        f'<g class="sheen">',
        f'<text x="600" y="166" font-family="{SERIF}" font-size="50" font-weight="700" fill="{CREAM_BRIGHT}" opacity=".55">YUVRAJ SINGH</text>',
        f'<text x="600" y="222" font-family="{SERIF}" font-size="50" font-weight="700" fill="{CREAM_BRIGHT}" opacity=".55">CHOWDHARY</text>',
        '</g></g>',
    ]

    py = 254
    body += pill(600, py, 96, 27, "BUILDER", CLAY)
    body += pill(704, py, 226, 27, "INFRASTRUCTURE ENGINEER", SAGE)
    body += pill(938, py, 160, 27, "0-TO-1 SYSTEMS", CLAY)
    body.append(f'<line x1="600" y1="300" x2="1350" y2="300" stroke="{LINE}"/>')

    body += [
        txt(600, 349, "I build the layer that decides what happens", 22, PARCHMENT, 500, family=SANS),
        txt(600, 388, "while the request is still alive.", 27, CREAM, 700, family=SANS),
        txt(600, 434, "from request edge to ledger · exchange to operator", 13, MUTED, 650),
        txt(600, 461, "AI runtime · quant · blockchain · Linux · control planes", 13, MUTED, 650),

        txt(600, 522, "$ operating_principle", 14, SAGE, 800),
        txt(600, 561, "OWN THE PATH AFTER 200 OK", 22, CREAM, 800, family=SANS),
        txt(600, 594, "state / money / latency / recovery / evidence", 12, SAGE_BRIGHT, 650),

        txt(600, 650, "$ current_build", 14, CLAY, 800),
    ]
    body += pill(600, 662, 128, 30, "SYNVOLV", CLAY, filled=True)
    body += [
        f'<circle cx="616" cy="677" r="7" fill="none" stroke="{CREAM}" stroke-width="1.4" class="pulse-ring"/>',
        txt(742, 682, "builder of the fastest AI gateway, period", 13, CREAM, 700, family=SANS),
        txt(600, 714, "sub-millisecond authority before a token or a dollar is spent", 12, MUTED, 650),
        txt(600, 746, "yuvraj@runtime:~$", 12, CLAY, 700),
        f'<rect x="781" y="732" width="9" height="16" fill="{CLAY_BRIGHT}" class="blink"/>',

        f'<g class="global-scan"><rect x="0" y="0" width="{w}" height="1" fill="{CLAY_BRIGHT}" opacity=".18"/><rect x="0" y="1" width="{w}" height="48" fill="url(#scanFadeY)" opacity=".1"/></g>',
    ]
    (ASSETS / "hero-terminal.svg").write_text(
        shell(w, h, "Yuvraj Singh Chowdhary — builder and infrastructure engineer",
              "A color-preserving terminal portrait with animated scanners, on a warm ink / clay / sage identity system.", body),
        encoding="utf-8",
    )


def node(x: int, y: int, title: str, lines: list[str], accent: str, width: int = 240) -> list[str]:
    out = [
        f'<rect x="{x}" y="{y}" width="{width}" height="142" rx="6" fill="{INK_PANEL}" stroke="{LINE}"/>',
        f'<rect x="{x}" y="{y}" width="4" height="142" rx="2" fill="{accent}"/>',
        txt(x + 18, y + 28, title, 13, CREAM, 800, family=SANS),
        f'<line x1="{x+18}" y1="{y+40}" x2="{x+width-18}" y2="{y+40}" stroke="{LINE_SOFT}"/>',
    ]
    yy = y + 67
    for line in lines:
        out.append(txt(x + 18, yy, line, 11, PARCHMENT, 600))
        yy += 23
    return out


def write_systems_overview() -> None:
    w, h = 1400, 650
    body: list[str] = [
        txt(28, 34, "yuvraj@runtime:~$ ./map --career --eagle-view", 13, CLAY, 700),
        txt(1370, 34, "one builder / many layers", 11, MUTED, 650, "end"),
        f'<line x1="28" y1="49" x2="1372" y2="49" stroke="{LINE}"/>',
        txt(42, 83, "# different domains; the same engineering instinct", 12, MUTED, 650),
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
    accents = [SAGE, CLAY, SAGE, CLAY, SAGE]
    for x, title, lines, accent in zip(positions, titles, data, accents):
        body += node(x, 112, title, lines, accent, 228)

    for x in [160, 430, 700, 970, 1240]:
        body.append(f'<path d="M{x} 254 V324" fill="none" stroke="{LINE}" stroke-width="2" class="dash"/>')
    body += [
        f'<rect x="120" y="324" width="1160" height="124" rx="6" fill="{INK_PANEL_2}" stroke="{CLAY}"/>',
        txt(700, 360, "THE COMMON LAYER", 13, CLAY, 800, "middle"),
        txt(700, 400, "CONTROL  ·  STATE  ·  MONEY  ·  LATENCY  ·  RECOVERY  ·  OPERATOR", 20, CREAM, 800, "middle", family=SANS),
        txt(700, 430, "the system is only finished when the consequence is owned", 12, SAGE_BRIGHT, 650, "middle"),
        f'<path id="flow1" d="M170 386 H1230" fill="none" stroke="{LINE}" stroke-width="1"/>',
        f'<circle cx="170" cy="386" r="5" fill="{CLAY_BRIGHT}" filter="url(#glow)" class="packet1"/>',
        f'<circle cx="1230" cy="386" r="4" fill="{SAGE_BRIGHT}" class="packet2"/>',

        f'<path d="M700 448 V505" fill="none" stroke="{LINE}" stroke-width="2" class="dash"/>',
        f'<rect x="255" y="505" width="890" height="92" rx="6" fill="{INK_PANEL}" stroke="{LINE}"/>',
        txt(282, 540, "$ builder_mode", 13, SAGE, 800),
        txt(282, 575, "understand the business -> find the invariant -> build -> operate -> rewrite what reality disproves", 14, CREAM, 600, family=SANS),
        txt(42, 625, "breadth is not the point; end-to-end ownership is", 11, MUTED, 650),
        f'<g class="global-scan"><rect x="0" y="0" width="{w}" height="1" fill="{CLAY_BRIGHT}" opacity=".14"/><rect x="0" y="1" width="{w}" height="42" fill="url(#scanFadeY)" opacity=".09"/></g>',
    ]
    (ASSETS / "systems-overview.svg").write_text(
        shell(w, h, "Systems overview",
              "A terminal map connecting product, blockchain, quantitative finance, Linux platform engineering and AI runtime work through shared systems principles.", body),
        encoding="utf-8",
    )


def write_placeholder_contributions() -> None:
    w, h = 1400, 300
    body = [
        txt(28, 34, "github://signal/$GITHUB_REPOSITORY_OWNER", 13, CLAY, 700),
        txt(1370, 34, "self-hosted signal", 10, MUTED, 650, "end"),
        f'<line x1="28" y1="49" x2="1372" y2="49" stroke="{LINE}"/>',
        txt(42, 82, "$ gh api graphql --field query=contributionsCollection", 13, CLAY, 800),
        txt(42, 108, "run Actions -> Refresh profile signal once; this panel becomes real KPIs", 11, MUTED, 600),
    ]
    labels = ["CONTRIBUTIONS / YR", "CURRENT STREAK", "LONGEST STREAK", "PUBLIC REPOS", "STARS EARNED", "FOLLOWERS"]
    tile_w, gap, sx, sy = 216, 16, 42, 150
    for i, label in enumerate(labels):
        x = sx + i * (tile_w + gap)
        body += [
            f'<rect x="{x}" y="{sy}" width="{tile_w}" height="88" rx="8" fill="{INK_PANEL}" stroke="{LINE}"/>',
            txt(x + 16, sy + 40, "--", 26, MUTED, 800, family=SANS),
            txt(x + 16, sy + 66, label, 10.5, MUTED, 650, family=SANS),
        ]
    (ASSETS / "github-contributions.svg").write_text(
        shell(w, h, "GitHub KPI signal", "A KPI panel replaced by real GitHub data after the included workflow runs.", body), encoding="utf-8")


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
        txt(28, 34, "github://events/public?tail=6", 13, CLAY, 700),
        f'<line x1="28" y1="49" x2="1372" y2="49" stroke="{LINE}"/>',
        txt(42, 82, "$ tail -f public-engineering.log", 13, CLAY, 800),
    ]
    for y, stamp, message in rows:
        body += [txt(44, y, stamp, 11, MUTED, 650), txt(160, y, "|", 11, MUTED), txt(186, y, message, 12, PARCHMENT, 600)]
    body += [txt(44, 322, "yuvraj@runtime:~$", 11, CLAY, 700), f'<rect x="206" y="309" width="9" height="16" fill="{CLAY_BRIGHT}" class="blink"/>']
    (ASSETS / "github-activity.svg").write_text(
        shell(w, h, "Recent GitHub activity", "Recent public GitHub activity populated by the included GitHub Action.", body), encoding="utf-8")


def write_social_preview(portrait_uri: str) -> None:
    w, h = 1280, 640
    body = [
        txt(28, 36, "yuvraj@runtime:~$ ./whoami --deep", 13, CLAY, 700),
        f'<line x1="28" y1="51" x2="1252" y2="51" stroke="{LINE}"/>',
        f'<image x="38" y="82" width="420" height="512" preserveAspectRatio="xMidYMid slice" href="{portrait_uri}"/>',
        f'<rect x="38" y="82" width="420" height="512" fill="none" stroke="{CLAY}"/>',
        f'<g class="scan-y"><rect x="38" y="82" width="420" height="2" fill="{CLAY_BRIGHT}"/><rect x="38" y="84" width="420" height="54" fill="url(#scanFadeY)"/></g>',
        f'<text x="505" y="148" font-family="{SERIF}" font-size="48" font-weight="700" fill="{CREAM}">YUVRAJ SINGH</text>',
        f'<text x="505" y="204" font-family="{SERIF}" font-size="48" font-weight="700" fill="{CREAM}">CHOWDHARY</text>',
    ]
    body += pill(508, 222, 300, 28, "BUILDER · INFRASTRUCTURE ENGINEER", CLAY)
    body += [
        txt(505, 328, "I follow systems past the point", 23, PARCHMENT, 500, family=SANS),
        txt(505, 369, "where the original ticket ends.", 26, CREAM, 700, family=SANS),
        txt(505, 423, "AI runtime · quant · blockchain · Linux · control planes", 13, MUTED, 650),
        txt(505, 495, "$ principle", 14, SAGE, 800),
        txt(505, 535, "OWN THE PATH AFTER 200 OK", 22, CREAM, 800, family=SANS),
        txt(28, 618, "state -> money -> latency -> recovery -> evidence -> operator", 12, MUTED, 650),
    ]
    (ASSETS / "social-preview.svg").write_text(
        shell(w, h, "Yuvraj Singh Chowdhary", "Social preview for Yuvraj's systems engineering GitHub profile.", body), encoding="utf-8")


def render(svg_name: str, png_name: str, width: int | None = None) -> None:
    try:
        import cairosvg  # imported lazily so the SVG pipeline works without it
    except Exception:
        # Missing either the cairosvg package or its native libcairo dependency
        # (e.g. `brew install cairo` on macOS). PNGs are a convenience export
        # for social previews / offline viewing; the SVGs are the real asset.
        print(f"skip {png_name}: cairosvg/libcairo not available")
        return
    kwargs = {"url": str(ASSETS / svg_name), "write_to": str(ASSETS / png_name)}
    if width:
        kwargs["output_width"] = width
    cairosvg.svg2png(**kwargs)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    portrait_uri = prepare_portrait()
    write_hero(portrait_uri)
    write_systems_overview()
    write_buttons()
    write_tech_stack()
    write_placeholder_contributions()
    write_placeholder_activity()
    write_social_preview(portrait_uri)
    for name in ["hero-terminal", "systems-overview", "tech-stack", "github-contributions", "github-activity", "social-preview"]:
        render(f"{name}.svg", f"{name}.png")
    for slug in ["synvolv", "call", "email", "linkedin", "github"]:
        render(f"button-{slug}.svg", f"button-{slug}.png")
    print("built terminal assets")


if __name__ == "__main__":
    main()
