"""Generate tabletop-style project cards into assets/cards/. Run: python3 scripts/make_cards.py"""
from pathlib import Path
from textwrap import wrap
from html import escape

OUT = Path(__file__).resolve().parent.parent / "assets" / "cards"
MEEPLE = ("M50 5 C60 5 66 12 66 22 C66 28 63 32 60 35 L88 44 C96 47 97 58 88 60 L70 62 L82 92 "
          "C84 97 80 100 75 100 L58 100 L50 84 L42 100 L25 100 C20 100 16 97 18 92 L30 62 L12 60 "
          "C3 58 4 47 12 44 L40 35 C37 32 34 28 34 22 C34 12 40 5 50 5 Z")
FONT = "Trebuchet MS, Verdana, sans-serif"
LANG_COLORS = {"Python": "#3776AB", "JavaScript": "#F1E05A", "TypeScript": "#3178C6", "HTML": "#E34C26"}

CARDS = [
    # slug, title, kind, description, language, accent, width
    ("service-screener-v2", "Service Screener v2", "LEGENDARY",
     "Scans your AWS account against AWS and community best practices and tells you exactly what to fix.",
     "Python", "#F4A261", 820),
    ("kirocredit", "kirocredit", "EXPANSION",
     "Unofficial guide to redeeming Kiro promo codes and fixing common errors.", "HTML", "#E63946", 400),
    ("ktws", "ktws", "EXPANSION",
     "Hands-on workshops: build MCP servers and AI agents on AWS.", "Python", "#2A9D8F", 400),
]


def card(title, kind, desc, lang, accent, width):
    h = 190 if width > 500 else 200
    chars = int((width - 150) / (15 * 0.52))
    lines = wrap(desc, chars)[:3]
    desc_svg = "".join(
        f'<text x="32" y="{88 + i * 22}" font-family="{FONT}" font-size="15" fill="#F1E3C8">{escape(l)}</text>'
        for i, l in enumerate(lines))
    legendary = kind == "LEGENDARY"
    border = f'stroke="{accent}" stroke-width="{4 if legendary else 2}"'
    shine = ('<animate attributeName="stroke-opacity" values="1;0.4;1" dur="3s" repeatCount="indefinite"/>'
             if legendary else "")
    lang_color = LANG_COLORS.get(lang, "#999")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {h}" width="{width}" height="{h}" role="img" aria-label="{escape(title)}: {escape(desc)}">
  <rect x="3" y="3" width="{width - 6}" height="{h - 6}" rx="16" fill="#2B1D14" {border}>{shine}</rect>
  <rect x="3" y="3" width="{width - 6}" height="50" rx="16" fill="{accent}" fill-opacity="0.18"/>
  <text x="32" y="38" font-family="{FONT}" font-size="22" font-weight="bold" fill="{accent}">{escape(title)}</text>
  <text x="{width - 32}" y="36" text-anchor="end" font-family="{FONT}" font-size="12" font-weight="bold" letter-spacing="2" fill="#F1E3C8" fill-opacity="0.7">{"★ " if legendary else ""}{kind}</text>
  {desc_svg}
  <circle cx="38" cy="{h - 30}" r="6" fill="{lang_color}"/>
  <text x="52" y="{h - 25}" font-family="{FONT}" font-size="14" fill="#F1E3C8" fill-opacity="0.8">{lang}</text>
  <path d="{MEEPLE}" transform="translate({width - 78} {h - 78}) scale(0.5)" fill="{accent}"/>
</svg>
'''


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, *rest in CARDS:
        (OUT / f"{slug}.svg").write_text(card(*rest))
        print("wrote", OUT / f"{slug}.svg")
