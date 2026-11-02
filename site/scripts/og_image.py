"""Make the shared share-card image once: python scripts/og_image.py → public/og.png (1200×630). Commit the PNG.
Uses the site's own fonts (Fraunces 600, Inter 400 from @fontsource) and color tokens (global.css, light theme).
No logo, player photo or team element; no URL (the domain may change).
"""
import io
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FILES = ROOT / "node_modules" / "@fontsource"
BG, INK, MUTED, SELL = "#F6F4EE", "#1A1A1A", "#5C5C57", "#A3352A"  # --bg, --ink, --muted, --sell
W, H, PAD = 1200, 630, 80


def font(woff: Path, size: int) -> ImageFont.FreeTypeFont:
    f = TTFont(str(woff))
    f.flavor = None  # woff → plain sfnt so FreeType can read it
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)


title = font(FILES / "fraunces/files/fraunces-latin-600-normal.woff", 128)
body = font(FILES / "inter/files/inter-latin-400-normal.woff", 44)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([PAD, PAD, W - PAD, PAD + 6], fill=INK)  # heavy rule, like the TOP 3 rule on the board
d.text((PAD, 200), "Rebound Lab", font=title, fill=INK)
d.rectangle([PAD, 372, PAD + 120, 378], fill=SELL)  # short brick accent
d.text((PAD, 412), "Which MLB hitters were unlucky,", font=body, fill=INK)
d.text((PAD, 470), "and who just got lucky?", font=body, fill=INK)
d.rectangle([PAD, H - PAD - 2, W - PAD, H - PAD], fill=MUTED)  # thin closing rule

out = ROOT / "public" / "og.png"
img.save(out, optimize=True)
assert Image.open(out).size == (W, H)
print(f"saved {out} ({out.stat().st_size // 1024} KB)")
