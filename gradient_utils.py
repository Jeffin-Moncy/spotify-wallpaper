# gradient_utils.py
import io
import colorsys
import random
from PIL import Image, ImageDraw
from colorthief import ColorThief
import colorsys
import numpy as np


# Extract a palette of usable colors from an image
def extract_palette(img_bytes, count=6):
    """Extract a palette of usable colors."""
    ct = ColorThief(io.BytesIO(img_bytes))
    palette = ct.get_palette(color_count=count)
    return palette

# Remove near-white, near-black, and overly dull colors from a palette
def filter_colors(palette):
    """Remove near-white, near-black, and overly dull colors."""
    filtered = []
    for r, g, b in palette:
        brightness = (r + g + b) / 3
        saturation = max(abs(r - g), abs(g - b), abs(b - r))
        if 40 < brightness < 220 and saturation > 10:
            filtered.append((r, g, b))
    return filtered if filtered else palette

# Generate 3 color pairs and gradient modes from a palette
def pick_gradient_combos(palette, features):
    modes = ["linear", "radial", "diagonal", "dual-radial", "shape-blur"]
    combos = []

    for _ in range(3):
        c1 = random.choice(palette)
        c2 = random.choice([c for c in palette if c != c1])
        mode = random.choice(modes)
        combos.append((c1, c2, mode))

    return combos

def extract_color_features(rgb):
    r, g, b = [x / 255 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hue_deg = int(h * 360)

    if hue_deg < 40 or hue_deg > 320:
        warmth = "warm"
    elif 150 <= hue_deg <= 250:
        warmth = "cool"
    else:
        warmth = "neutral"

    return {
        "hue": hue_deg,
        "brightness": round(v, 2),
        "warmth": warmth
    }

# Create a gradient image (linear or radial) between two colors
def make_gradient(size, c1, c2, mode="linear"):
    W, H = size
    base = Image.new("RGB", size, c1)
    top = Image.new("RGB", size, c2)

    if mode == "radial":
        mask = Image.radial_gradient("L").resize(size)

    elif mode == "diagonal":
        mask = Image.linear_gradient("L").rotate(45, expand=True).crop((0, 0, W, H))

    elif mode == "dual-radial":
        mask = Image.new("L", size)
        cx1, cy1 = int(W * 0.3), int(H * 0.3)
        cx2, cy2 = int(W * 0.7), int(H * 0.7)
        rx, ry = np.ogrid[:H, :W]
        dist1 = ((rx - cy1)**2 + (ry - cx1)**2)**0.5
        dist2 = ((rx - cy2)**2 + (ry - cx2)**2)**0.5
        dist = np.minimum(dist1, dist2)
        dist = (dist / dist.max() * 255).astype("uint8")
        mask.putdata(dist.flatten())

    elif mode == "shape-blur":
    # concentric diamond blur - fades from centre-diamond to edges
        mask = Image.new("L", size)
        cx, cy = W // 2, H // 2
        for y in range(H):
            for x in range(W):
                d = abs(x - cx) + abs(y - cy)          # Manhattan distance ⇒ diamond
                mask.putpixel((x, y), int(d / (cx + cy) * 255))


    else:
        mask = Image.linear_gradient("L").resize(size)

    return Image.composite(top, base, mask).convert("RGBA")
