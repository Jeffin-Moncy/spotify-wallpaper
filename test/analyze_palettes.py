from PIL import Image
from colorthief import ColorThief
import matplotlib.pyplot as plt
from pathlib import Path

# Folder where your wallpapers are stored
folder = Path("manual")  # ← change this

# Pick a few files for analysis
wallpapers = sorted(folder.glob("*.jpg"))

def extract_palette(img_path, color_count=6):
    ct = ColorThief(str(img_path))
    return ct.get_palette(color_count=color_count)

def plot_palettes(image_paths):
    fig, axes = plt.subplots(len(image_paths), 1, figsize=(6, 2.5 * len(image_paths)))

    for ax, path in zip(axes, image_paths):
        palette = extract_palette(path)
        for i, color in enumerate(palette):
            ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=[c / 255 for c in color]))
        ax.set_xlim(0, len(palette))
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.set_title(path.name, fontsize=10)

    plt.tight_layout()
    plt.show()

plot_palettes(wallpapers[:4])  # show first 5
