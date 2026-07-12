from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSETS = ROOT / "assets"

errors: list[str] = []

if not README.exists():
    errors.append("README.md is missing")
else:
    text = README.read_text(encoding="utf-8")
    for relative in re.findall(r'(?:src|href)="(\./[^"#?]+)', text):
        target = ROOT / relative[2:]
        if not target.exists():
            errors.append(f"missing README target: {relative}")
    forbidden = ["shields.io", "github-readme-stats", "visitor-badge", "github-profile-trophy"]
    for item in forbidden:
        if item in text.lower():
            errors.append(f"external profile widget found: {item}")

for svg in ASSETS.glob("*.svg"):
    try:
        ET.parse(svg)
    except ET.ParseError as exc:
        errors.append(f"invalid SVG {svg.name}: {exc}")
    content = svg.read_text(encoding="utf-8")
    if re.search(r'\b(?:href|src)="https?://', content):
        errors.append(f"external URL embedded in SVG: {svg.name}")

required = [
    ASSETS / "hero-terminal.svg",
    ASSETS / "systems-overview.svg",
    ASSETS / "builder-mode.svg",
    ASSETS / "github-contributions.svg",
    ASSETS / "github-activity.svg",
    ASSETS / "social-preview.png",
    ROOT / ".github/workflows/profile-signal.yml",
    ROOT / ".github/workflows/profile-check.yml",
]
for path in required:
    if not path.exists():
        errors.append(f"required file missing: {path.relative_to(ROOT)}")

if errors:
    print("profile validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("profile validation passed")
