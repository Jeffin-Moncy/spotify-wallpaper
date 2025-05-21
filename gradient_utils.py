# gradient_utils.py

import io
import colorsys
import random
from PIL import Image, ImageDraw
from colorthief import ColorThief

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
def pick_gradient_combos(palette):
    """Generate 3 color pairs + modes from palette."""
    combos = []
    palette = filter_colors(palette)

    for i in range(3):
        c1 = random.choice(palette)
        c2 = random.choice([c for c in palette if c != c1])
        mode = random.choice(["linear", "radial"])
        combos.append((c1, c2, mode))

    return combos

# Create a gradient image (linear or radial) between two colors
def make_gradient(size, c1, c2, mode="linear"):
    W, H = size
    base = Image.new("RGB", size, c1)
    top = Image.new("RGB", size, c2)

    if mode == "radial":
        mask = Image.radial_gradient("L").resize(size)
    else:
        mask = Image.linear_gradient("L").resize(size)

    return Image.composite(top, base, mask).convert("RGBA")
