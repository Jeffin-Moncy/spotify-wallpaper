from spotify_utils import get_spotify_metadata
from wallpaper_utils import generate_wallpaper

link = "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"
meta = get_spotify_metadata(link)
generate_wallpaper(meta, "preview.jpg")
print("Done! Saved as preview.jpg")
