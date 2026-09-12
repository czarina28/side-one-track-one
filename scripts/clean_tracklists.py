import json
from pathlib import Path

PROJECT = Path(r"C:\Users\maria\side-one-track-one")

SOURCE = PROJECT / "data" / "album-tracklists.json"
OUTPUT = PROJECT / "data" / "albums-clean.json"

with SOURCE.open("r", encoding="utf-8") as f:
    albums = json.load(f)


OPENING_OVERRIDES = {
    "The Beatles|Sgt. Pepper's Lonely Hearts Club Band":
        "Sgt. Pepper's Lonely Hearts Club Band",

    "The Kinks|The Kinks Are the Village Green Preservation Society":
        "The Village Green Preservation Society",

    "Jimi Hendrix|Are You Experienced":
        "Foxy Lady",

    "Pixies|Doolittle":
        "Debaser",

    "Pearl Jam|Ten":
        "Once"
}


# Remove edition/version descriptions that make terrible
# multiple-choice answers.
TITLE_REPLACEMENTS = {
    "Sgt. Pepper’s Lonely Hearts Club Band (remix)":
        "Sgt. Pepper's Lonely Hearts Club Band",

    "The Village Green Preservation Society (stereo mix)":
        "The Village Green Preservation Society",

    "Once (2008 Brendan O’Brien mix)":
        "Once"
}


for album in albums:

    key = f"{album['artist']}|{album['album']}"

    # Clean track titles throughout the album.
    album["tracks"] = [
        TITLE_REPLACEMENTS.get(track, track)
        for track in album["tracks"]
    ]

    # Explicitly store the canonical answer separately.
    if key in OPENING_OVERRIDES:
        album["opening_track"] = OPENING_OVERRIDES[key]
    else:
        album["opening_track"] = album["tracks"][0]

    # Make sure the opening track is available as a choice.
    #
    # This matters for cases such as Doolittle where our
    # selected MusicBrainz edition was simply the wrong one.
    if album["opening_track"] not in album["tracks"]:
        album["tracks"].insert(
            0,
            album["opening_track"]
        )


with OUTPUT.open("w", encoding="utf-8") as f:
    json.dump(
        albums,
        f,
        indent=2,
        ensure_ascii=False
    )


print(f"Wrote: {OUTPUT}")
print(f"Albums: {len(albums)}")

print()
print("Canonical opening tracks:")
print()

for album in albums:
    print(
        f"{album['artist']} — "
        f"{album['album']} -> "
        f"{album['opening_track']}"
    )