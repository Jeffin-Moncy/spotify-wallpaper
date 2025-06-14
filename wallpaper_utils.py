# wallpaper_utils.py

import io, uuid, requests, re
import colorsys
import random
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from colorthief import ColorThief
from pathlib import Path
from gradient_utils import extract_palette, pick_gradient_combos, make_gradient, extract_color_features

# ========== CONFIG ==========

CONTROLS_PATH = Path("assets/ui/controls.png")
FONT_PATH = Path("assets/fonts/CircularSpotifyText-Medium.otf") # Replace with Inter or Roboto if needed

# ========== HELPERS ==========

def clean_old_wallpapers(folder="static/output", ttl_min=60):
    import time
    limit = time.time() - ttl_min * 60

    for fp in Path(folder).glob("*.jpg"):
        if fp.stat().st_mtime < limit:
            fp.unlink(missing_ok=True)

def nice_filename(title: str, variant: int) -> str:
    base = re.sub(r'\W+', '_', title)[:30]           # sanitize + trim
    tag  = uuid.uuid4().hex[:6]
    return f"{base}_{variant}_{tag}.jpg"

def download_image(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if "image" not in response.headers.get("Content-Type", ""):
        raise ValueError(f"URL did not return an image: {url}")
    return Image.open(io.BytesIO(response.content)).convert("RGBA")

def strip_black(img):
    """Make pure black pixels fully transparent."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if r < 10 and g < 10 and b < 10:
                px[x, y] = (0, 0, 0, 0)
    return img

def pick_gradient_colors(art_bytes):
    ct = ColorThief(io.BytesIO(art_bytes))
    palette = ct.get_palette(color_count=6, quality=1)
    hsv = [colorsys.rgb_to_hsv(*[c / 255 for c in rgb]) for rgb in palette]
    sorted_by_brightness = sorted(zip(palette, hsv), key=lambda t: t[1][2])
    c1 = sorted_by_brightness[0][0]  # darkest
    c2 = sorted_by_brightness[-1][0]  # brightest
    if abs(c1[0] - c2[0]) < 20:
        c2 = random.choice(palette)
    return c1, c2

def make_vertical_gradient(size, rgb_top, rgb_bottom):
    W, H = size
    base = Image.new("RGB", size, rgb_top)
    top = Image.new("RGB", size, rgb_bottom)
    mask = Image.linear_gradient("L").resize(size)
    return Image.composite(top, base, mask)

# ========== MAIN FUNCTION ==========

def generate_wallpaper(meta, base_name="wallpaper", session_id=None):
    """
    Creates three wallpaper variations and returns a list of filenames.
    Logs every variant to all_log.csv with chosen = 0.

    meta = {
        "title":   str,
        "artist":  str,
        "cover_url": str,
        "song_id": str
    }
    """
    # ── CONSTANTS ──────────────────────────────────────────────────────────
    CANVAS     = (1080, 2400)
    OUTPUT_DIR = Path("static/output")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Session ID ────────────────────────────────────────────────────────
    if session_id is None:
        session_id = uuid.uuid4().hex

    # ── 1. Album art (download once) ──────────────────────────────────────
    art_bytes = requests.get(meta["cover_url"]).content
    art_orig  = Image.open(io.BytesIO(art_bytes)).convert("RGBA")

    # ── 2. Overlays & fonts ───────────────────────────────────────────────
    controls = strip_black(Image.open(CONTROLS_PATH).convert("RGBA"))
    try:
        font_title  = ImageFont.truetype(str(FONT_PATH), 50)
        font_artist = ImageFont.truetype(str(FONT_PATH), 38)
    except OSError:
        font_title = font_artist = ImageFont.load_default()

    # ── 3. Gradient combos ────────────────────────────────────────────────
    palette   = extract_palette(art_bytes)
    dominant  = ColorThief(io.BytesIO(art_bytes)).get_color(quality=1)
    features  = extract_color_features(dominant)
    combos    = pick_gradient_combos(palette, features)[:3]   # only 3 variants

    saved_files  = []

    for idx, (c1, c2, mode) in enumerate(combos, start=1):
        # (a) Gradient background
        bg = make_gradient(CANVAS, c1, c2, mode)

        # (b) Album art
        art_w     = int(CANVAS[0] * 0.76)
        album_top = 950
        art = art_orig.resize((art_w, art_w), Image.LANCZOS)
        bg.paste(art, ((CANVAS[0] - art_w) // 2, album_top), art)

        # (c) Controls overlay
        bg.alpha_composite(controls.resize(CANVAS, Image.LANCZOS))

        # (d) Text
        draw  = ImageDraw.Draw(bg)
        pad_x = 160
        draw.text((pad_x, 1890), meta["title"],  font=font_title,  fill="white")
        draw.text((pad_x, 1950), meta["artist"], font=font_artist, fill=(255,255,255,200))

        # (e) Save
        filename  = nice_filename(meta["title"], idx)
        full_path = OUTPUT_DIR / filename
        bg.convert("RGB").save(full_path, "JPEG", quality=92)

        saved_files.append(filename)


    return saved_files