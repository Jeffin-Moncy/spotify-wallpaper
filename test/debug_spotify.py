from spotify_utils import get_spotify_metadata

link = input("Paste your Spotify track or album link: ")
meta = get_spotify_metadata(link)

if meta:
    print("✅ Metadata:")
    print(meta)
else:
    print("❌ Failed to get metadata.")
