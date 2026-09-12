import json
from pathlib import Path

PROJECT = Path(r"C:\Users\maria\side-one-track-one")

SOURCE = PROJECT / "data" / "albums-clean.json"
OUTPUT = PROJECT / "data" / "albums.js"

with SOURCE.open("r", encoding="utf-8") as f:
    albums = json.load(f)

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