from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BG = "#0d1117"
GREEN = "#42ff78"
GREEN_MID = "#27c957"
GREEN_DIM = "#12672d"
TEXT = "#dce7df"
MUTED = "#9aaba0"


def font(mono: bool, size: int, bold: bool = False):
    if mono:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    else:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)


def wrapped(draw, x, y, value, width=88, f=None, fill=TEXT, gap=8):
    f = f or font(False, 18)
    asc, desc = f.getmetrics()
    step = asc + desc + gap
    for paragraph in value.split("\n"):
        lines = textwrap.wrap(paragraph, width=width, break_long_words=False) if paragraph else [""]
        for line in lines:
            draw.text((x, y), line, font=f, fill=fill)
            y += step
    return y


def image_scaled(name: str, width: int) -> Image.Image:
    img = Image.open(ASSETS / name).convert("RGB")
    ratio = width / img.width
    return img.resize((width, int(img.height * ratio)), Image.Resampling.LANCZOS)


def rule(draw, y, left, right):
    draw.line((left, y, right, y), fill=GREEN_DIM)


def heading(draw, y, text, margin, hfont):
    rule(draw, y, margin, 1160 - margin)
    y += 28
    draw.text((margin, y), text, font=hfont, fill=GREEN)
    return y + 44


def main():
    width, margin = 1160, 44
    content_w = width - 2 * margin
    hero = image_scaled("hero-terminal.png", content_w)
    overview = image_scaled("systems-overview.png", content_w)
    contrib = image_scaled("github-contributions.png", content_w)
    activity = image_scaled("github-activity.png", content_w)

    canvas = Image.new("RGB", (width, 7600), BG)
    d = ImageDraw.Draw(canvas)
    hfont = font(True, 22, True)
    bfont = font(False, 18)
    bold = font(False, 18, True)
    mfont = font(True, 15)
    small = font(True, 13)

    y = 28
    canvas.paste(hero, (margin, y)); y += hero.height + 24
    d.text((margin, y), "synvolv  ·  schedule a call  ·  email  ·  linkedin", font=mfont, fill=GREEN_MID); y += 48

    y = heading(d, y, "$ cat /home/yuvraj/about", margin, hfont)
    intro = (
        "Most people try to place me in one box. Backend. Infrastructure. AI. Quant. Blockchain. Founder.\n\n"
        "The honest answer is that I keep following a system until I reach the layer that can actually fail the business.\n\n"
        "I have built products, DeFi flows, exchange and broker integrations, order and fill state machines, reconciliation, risk monitors, Linux release tooling, distributed backends, AI gateways, policy engines, ledgers and operator control planes. Not because I collect stacks. Each problem simply pulled me one layer deeper."
    )
    y = wrapped(d, margin, y, intro, f=bfont); y += 18
    d.text((margin, y), "make the important state explicit", font=mfont, fill=GREEN); y += 27
    d.text((margin, y), "keep the system honest under pressure", font=mfont, fill=GREEN); y += 27
    d.text((margin, y), "own the path after the endpoint returns 200 OK", font=mfont, fill=GREEN); y += 42
    y = wrapped(d, margin, y, "I like starting from zero: empty repository, ugly first diagram, incomplete requirements, and a customer describing the problem with the wrong nouns. That is usually where my best work begins.", f=bfont); y += 28

    canvas.paste(overview, (margin, y)); y += overview.height + 34

    y = heading(d, y, "$ less /var/log/the-long-way-here.log", margin, hfont)
    body = (
        "Small products taught me speed. Automation taught me that a boring five-minute task becomes infrastructure the moment a team quietly depends on it.\n\n"
        "Blockchain and DeFi changed the cost of being careless. A bad retry, stale nonce, loose signing boundary or confused chain state can turn a small software mistake into irreversible truth.\n\n"
        "Markets and financial operations changed my standards again. Exchanges disagree. Orders are accepted before they are settled. Fills arrive out of order. Balances drift. So I built the layer around the APIs: normalized state, reconciliation, cash checks, risk, reporting and control rooms.\n\n"
        "Linux taught me to make the fix reproducible. AI infrastructure then brought almost every earlier lesson into the same request path."
    )
    y = wrapped(d, margin, y, body, f=bfont); y += 30

    y = heading(d, y, "$ ./inspect --builder --all-layers", margin, hfont)
    y = wrapped(d, margin, y, "I am an infrastructure engineer in the broad, old-fashioned meaning of the word. I care about the things underneath a product, between its components and immediately after it fails.", f=bfont); y += 18
    for line in [
        "request paths        gateways / streaming / routing / rate control",
        "financial state      ledgers / reconciliation / cash / risk",
        "market connectivity  exchanges / brokers / orders / fills",
        "control systems      policy / budgets / audit / operator actions",
        "reliability          retries / idempotency / recovery / observability",
        "platform work        Linux / CI / release validation / deployment",
    ]:
        d.text((margin, y), line, font=small, fill=GREEN_MID); y += 26
    y += 10
    y = wrapped(d, margin, y, "A lot of software is locally correct and globally wrong. Every service returns success. Every dashboard is green. The customer still lost money, the balance still drifted, or the retry still duplicated the action. I build against that class of failure.", f=bfont); y += 30

    y = heading(d, y, "$ cat /srv/synvolv/WHY", margin, hfont)
    body = (
        "Synvolv is what happened when that systems instinct met production AI. I founded it because teams had SDKs, gateways, logs and monthly bills, but very little authority while the request was still alive.\n\n"
        "I architected the gateway and control plane from an empty repository: OpenAI-compatible ingress, provider normalization, streaming, tenant identity, budgets, policy, routing, fallback, metering, cost attribution, audit and operator controls.\n\n"
        "I built one of the fastest AI gateway control paths I know of in production: about 456 microseconds of average measured overhead on our path while still making real decisions."
    )
    y = wrapped(d, margin, y, body, f=bfont); y += 20
    d.rectangle((margin, y, width-margin, y+132), outline=GREEN_DIM, fill="#071109")
    metrics = [
        "17M+     LLM requests / month",
        "~456 us  average measured gateway overhead",
        "200+     models across providers and custom endpoints",
        "$65M     AUM supported by quant operating infrastructure",
    ]
    yy = y + 20
    for line in metrics:
        d.text((margin+20, yy), line, font=mfont, fill=GREEN_MID); yy += 27
    y += 162

    y = heading(d, y, "$ cat ~/.notes-from-systems-that-fought-back", margin, hfont)
    notes = [
        "The happy path proves the demo. The recovery path proves the product.",
        "A retry is a new state transition.",
        "A ledger is the answer you can still defend after two systems disagree.",
        "Tail latency is where a clean architecture stops being polite.",
        "If a control cannot change the outcome, it is a report.",
        "The operator is part of the system.",
        "Fast code with slow recovery is not a fast system.",
        "The best infrastructure is boring because the hard thinking happened early.",
    ]
    for i, note in enumerate(notes, 1):
        d.text((margin, y), f"{i:02d}", font=mfont, fill=GREEN)
        y = wrapped(d, margin+48, y, note, width=82, f=bfont)
        y += 5
    y += 18
    y = wrapped(d, margin, y, "I care about performance, but not benchmark theatre. I care about correctness, but not the kind that ends when the tests turn green. And I care about taste: sharp names, fewer knobs, explicit ownership, small hot paths, useful logs and no magic state.", f=bfont); y += 30

    y = heading(d, y, "$ git log --all --author=yuvraj --stat", margin, hfont)
    y = wrapped(d, margin, y, "Real public contribution history and recent activity are generated inside the profile repository by GitHub Actions.", f=bfont); y += 22
    canvas.paste(contrib, (margin, y)); y += contrib.height + 20
    canvas.paste(activity, (margin, y)); y += activity.height + 32

    y = heading(d, y, "$ ./connect --problem-has-teeth", margin, hfont)
    y = wrapped(d, margin, y, "Bring me the gateway that must disappear under load, the financial workflow nobody trusts, the exchange integration with six definitions of account state, or the internal operation held together by a spreadsheet and one person's memory.", f=bfont); y += 24
    d.text((margin, y), "cal.com/heyyuvraj/chat  ·  chowdharyyuvrajsingh@gmail.com", font=mfont, fill=GREEN_MID); y += 34
    d.text((margin, y), "yuvraj@runtime:~$ █", font=mfont, fill=GREEN); y += 44

    out = canvas.crop((0, 0, width, y + 24))
    out.save(ROOT / "profile-preview.png", quality=95)
    print(ROOT / "profile-preview.png")


if __name__ == "__main__":
    main()
