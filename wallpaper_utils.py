# wallpaper_utils.py

import io
import requests
import colorsys
import random
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from colorthief import ColorThief
from pathlib import Path
from gradient_utils import extract_palette, pick_gradient_combos, make_gradient
import time

# ========== CONFIG ==========

CANVAS = (1080, 2400)
CONTROLS_PATH = Path("assets/ui/controls.png")
FONT_PATH = Path("assets/fonts/CircularSpotifyText-Medium.otf") # Replace with Inter or Roboto if needed

# ========== HELPERS ==========

def clean_old_wallpapers(folder="static/output", max_age_minutes=10):
    now = time.time()
    max_age = max_age_minutes * 60

    for file in Path(folder).glob("*.jpg"):
        if file.is_file():
            if now - file.stat().st_mtime > max_age:
                file.unlink()

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

# --- at the top of wallpaper_utils.py if not already ---

def generate_wallpaper(meta, base_name="wallpaper"):
    """
    Creates three wallpaper variations and returns a list of filenames.

    meta = {
        'title':  str,
        'artist': str,
        'cover_url': str,
        'code_url': str
    }
    """
    # ---- CONSTANTS --------------------------------------------------------
    CANVAS        = (1080, 2400)
    OUTPUT_DIR    = Path("static/output")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- 1. Download album-art bytes once ---------------------------------
    art_bytes = requests.get(meta["cover_url"]).content
    art_orig  = Image.open(io.BytesIO(art_bytes)).convert("RGBA")

    # ---- 2. Try Spotify code bar (may be None) ----------------------------
    code_img = None
    try:
        code_img = download_image(meta["code_url"])
    except Exception:
        pass  # silently skip

    # ---- 3. Controls overlay & font --------------------------------------
    controls = strip_black(Image.open(CONTROLS_PATH).convert("RGBA"))
    try:
        font_title  = ImageFont.truetype(str(FONT_PATH), 50)
        font_artist = ImageFont.truetype(str(FONT_PATH), 38)
    except OSError:
        font_title = font_artist = ImageFont.load_default()

    # ---- 4. Build three gradient combos ----------------------------------
    palette = extract_palette(art_bytes)
    combos  = pick_gradient_combos(palette)           # [(c1,c2,mode), …]

    saved_files = []

    for idx, (c1, c2, mode) in enumerate(combos, start=1):
        # (a) Gradient background
        bg = make_gradient(CANVAS, c1, c2, mode)

        # (b) Spotify code (if any)
        if code_img:
            code_w = int(CANVAS[0] * 0.75)
            code   = code_img.resize(
                (code_w, int(code_w * code_img.height / code_img.width)),
                Image.LANCZOS,
            )
            bg.paste(code, ((CANVAS[0] - code_w) // 2, 300), code)

        # (c) Album art
        art_w     = int(CANVAS[0] * 0.76)
        album_top = 950
        art = art_orig.resize((art_w, art_w), Image.LANCZOS)
        bg.paste(art, ((CANVAS[0] - art_w) // 2, album_top), art)

        # (d) Controls overlay
        bg.alpha_composite(controls.resize(CANVAS, Image.LANCZOS))

        # (e) Text
        draw    = ImageDraw.Draw(bg)
        pad_x   = 160
        title_y = 1890
        draw.text((pad_x, title_y),           meta["title"],  font=font_title,  fill="white")
        draw.text((pad_x, title_y + 60),      meta["artist"], font=font_artist, fill=(255,255,255,200))

        # (f) Save
        filename   = f"{base_name}_{idx}.jpg"
        full_path  = OUTPUT_DIR / filename
        bg.convert("RGB").save(full_path, format="JPEG", quality=92)
        saved_files.append(filename)

    return saved_files
