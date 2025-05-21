# test_spotify.py

from spotify_utils import get_spotify_metadata

url = "https://open.spotify.com/track/6qr6qpP9J9YBBYsVmJFd5c?si=bd2f9a7cefd74a5e"  # Example: Eminem - Without Me
data = get_spotify_metadata(url)

print(data)
