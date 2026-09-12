import json
from pathlib import Path

PROJECT = Path(r"C:\Users\maria\side-one-track-one")

SOURCE = PROJECT / "data" / "albums-clean.json"
OUTPUT = PROJECT / "data" / "albums.js"

with SOURCE.open("r", encoding="utf-8") as f:
    albums = json.load(f)


# Preserve any hand-curated albums already in the game. MusicBrainz can leave
# a seed unresolved because of title or artist-credit ambiguity; that should
# never make a known-good album disappear from Track Record.
existing_albums = []

if OUTPUT.exists():
    existing_text = OUTPUT.read_text(encoding="utf-8").strip()

    if existing_text.startswith("const ALBUMS = "):
        existing_json = existing_text[len("const ALBUMS = "):]
        if existing_json.endswith(";"):
            existing_json = existing_json[:-1]
        existing_albums = json.loads(existing_json)


def album_key(album):
    return (album["artist"].casefold(), album["album"].casefold())


existing_by_key = {
    album_key(album): album
    for album in existing_albums
}

merged_albums = []
seen = set()

for album in albums:
    key = album_key(album)
    existing = existing_by_key.get(key, {})
    merged = {**existing, **album}

    # A missing MusicBrainz date must not erase a verified existing year.
    if not merged.get("year") and existing.get("year"):
        merged["year"] = existing["year"]

    merged_albums.append(merged)
    seen.add(key)

for album in existing_albums:
    key = album_key(album)
    if key not in seen:
        merged_albums.append(album)
        seen.add(key)

albums = merged_albums

with OUTPUT.open("w", encoding="utf-8") as f:
    f.write("const ALBUMS = ")
    json.dump(
        albums,
        f,
        indent=2,
        ensure_ascii=False
    )
    f.write(";\n")

print(f"Wrote: {OUTPUT}")
print(f"Albums: {len(albums)}")
