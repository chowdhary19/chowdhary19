from __future__ import annotations

from pathlib import Path
import base64
import html
import io
import math

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


PORTRAIT_W, PORTRAIT_H = 560, 660

# Character ramp from faint to dense; drives both the glyph chosen per cell
# and (via the same intensity value) its color, so "denser-looking" glyphs
# are also the brighter ones -- important for a light-on-dark rendering.
# Deliberately short and visually consistent (not a 70-glyph mix of random
# digits/letters/brackets): a wide alphabet reads as typographic noise since
# neighboring cells of similar intensity can land on unrelated-looking glyphs.
# This is the same short ramp classic ASCII-art tools converge on.
_ASCII_RAMP = " .:-=+*#%@"


def _ascii_ramp_color(t: float) -> tuple[int, int, int]:
    def lerp(a, b, k):
        k = max(0.0, min(1.0, k))
        return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))

    ink, sage, parch, cream, clay_hot = (21, 19, 15), (130, 155, 122), (218, 210, 197), (250, 247, 240), (236, 152, 118)
    if t < 0.20:
        return lerp(ink, sage, t / 0.20)
    if t < 0.45:
        return lerp(sage, parch, (t - 0.20) / 0.25)
    if t < 0.70:
        return lerp(parch, cream, (t - 0.45) / 0.25)
    return lerp(cream, clay_hot, (t - 0.70) / 0.30)


def _silhouette_mask(nx: float, ny: float) -> float:
    """A feathered head-and-shoulders mask (not a radial vignette) so the
    portrait background goes fully black instead of showing faint static
    from a flat studio backdrop. Tuned to this specific photo's framing.
    """
    hx, hy, rx, ry = 0.5, 0.36, 0.29, 0.35
    head_d = math.sqrt(((nx - hx) / rx) ** 2 + ((ny - hy) / ry) ** 2)

    shoulder_top, shoulder_full = 0.58, 0.76
    if ny <= shoulder_top:
        d = head_d
    else:
        t = min(1.0, (ny - shoulder_top) / (shoulder_full - shoulder_top))
        half_w = rx + t * (0.53 - rx)
        shoulder_d = abs(nx - hx) / half_w
        blend_band = 0.06
        if ny <= shoulder_top + blend_band:
            blend = (ny - shoulder_top) / blend_band
            d = head_d * (1 - blend) + shoulder_d * blend
        else:
            d = shoulder_d

    feather = 0.07
    result = 1.0
    if d <= 1.0 - feather:
        result = 1.0
    elif d >= 1.0 + feather:
        result = 0.0
    else:
        result = 1.0 - (d - (1.0 - feather)) / (2 * feather)

    # Horizontal shoulder distance alone never forces the mask to zero as ny
    # grows past shoulder_full (it just stops widening) -- without an explicit
    # vertical floor, isolated pixels far below the frame can still slip
    # through if they happen to sit within the shoulder's horizontal span.
    bottom_fade_start, bottom_fade_end = 0.80, 0.86
    if ny > bottom_fade_start:
        vfade = 1.0 - min(1.0, (ny - bottom_fade_start) / (bottom_fade_end - bottom_fade_start))
        result = min(result, vfade)
    return result


def prepare_portrait() -> str:
    """Rebuild the portrait entirely out of characters -- a luminance-driven
    ASCII mosaic (real light/shadow tonal structure, not just outlines),
    rendered once to a raster image.

    An earlier version drove this purely off edge-detection, which only
    captures outlines -- no smooth shading -- so faces read as a flat noisy
    texture instead of a face. This blends mostly luminance (for actual
    photographic form: forehead highlight, cheek shading, jaw shadow) with a
    smaller edge contribution (for crisp glasses/hairline definition).

    This deliberately does *not* draw thousands of live SVG <text> nodes (an
    earlier version did exactly that -- 7,380 of them -- and made the profile
    stutter on scroll). All the character detail lives in JPEG pixels instead,
    so the SVG that embeds it stays a single small <image> tag regardless of
    how dense the mosaic is.
    """
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

    cols = 100
    lum_gamma, edge_weight, contrast, thresh = 0.75, 0.25, 1.5, 0.05
    font_path = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"

    source = Image.open(SOURCE).convert("RGB")
    crop = ImageOps.fit(source, (PORTRAIT_W, PORTRAIT_H), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    gray = ImageOps.grayscale(crop)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=8, percent=180, threshold=2))
    gray = ImageOps.autocontrast(gray, cutoff=2)
    gray = ImageEnhance.Contrast(gray).enhance(contrast)

    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.autocontrast(edges, cutoff=0)

    rows = round(cols * PORTRAIT_H / PORTRAIT_W)
    small_lum = gray.resize((cols, rows), Image.Resampling.BOX)
    small_edge = edges.resize((cols, rows), Image.Resampling.BOX)
    pl, pe = small_lum.load(), small_edge.load()

    cell_w, cell_h = PORTRAIT_W / cols, PORTRAIT_H / rows
    fsize = max(6, round(cell_h * 1.35))
    try:
        from PIL import ImageFont
        font = ImageFont.truetype(font_path, fsize)
        glow_font = ImageFont.truetype(font_path, int(fsize * 1.5))
    except OSError:
        from PIL import ImageFont
        font = ImageFont.load_default()
        glow_font = font

    cells: list[tuple[float, float, str, float]] = []
    for yy in range(rows):
        for xx in range(cols):
            mask = _silhouette_mask(xx / cols, yy / rows)
            if mask <= 0.0:
                continue
            lum, e = pl[xx, yy] / 255.0, pe[xx, yy] / 255.0
            raw = (lum * (1 - edge_weight) + max(lum, e) * edge_weight) * mask
            intensity = raw ** lum_gamma if raw > 0 else 0.0
            if intensity < thresh:
                continue
            idx = min(len(_ASCII_RAMP) - 1, int(intensity * (len(_ASCII_RAMP) - 1)))
            ch = _ASCII_RAMP[idx]
            if ch == " ":
                continue
            cells.append((xx * cell_w + cell_w / 2, yy * cell_h + cell_h / 2, ch, intensity))

    canvas = Image.new("RGB", (PORTRAIT_W, PORTRAIT_H), (21, 19, 15))

    # Soft bloom pass: the brightest cells (glasses highlights, forehead) get
    # drawn oversized and blurred underneath the crisp pass, like a lit screen.
    glow_layer = Image.new("RGB", (PORTRAIT_W, PORTRAIT_H), (21, 19, 15))
    gdraw = ImageDraw.Draw(glow_layer)
    for x, y, ch, inten in cells:
        if inten > 0.62:
            gdraw.text((x, y), ch, font=glow_font, fill=_ascii_ramp_color(inten), anchor="mm")
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=fsize * 0.28))
    canvas = Image.blend(canvas, glow_layer, 0.4)

    draw = ImageDraw.Draw(canvas)
    for x, y, ch, inten in cells:
        draw.text((x, y), ch, font=font, fill=_ascii_ramp_color(inten), anchor="mm")

    return data_uri(canvas, fmt="JPEG", quality=88)


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
  <linearGradient id="panelGrad" x1="0" y1="0" x2="0.6" y2="1">
    <stop stop-color="{INK_PANEL_2}"/>
    <stop offset="1" stop-color="{INK_PANEL}"/>
  </linearGradient>
  <linearGradient id="panelGradWarm" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="{INK_PANEL_2}"/>
    <stop offset="1" stop-color="{CLAY_DIM}" stop-opacity=".35"/>
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
    .type{{width:0;animation-name:typeIn;animation-timing-function:steps(1,end);animation-fill-mode:both}}
    .blink-in{{animation-name:blinkIn;animation-timing-function:steps(1,end);animation-iteration-count:infinite;animation-fill-mode:backwards}}
    .zoom{{animation:zoom 16s ease-in-out infinite}}
    @keyframes blink{{50%{{opacity:0}}}}
    @keyframes typeIn{{from{{width:0}}to{{width:var(--tw)}}}}
    @keyframes blinkIn{{0%{{opacity:0}}0.01%,50%{{opacity:1}}50.01%,100%{{opacity:0}}}}
    @keyframes zoom{{0%,100%{{transform:scale(1) translate(0,0)}}50%{{transform:scale(1.045) translate(-0.6%,-0.4%)}}}}
    @keyframes scanY{{from{{transform:translateY(-90px)}}to{{transform:translateY({height + 90}px)}}}}
    @keyframes globalScan{{from{{transform:translateY(-120px)}}to{{transform:translateY({height + 120}px)}}}}
    @keyframes dash{{to{{stroke-dashoffset:-180}}}}
    @keyframes pulse{{0%,100%{{opacity:.4}}50%{{opacity:1}}}}
    @keyframes pulseRing{{0%{{opacity:.6;transform:scale(1)}}100%{{opacity:0;transform:scale(2.4)}}}}
    @keyframes packet1{{0%{{transform:translateX(0)}}100%{{transform:translateX(1030px)}}}}
    @keyframes packet2{{0%{{transform:translateX(0)}}100%{{transform:translateX(-1030px)}}}}
    @keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
    @keyframes sheen{{0%,35%{{transform:translateX(-120%)}}65%,100%{{transform:translateX(120%)}}}}
    @media(prefers-reduced-motion:reduce){{.blink,.scan-y,.global-scan,.dash,.pulse,.pulse-ring,.packet1,.packet2,.rise,.sheen,.zoom{{animation:none!important}}.type{{animation:none!important;width:var(--tw)!important}}.blink-in{{animation:none!important;opacity:1!important}}}}
  </style>
</defs>
"""
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
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


_type_seq = 0


_FONT_FILES = {
    (SERIF, True): "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    (SERIF, False): "/System/Library/Fonts/Supplemental/Georgia.ttf",
    (SANS, True): "/System/Library/Fonts/Helvetica.ttc",
    (SANS, False): "/System/Library/Fonts/Helvetica.ttc",
    (MONO, True): "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
    (MONO, False): "/System/Library/Fonts/Menlo.ttc",
}
_measure_cache: dict[tuple, float] = {}


def _measure_text_width(text: str, size: float, weight: int, family: str) -> float:
    """Real font-metric width via a local proxy font matching the SVG's
    font-family stack, so typing-reveal clip widths don't guess and clip
    text short. Falls back to a generous monospace estimate if unavailable.
    """
    key = (text, size, weight, family)
    if key in _measure_cache:
        return _measure_cache[key]
    try:
        from PIL import ImageFont
        path = _FONT_FILES.get((family, weight >= 700), _FONT_FILES[(MONO, True)])
        font = ImageFont.truetype(path, round(size))
        width = font.getlength(text)
    except Exception:
        width = len(text) * size * 0.62
    _measure_cache[key] = width
    return width


def type_txt(x: float, y: float, value: object, size: float = 16, fill: str = CREAM,
             weight: int = 400, family: str = MONO, anchor: str = "start",
             delay: float = 0.0, duration: float = 1.0) -> list[str]:
    """A text element that reveals like it's being typed (a stepped clip-path
    wipe, not per-character DOM nodes), then holds. One-shot -- it does not
    loop -- so a profile left open doesn't keep re-typing at the viewer.

    Width is measured with a real font (see _measure_text_width) and padded
    generously: a slightly-early finish is invisible, a clipped final letter
    (a proportional serif name rendered as if it were monospace) is not.
    """
    global _type_seq
    _type_seq += 1
    text = str(value)
    tw = _measure_text_width(text, size, weight, family) * 1.18 + 6
    ascent, descent = size * 0.86, size * 0.30
    cid = f"tc{_type_seq}"
    clip_x = x if anchor == "start" else (x - tw if anchor == "end" else x - tw / 2)
    steps = max(1, len(text))
    return [
        f'<clipPath id="{cid}"><rect class="type" x="{clip_x:.1f}" y="{y-ascent:.1f}" height="{ascent+descent:.1f}" '
        f'style="--tw:{tw:.1f}px;animation-duration:{duration}s;animation-delay:{delay}s;'
        f'animation-timing-function:steps({steps},end)"/></clipPath>',
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}" clip-path="url(#{cid})">{esc(text)}</text>',
    ]


def frame_brackets(x: float, y: float, w: float, h: float, accent: str, corner: float = 22) -> str:
    """The corner-bracket motif from the hero, reused on other panels so the
    whole asset set reads as one signature system instead of loose pieces."""
    return (
        f'<path d="M{x} {y+corner}V{y}H{x+corner} '
        f'M{x+w-corner} {y}H{x+w}V{y+corner} '
        f'M{x} {y+h-corner}V{y+h}H{x+corner} '
        f'M{x+w-corner} {y+h}H{x+w}V{y+h-corner}" '
        f'fill="none" stroke="{accent}" stroke-width="2"/>'
    )


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
    # No GitHub button -- linking to GitHub from a page that's already on
    # GitHub is dead weight, and this repo has no third-party badges to
    # justify a "you are here" marker either.
    button("synvolv", "SYNVOLV", "terminal", 160, primary=True)
    button("call", "SCHEDULE A CALL", "calendar", 214, accent=SAGE)
    button("email", "EMAIL", "envelope", 128, accent=CLAY)
    button("linkedin", "LINKEDIN", "brand:linkedin", 152, accent=SAGE)


def write_tech_stack() -> None:
    """Not a flat icon grid -- an actual stack. Layers drawn foundation-first
    (platform/cloud at the base) up to the product surface at top, with a
    glowing marker climbing the spine from bottom to top: the same "a request
    moves through layers, and I know what happens at each one" idea the rest
    of the profile is built around, not just a wall of logos.
    """
    layers = [
        ("PRODUCT SURFACE", "the interface", ["react", "nextdotjs"], CLAY),
        ("OBSERVABILITY", "the visibility", ["grafana", "prometheus"], SAGE),
        ("RUNTIME LANGUAGES", "the execution", ["go", "python", "rust", "typescript"], CLAY),
        ("DATA + MESSAGING", "the state", ["postgresql", "redis", "apachekafka", "rabbitmq"], SAGE),
        ("PLATFORM + CLOUD", "the foundation", ["docker", "kubernetes", "amazonaws", "terraform", "linux", "githubactions"], CLAY),
    ]
    w = 1400
    band_h = 104
    top = 64
    h = top + band_h * len(layers) + 26

    body = [
        txt(28, 34, "yuvraj@runtime:~$ ./stack --trace-request --bottom-up", 13, CLAY, 700),
        txt(w - 28, 34, "the tools; not the identity", 11, MUTED, 650, anchor="end"),
        f'<line x1="28" y1="49" x2="{w-28}" y2="49" stroke="{LINE}"/>',
        frame_brackets(14, 60, w - 28, band_h * len(layers) + 8, CLAY_DIM, corner=16),
    ]

    spine_x = 258
    spine_top, spine_bottom = top + 10, top + band_h * len(layers) - 10
    body += [
        f'<line x1="{spine_x}" y1="{spine_top}" x2="{spine_x}" y2="{spine_bottom}" stroke="{LINE}" stroke-width="1.5"/>',
        f'<path id="stackSpine" d="M{spine_x},{spine_bottom} L{spine_x},{spine_top}" fill="none" stroke="none"/>',
        f'<g filter="url(#glow)"><circle r="5" fill="{CLAY_BRIGHT}"><animateMotion dur="5s" repeatCount="indefinite"><mpath xlink:href="#stackSpine"/></animateMotion></circle></g>',
        txt(spine_x, spine_top - 18, "request", 9.5, MUTED, 650, "middle"),
    ]

    n_layers = len(layers)
    for i, (title, subtitle, icons, accent) in enumerate(layers):
        y0 = top + i * band_h
        cy = y0 + band_h / 2
        body.append(f'<g class="rise" style="animation-delay:{0.08*i:.2f}s">')
        body += [
            f'<rect x="14" y="{y0+2}" width="{w-28}" height="{band_h-4}" fill="url(#panelGrad)"/>',
            txt(46, y0 + 28, f"L{n_layers-i:02d}", 10, accent, 700),
            txt(46, y0 + 52, title, 13.5, CREAM, 800, family=SANS),
            txt(46, y0 + 72, subtitle, 10.5, MUTED, 600),
            f'<circle cx="{spine_x}" cy="{cy}" r="4.5" fill="{accent}"/>',
        ]
        for j, slug in enumerate(icons):
            label, d = ICONS[slug]
            cx = 340 + j * 150
            scale = 30 / 24
            body += [
                f'<g transform="translate({cx-15},{cy-24}) scale({scale:.4f})"><path d="{d}" fill="{CREAM if (i+j) % 2 == 0 else PARCHMENT}"/></g>',
                txt(cx, cy + 22, label, 10, MUTED, 600, "middle", family=SANS),
            ]
        body.append('</g>')
        if i < n_layers - 1:
            body.append(f'<line x1="14" y1="{y0+band_h}" x2="{w-14}" y2="{y0+band_h}" stroke="{LINE_SOFT}"/>')

    (ASSETS / "tech-stack.svg").write_text(
        shell(w, h, "Tech stack",
              "A layered stack diagram from platform and cloud at the foundation up to the product surface, with an animated request climbing through it.", body),
        encoding="utf-8",
    )


def eyebrow(x: float, y: float, label: str, accent: str) -> list[str]:
    """A small tracked label with a leading tick, replacing a fake '$ prompt'
    -- still structured/technical, but reads as editorial, not terminal roleplay."""
    return [
        f'<rect x="{x}" y="{y-11}" width="3" height="13" fill="{accent}"/>',
        txt(x + 12, y, label, 11.5, accent, 700, family=SANS),
    ]


def write_hero(portrait_uri: str) -> None:
    w, h = 1400, 720
    x0, y0, pw, ph = 70, 64, 470, 580
    cx_mid, cy_mid = x0 + pw / 2, y0 + ph / 2
    body: list[str] = [
        f'<rect x="600" y="40" width="770" height="650" fill="url(#rightGlow)"/>',
        f'<clipPath id="portrait"><rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" rx="3"/></clipPath>',
        f'<g clip-path="url(#portrait)">',
        f'<g class="zoom" style="transform-origin:{cx_mid}px {cy_mid}px">',
        f'<image x="{x0}" y="{y0}" width="{pw}" height="{ph}" preserveAspectRatio="xMidYMid slice" href="{portrait_uri}"/>',
        '</g>',
        f'<g class="scan-y"><rect x="{x0}" y="{y0}" width="{pw}" height="2" fill="{CLAY_BRIGHT}" filter="url(#glow)"/><rect x="{x0}" y="{y0+2}" width="{pw}" height="72" fill="url(#scanFadeY)"/></g>',
        '</g>',
        f'<rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" fill="none" stroke="{LINE}" stroke-width="1.5"/>',
    ]

    x = 610
    # Typed reveal, one shot, roughly the pace of someone actually typing it.
    body += type_txt(x, 148, "YUVRAJ SINGH", 52, CREAM, 700, SERIF, delay=0.3, duration=0.7)
    body += type_txt(x, 206, "CHOWDHARY", 52, CREAM, 700, SERIF, delay=1.0, duration=0.55)
    body += [
        f'<clipPath id="sheenClip"><rect x="{x-5}" y="102" width="640" height="118"/></clipPath>',
        f'<g clip-path="url(#sheenClip)"><g class="sheen" style="animation-delay:9s">',
        f'<text x="{x}" y="148" font-family="{SERIF}" font-size="52" font-weight="700" fill="{CREAM_BRIGHT}" opacity=".55">YUVRAJ SINGH</text>',
        f'<text x="{x}" y="206" font-family="{SERIF}" font-size="52" font-weight="700" fill="{CREAM_BRIGHT}" opacity=".55">CHOWDHARY</text>',
        '</g></g>',
    ]

    py = 236
    body += [f'<g class="rise" style="animation-delay:1.6s">'] + pill(x, py, 96, 27, "BUILDER", CLAY) + ['</g>']
    body += [f'<g class="rise" style="animation-delay:1.72s">'] + pill(x+104, py, 226, 27, "INFRASTRUCTURE ENGINEER", SAGE) + ['</g>']
    body += [f'<g class="rise" style="animation-delay:1.84s">'] + pill(x+338, py, 160, 27, "0-TO-1 SYSTEMS", CLAY) + ['</g>']
    body.append(f'<line x1="{x}" y1="288" x2="1350" y2="288" stroke="{LINE}"/>')

    body += type_txt(x, 336, "I build the layer that decides what happens", 23, PARCHMENT, 500, SANS, delay=2.1, duration=1.0)
    body += type_txt(x, 376, "while the request is still alive.", 28, CREAM, 700, SANS, delay=3.15, duration=0.7)
    body += [
        f'<g class="rise" style="animation-delay:3.9s">' + txt(x, 420, "from request edge to ledger · exchange to operator", 13, MUTED, 650) + '</g>',
        f'<g class="rise" style="animation-delay:4.0s">' + txt(x, 444, "AI runtime · quant · blockchain · Linux · control planes", 13, MUTED, 650) + '</g>',
    ]

    body += [f'<g class="rise" style="animation-delay:4.3s">'] + eyebrow(x, 496, "OPERATING PRINCIPLE", SAGE) + ['</g>']
    body += type_txt(x, 534, "OWN THE PATH AFTER 200 OK", 23, CREAM, 800, SANS, delay=4.6, duration=0.85)
    body.append(f'<g class="rise" style="animation-delay:5.55s">' + txt(x, 566, "state / money / latency / recovery / evidence", 12, SAGE_BRIGHT, 650) + '</g>')

    body += [f'<g class="rise" style="animation-delay:5.9s">'] + eyebrow(x, 618, "CURRENT BUILD", CLAY) + ['</g>']
    body += [f'<g class="rise" style="animation-delay:6.1s">'] + pill(x, 632, 128, 30, "SYNVOLV", CLAY, filled=True) + [
        f'<circle cx="{x+16}" cy="647" r="7" fill="none" stroke="{CREAM}" stroke-width="1.4" class="pulse-ring"/>',
        '</g>',
    ]
    body += type_txt(x+142, 652, "builder of the fastest AI gateway, period", 13, CREAM, 700, SANS, delay=6.5, duration=0.85)
    body.append(f'<g class="rise" style="animation-delay:7.45s">' + txt(x, 684, "sub-millisecond authority before a token or a dollar is spent", 12, MUTED, 650) + '</g>')

    (ASSETS / "hero-terminal.svg").write_text(
        shell(w, h, "Yuvraj Singh Chowdhary — builder and infrastructure engineer",
              "A character-mosaic portrait beside a typed identity sequence, on a warm ink / clay / sage editorial layout.", body),
        encoding="utf-8",
    )


def _orbit_xy(cx: float, cy: float, r: float, deg: float) -> tuple[float, float]:
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def bubble(x: float, y: float, w: float, h: float, title: str, lines: list[str], accent: str) -> list[str]:
    out = [
        f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="16" fill="url(#panelGrad)" stroke="{LINE}" stroke-width="1.4"/>',
        f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="3" rx="1.5" fill="{accent}"/>',
        txt(x, y - h/2 + 26, title, 12.5, CREAM, 800, "middle", family=SANS),
    ]
    yy = y - h/2 + 48
    for line in lines:
        out.append(txt(x, yy, line, 10.5, PARCHMENT, 600, "middle"))
        yy += 20
    return out


def write_systems_overview() -> None:
    w, h = 1400, 820
    hub_x, hub_y = 700, 430
    hub_r, tag_r, bubble_r = 95, 165, 310

    body: list[str] = [
        txt(28, 34, "yuvraj@runtime:~$ ./map --career --orbit-view", 13, CLAY, 700),
        txt(1370, 34, "one builder / many layers", 11, MUTED, 650, "end"),
        f'<line x1="28" y1="49" x2="1372" y2="49" stroke="{LINE}"/>',
        frame_brackets(14, 14, w - 28, h - 28, CLAY_DIM, corner=20),
    ]

    # slow-rotating guide rings -- imply the orbit even when nothing else moves
    body += [
        f'<g style="transform-origin:{hub_x}px {hub_y}px">',
        f'<circle cx="{hub_x}" cy="{hub_y}" r="{bubble_r}" fill="none" stroke="{LINE_SOFT}" stroke-width="1" stroke-dasharray="2 10"><animateTransform attributeName="transform" type="rotate" from="0 {hub_x} {hub_y}" to="360 {hub_x} {hub_y}" dur="90s" repeatCount="indefinite"/></circle>',
        '</g>',
        f'<g style="transform-origin:{hub_x}px {hub_y}px">',
        f'<circle cx="{hub_x}" cy="{hub_y}" r="{tag_r}" fill="none" stroke="{LINE_SOFT}" stroke-width="1" stroke-dasharray="1 8"><animateTransform attributeName="transform" type="rotate" from="360 {hub_x} {hub_y}" to="0 {hub_x} {hub_y}" dur="70s" repeatCount="indefinite"/></circle>',
        '</g>',
    ]

    domains = [
        ("PRODUCT / AUTOMATION", ["ship from zero", "workflows + integrations"], SAGE),
        ("BLOCKCHAIN / DEFI", ["signing + replay", "irreversible state"], CLAY),
        ("QUANT / FINANCIAL", ["orders + fills", "ledger + reconciliation"], SAGE),
        ("LINUX / PLATFORM", ["CI + release safety", "diagnostics + images"], CLAY),
        ("AI RUNTIME", ["gateway + streaming", "policy + economics"], SAGE),
    ]
    bw, bh = 190, 88

    # connecting lines + traveling particles, drawn under the bubbles/hub
    for i, (title, lines, accent) in enumerate(domains):
        deg = -90 + i * (360 / len(domains))
        bx, by = _orbit_xy(hub_x, hub_y, bubble_r, deg)
        hx, hy = _orbit_xy(hub_x, hub_y, hub_r + 4, deg)
        pid = f"orbitpath{i}"
        body += [
            f'<path id="{pid}" d="M{bx:.0f},{by:.0f} L{hx:.0f},{hy:.0f}" fill="none" stroke="{LINE}" stroke-width="1.5"/>',
            f'<g filter="url(#glow)">',
            f'<circle r="3.5" fill="{accent}"><animateMotion dur="2.6s" begin="{i*0.4:.1f}s" repeatCount="indefinite"><mpath xlink:href="#{pid}"/></animateMotion></circle>',
            f'<circle r="3.5" fill="{accent}"><animateMotion dur="2.6s" begin="{i*0.4+1.3:.1f}s" repeatCount="indefinite"><mpath xlink:href="#{pid}"/></animateMotion></circle>',
            '</g>',
        ]

    # inner ring: the shared concepts, orbiting as small satellite tags
    concepts = ["CONTROL", "STATE", "MONEY", "LATENCY", "RECOVERY", "OPERATOR"]
    for i, label in enumerate(concepts):
        deg = -90 + i * (360 / len(concepts))
        tx, ty = _orbit_xy(hub_x, hub_y, tag_r, deg)
        accent = CLAY if i % 2 == 0 else SAGE
        tw = 34 + len(label) * 7.6
        body.append(f'<g class="pulse" style="animation-delay:{i*0.35:.2f}s">')
        body += pill(tx - tw/2, ty - 13, tw, 26, label, accent)
        body.append('</g>')

    # hub, drawn last so it sits above the connecting lines
    body += [
        f'<circle cx="{hub_x}" cy="{hub_y}" r="{hub_r+16}" fill="none" stroke="{CLAY_BRIGHT}" stroke-width="1.4" opacity=".5" class="pulse-ring"/>',
        f'<circle cx="{hub_x}" cy="{hub_y}" r="{hub_r}" fill="url(#panelGradWarm)" stroke="{CLAY}" stroke-width="2"/>',
        txt(hub_x, hub_y - 14, "THE COMMON", 15, CLAY, 800, "middle", family=SANS),
        txt(hub_x, hub_y + 10, "LAYER", 22, CREAM, 800, "middle", family=SANS),
        txt(hub_x, hub_y + 34, "5 domains, 1 discipline", 10.5, SAGE_BRIGHT, 650, "middle"),
    ]

    # domain bubbles, staggered reveal, drawn on top of everything
    for i, (title, lines, accent) in enumerate(domains):
        deg = -90 + i * (360 / len(domains))
        bx, by = _orbit_xy(hub_x, hub_y, bubble_r, deg)
        body.append(f'<g class="rise" style="animation-delay:{0.1*i:.2f}s">')
        body += bubble(bx, by, bw, bh, title, lines, accent)
        body.append('</g>')

    (ASSETS / "systems-overview.svg").write_text(
        shell(w, h, "Systems overview",
              "An orbit diagram: product, blockchain, quantitative finance, Linux platform engineering and AI runtime work, converging on one shared control discipline.", body),
        encoding="utf-8",
    )


def write_builder_mode() -> None:
    w, h = 1400, 170
    body = [
        f'<rect x="40" y="24" width="6" height="122" rx="3" fill="{CLAY}"/>',
        txt(70, 60, "$ builder_mode", 13, SAGE, 800),
        txt(70, 98, "understand the business  ->  find the invariant  ->  build  ->  operate  ->  rewrite what reality disproves", 18, CREAM, 700, SANS),
        txt(70, 130, "breadth is not the point; end-to-end ownership is", 12, MUTED, 650),
    ]
    (ASSETS / "builder-mode.svg").write_text(
        shell(w, h, "Builder mode", "How the work actually gets done, end to end.", body),
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
    write_builder_mode()
    write_buttons()
    write_tech_stack()
    # Placeholders exist only to give a brand-new checkout something to show
    # before the "Refresh profile signal" Action has ever run. Once real data
    # is in place, running this script again for unrelated asset changes must
    # never silently blow it away and replace it with "--" placeholders.
    if not (ASSETS / "github-contributions.svg").exists():
        write_placeholder_contributions()
    if not (ASSETS / "github-activity.svg").exists():
        write_placeholder_activity()
    write_social_preview(portrait_uri)
    for name in ["hero-terminal", "systems-overview", "builder-mode", "tech-stack", "github-contributions", "github-activity", "social-preview"]:
        render(f"{name}.svg", f"{name}.png")
    for slug in ["synvolv", "call", "email", "linkedin"]:
        render(f"button-{slug}.svg", f"button-{slug}.png")
    print("built terminal assets")


if __name__ == "__main__":
    main()
