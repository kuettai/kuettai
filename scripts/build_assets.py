"""Build the profile's SVG assets (banner, project cards, score track) in dark and light variants.

Text is converted to outlines with the bundled Fredoka font (SIL OFL, see fonts/OFL.txt),
so the SVGs look identical everywhere GitHub shows them, with no font loading.

    python3 -m venv .venv && .venv/bin/pip install fonttools
    .venv/bin/python scripts/build_assets.py
"""
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path(__file__).resolve().parent / "fonts"
ASSETS = ROOT / "assets"
W = 1000

MEEPLE = ("M50 5 C60 5 66 12 66 22 C66 28 63 32 60 35 L88 44 C96 47 97 58 88 60 L70 62 L82 92 "
          "C84 97 80 100 75 100 L58 100 L50 84 L42 100 L25 100 C20 100 16 97 18 92 L30 62 L12 60 "
          "C3 58 4 47 12 44 L40 35 C37 32 34 28 34 22 C34 12 40 5 50 5 Z")
STAR = "M0 -10 L2.9 -4 L9.5 -3.1 L4.7 1.5 L5.9 8.1 L0 5 L-5.9 8.1 L-4.7 1.5 L-9.5 -3.1 L-2.9 -4 Z"

THEMES = {
    "dark": dict(bg="#2B1D14", edge="#6B4A33", grain="#F1E3C8", text="#F1E3C8", muted="#D8C3A0",
                 name="#F4A261", pip="#2B1D14", die="#F1E3C8",
                 red="#E63946", orange="#F4A261", teal="#2A9D8F", blue="#5B93B8", purple="#9D8CCB"),
    "light": dict(bg="#F6EBD6", edge="#B89A72", grain="#5A4330", text="#2B1D14", muted="#5A4330",
                  name="#A4521A", pip="#F6EBD6", die="#3D2C1E",
                  red="#C62F3B", orange="#B85F18", teal="#1F7A70", blue="#33658A", purple="#6F5DA8"),
}
TRACK = ["red", "orange", "teal", "blue", "purple"]


class Face:
    def __init__(self, path):
        font = TTFont(path)
        self.glyphs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self.upem = font["head"].unitsPerEm
        self.hmtx = font["hmtx"]

    def _glyph(self, ch):
        name = self.cmap.get(ord(ch))
        if name is None:
            raise ValueError(f"glyph missing for {ch!r}")
        return name

    def width(self, text, size, track=0.0):
        adv = sum(self.hmtx[self._glyph(c)][0] for c in text) * size / self.upem
        return adv + track * size * max(len(text) - 1, 0)

    def path(self, text, x, y, size, fill, track=0.0, anchor="start"):
        if anchor == "middle":
            x -= self.width(text, size, track) / 2
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        scale = size / self.upem
        for ch in text:
            name = self._glyph(ch)
            self.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
            x += self.hmtx[name][0] * scale + track * size
        return f'<path fill="{fill}" d="{pen.getCommands()}"/>'

    def wrap(self, text, size, max_width):
        lines, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if cur and self.width(trial, size) > max_width:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return lines + [cur]


REG = Face(FONTS / "Fredoka-400.ttf")
BOLD = Face(FONTS / "Fredoka-600.ttf")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def svg(h, title, body, style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
            f'role="img" aria-labelledby="t"><title id="t">{esc(title)}</title>{style}{body}</svg>\n')


def meeple(x, y, scale, fill, cls=""):
    inner = f'<path d="{MEEPLE}" fill="{fill}"/>'
    if cls:
        inner = f'<g class="{cls}">{inner}</g>'
    return f'<g transform="translate({x} {y}) scale({scale})">{inner}</g>'


def table(h, t):
    return (f'<rect x="1.5" y="1.5" width="{W - 3}" height="{h - 3}" rx="28" fill="{t["bg"]}" '
            f'stroke="{t["edge"]}" stroke-width="3"/>')


MOTION = """<style>
@media (prefers-reduced-motion: no-preference) {
  .hop { animation: hop .7s cubic-bezier(.22,1,.36,1) 2 both; }
  .d1 { animation-delay: .15s } .d2 { animation-delay: .3s } .d3 { animation-delay: .45s } .d4 { animation-delay: .6s }
  .roll { transform-box: fill-box; transform-origin: center; animation: roll 1.4s cubic-bezier(.22,1,.36,1) .2s both; }
}
@keyframes hop { 0%, 100% { transform: translateY(0) } 45% { transform: translateY(-30px) } }
@keyframes roll { 0% { transform: rotate(0) } 75% { transform: rotate(380deg) } 100% { transform: rotate(360deg) } }
</style>"""


def banner(t):
    h = 400
    lines = [
        BOLD.path("KuetTai", 56, 168, 128, t["name"]),
        BOLD.path("Solutions Architect at AWS", 58, 236, 44, t["text"]),
        REG.path("Malaysia · game night tinkerer", 58, 290, 34, t["muted"]),
    ]
    for text, face, size in (("KuetTai", BOLD, 128), ("Solutions Architect at AWS", BOLD, 44),
                             ("Malaysia · game night tinkerer", REG, 34)):
        assert 58 + face.width(text, size) < 620, f"banner text too wide: {text}"
    grain = "".join(f'<path d="M0 {y} L{W} {y + d}" stroke="{t["grain"]}" stroke-opacity=".06" stroke-width="2"/>'
                    for y, d in ((70, -4), (130, 5), (200, -3), (330, 4)))
    squares = "".join(f'<rect x="{44 + i * 48}" y="362" width="44" height="18" rx="5" '
                      f'fill="{t[TRACK[i % 5]]}" fill-opacity=".55"/>' for i in range(19))
    cast = "".join(meeple(604 + i * 74, 290, 0.72, t[c], f"hop d{i}" if i else "hop")
                   for i, c in enumerate(TRACK))
    pips = "".join(f'<circle cx="{x}" cy="{y}" r="5.5" fill="{t["pip"]}"/>'
                   for x, y in ((-15, -15), (15, -15), (0, 0), (-15, 15), (15, 15)))
    die = (f'<g transform="translate(918 84)"><g class="roll"><rect x="-32" y="-32" width="64" height="64" '
           f'rx="12" fill="{t["die"]}"/>{pips}</g></g>')
    body = table(h, t) + grain + squares + "".join(lines) + die + cast
    return svg(h, "KuetTai, Solutions Architect at AWS, Malaysia, game night tinkerer", body, MOTION)


def card(t, tag, title, desc, meta, accent, legendary=False):
    tx, tw = 200, W - 200 - 44
    body_lines = REG.wrap(desc, 34, tw)
    assert len(body_lines) <= 3, f"{title}: description too long"
    assert BOLD.width(title, 54) < tw and REG.width(meta, 30) < tw
    y_tag, y_title = 66, 128
    y_body = [y_title + 54 + i * 44 for i in range(len(body_lines))]
    y_meta = y_body[-1] + 52
    h = y_meta + 44
    col = t[accent]
    tag_x = tx
    parts = [table(h, t)]
    if legendary:
        parts.append(f'<rect x="14" y="14" width="{W - 28}" height="{h - 28}" rx="18" fill="none" '
                     f'stroke="{col}" stroke-width="2.5"/>')
        parts[0] = parts[0].replace(f'stroke="{t["edge"]}" stroke-width="3"', f'stroke="{col}" stroke-width="6"')
        parts.append(f'<path d="{STAR}" transform="translate({tx + 11} {y_tag - 9}) scale(1.15)" fill="{col}"/>')
        tag_x = tx + 32
    else:
        parts[0] = parts[0].replace(f'stroke="{t["edge"]}"', f'stroke="{col}"')
    parts += [
        BOLD.path(tag, tag_x, y_tag, 26, t["muted"], track=0.12),
        BOLD.path(title, tx, y_title, 54, t["text"]),
        *[REG.path(line, tx, y, 34, t["text"]) for line, y in zip(body_lines, y_body)],
        REG.path(meta, tx, y_meta, 30, t["muted"]),
        meeple(48, (h - 120) / 2, 1.2, col),
    ]
    return svg(h, f"{title}: {desc}", "".join(parts))


def score(t):
    stops = [("1,500+", "contributions"), ("500+", "stars on|Service Screener"),
             ("130+", "forks of|Service Screener"), ("20+", "public repos")]
    h = 330
    squares = "".join(f'<rect x="{44 + i * 48}" y="152" width="44" height="22" rx="5" '
                      f'fill="{t[TRACK[i % 5]]}" fill-opacity=".45"/>' for i in range(19))
    parts = [table(h, t), squares]
    for i, (value, label) in enumerate(stops):
        cx = 135 + i * 243
        parts.append(meeple(cx - 45, 62, 0.9, t[TRACK[i]]))
        parts.append(BOLD.path(value, cx, 228, 42, t["text"], anchor="middle"))
        for j, line in enumerate(label.split("|")):
            parts.append(REG.path(line, cx, 266 + j * 32, 26, t["muted"], anchor="middle"))
    alt = "Score track: " + ", ".join(f"{v} {l.replace('|', ' ')}" for v, l in stops)
    return svg(h, alt, "".join(parts))


CARDS = [
    ("service-screener-v2", "LEGENDARY", "Service Screener v2",
     "Scans your AWS account against AWS and community best practices and tells you exactly what to fix.",
     "Python · AWS Samples · 500+ stars · 130+ forks", "orange", True),
    ("kirocredit", "EXPANSION", "kirocredit",
     "Unofficial guide to redeeming Kiro promo codes and fixing common errors.",
     "Live guide · HTML", "red", False),
    ("ktws", "EXPANSION", "ktws",
     "Hands-on workshops: build MCP servers and AI agents on AWS.",
     "Workshops · Python", "teal", False),
    ("bgrules", "GAME NIGHT", "bgrules",
     "Board game rules for quick lookup at the table, or a refresher before game night.",
     "Live tool · HTML", "blue", False),
    ("boardgame-timer", "GAME NIGHT", "boardgame-timer",
     "Installable, offline turn timer: track each player's total time, or count down turns and rounds.",
     "Live app · JavaScript", "purple", False),
]

if __name__ == "__main__":
    (ASSETS / "cards").mkdir(parents=True, exist_ok=True)
    for mode, t in THEMES.items():
        (ASSETS / f"banner-{mode}.svg").write_text(banner(t))
        (ASSETS / f"score-{mode}.svg").write_text(score(t))
        for slug, *spec in CARDS:
            (ASSETS / "cards" / f"{slug}-{mode}.svg").write_text(card(t, *spec))
    print("built", len(list(ASSETS.rglob("*.svg"))), "svg files")
