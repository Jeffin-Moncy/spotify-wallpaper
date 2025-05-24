import csv, os, time
from hashlib import sha256
from pathlib import Path

CACHE_PATH = Path("spotify_cache.csv")
CACHE_TTL = 60 * 60 * 24 * 7  # 7 days in seconds

def get_cache_key(link):
    return sha256(link.encode()).hexdigest()

def read_cache():
    if not CACHE_PATH.exists():
        return []
    with open(CACHE_PATH, newline="") as f:
        return list(csv.DictReader(f))

def write_cache_row(row):
    cache = read_cache()
    keys = cache[0].keys() if cache else row.keys()
    cache.append(row)
    with open(CACHE_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(cache)

def get_cached_metadata(link):
    cache = read_cache()
    now = time.time()
    key = get_cache_key(link)

    for row in cache:
        if row["key"] == key:
            if now - float(row["timestamp"]) < CACHE_TTL:
                return {
                    "title": row["title"],
                    "artist": row["artist"],
                    "cover_url": row["cover_url"],
                    "song_id": row["song_id"]
                }
    return None

def save_to_cache(link, metadata):
    write_cache_row({
        "key": get_cache_key(link),
        "title": metadata["title"],
        "artist": metadata["artist"],
        "cover_url": metadata["cover_url"],
        "song_id": metadata["song_id"],
        "timestamp": time.time()
    })
