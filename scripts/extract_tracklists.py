import csv
import json
from pathlib import Path
from collections import defaultdict

csv.field_size_limit(10_000_000)

PROJECT = Path(r"C:\Users\maria\side-one-track-one")
MBDUMP = Path(r"C:\Users\maria\Downloads\mbdump\mbdump")

SEEDS = PROJECT / "data" / "seed-albums.txt"
CANDIDATES = PROJECT / "data" / "release-candidates.json"
OVERRIDES = PROJECT / "data" / "release-group-overrides.json"
OUTPUT = PROJECT / "data" / "album-tracklists.json"


def read_tsv(name):
    with (MBDUMP / name).open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as f:
        yield from csv.reader(f, delimiter="\t")


def load_seeds():
    result = []

    with SEEDS.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            artist, album = line.split("|", 1)

            result.append({
                "artist": artist,
                "album": album,
                "key": f"{artist}|{album}"
            })

    return result


seeds = load_seeds()

with CANDIDATES.open("r", encoding="utf-8") as f:
    candidate_data = json.load(f)

with OVERRIDES.open("r", encoding="utf-8") as f:
    overrides = json.load(f)


# ---------------------------------------------------------
# Resolve release-group MBID for every album
# ---------------------------------------------------------

groups_by_key = {}

for item in candidate_data:

    key = f"{item['artist']}|{item['album']}"

    groups = item.get("release_groups", [])

    if len(groups) == 1:
        groups_by_key[key] = groups[0]["mbid"]


# Manual decisions beat automatic decisions.
for key, mbid in overrides.items():
    groups_by_key[key] = mbid


print("SIDE ONE TRACK ONE — Tracklist Extractor")
print("----------------------------------------")
print(f"Seeds: {len(seeds)}")
print(f"Resolved groups: {len(groups_by_key)}")


# ---------------------------------------------------------
# Hardcoded exception
# ---------------------------------------------------------

hardcoded = {
    "Led Zeppelin|Led Zeppelin IV": {
        "artist": "Led Zeppelin",
        "album": "Led Zeppelin IV",
        "year": 1971,
        "tracks": [
            "Black Dog",
            "Rock and Roll",
            "The Battle of Evermore",
            "Stairway to Heaven",
            "Misty Mountain Hop",
            "Four Sticks",
            "Going to California",
            "When the Levee Breaks"
        ]
    }
}


# ---------------------------------------------------------
# Map release-group MBIDs -> internal IDs
# ---------------------------------------------------------

wanted_group_mbids = {
    mbid
    for mbid in groups_by_key.values()
    if mbid != "HARDCODE"
}

group_internal_to_key = {}

print("Scanning release_group...")

mbid_to_key = {
    mbid: key
    for key, mbid in groups_by_key.items()
    if mbid != "HARDCODE"
}

for row in read_tsv("release_group"):

    if len(row) < 2:
        continue

    mbid = row[1]

    if mbid in wanted_group_mbids:
        group_internal_to_key[row[0]] = mbid_to_key[mbid]


print(
    f"Found {len(group_internal_to_key)} "
    "release groups in dump."
)


# ---------------------------------------------------------
# Collect releases for those groups
# ---------------------------------------------------------

releases_by_key = defaultdict(list)
release_id_to_key = {}
release_by_id = {}

print("Scanning release...")

for row in read_tsv("release"):

    if len(row) < 5:
        continue

    group_id = row[4]

    if group_id not in group_internal_to_key:
        continue

    key = group_internal_to_key[group_id]

    release = {
        "id": row[0],
        "mbid": row[1],
        "title": row[2],
        "status": row[5] if len(row) > 5 else "",
        "packaging": row[6] if len(row) > 6 else "",
    }

    releases_by_key[key].append(release)
    release_id_to_key[row[0]] = key
    release_by_id[row[0]] = release


print(
    f"Found {len(release_id_to_key)} "
    "candidate releases."
)


# ---------------------------------------------------------
# Release dates
#
# release_country / release_unknown_country:
# 0 release, 1 country (country table only), then year/month/day
# ---------------------------------------------------------

print("Scanning release dates...")

for table_name, year_column in (
    ("release_country", 2),
    ("release_unknown_country", 1),
):
    for row in read_tsv(table_name):
        if len(row) <= year_column or row[0] not in release_by_id:
            continue

        try:
            year = int(row[year_column])
        except (TypeError, ValueError):
            continue

        release = release_by_id[row[0]]
        current = release.get("year")
        if current is None or year < current:
            release["year"] = year

years_by_key = {
    key: min(
        release["year"]
        for release in releases
        if release.get("year")
    )
    for key, releases in releases_by_key.items()
    if any(release.get("year") for release in releases)
}


# ---------------------------------------------------------
# Collect media
#
# medium:
# 0 id
# 1 release
# 2 position
# 3 format
# ---------------------------------------------------------

media_by_key = defaultdict(list)

print("Scanning medium...")

for row in read_tsv("medium"):

    if len(row) < 4:
        continue

    release_id = row[1]

    if release_id not in release_id_to_key:
        continue

    key = release_id_to_key[release_id]

    media_by_key[key].append({
        "medium_id": row[0],
        "release_id": release_id,
        "position": row[2],
        "format_id": row[3]
    })


# ---------------------------------------------------------
# Pick one candidate medium per album.
#
# For now:
#   - medium position 1
#   - prefer format 12 (vinyl in this dump)
#   - then format 31
#   - then anything
#
# We will validate the resulting tracklists rather than
# pretending this heuristic is historically perfect.
# ---------------------------------------------------------

selected_media = {}

for seed in seeds:

    key = seed["key"]

    if key in hardcoded:
        continue

    media = [
        m for m in media_by_key.get(key, [])
        if m["position"] == "1"
    ]

    if not media:
        print(f"NO MEDIA: {key}")
        continue

    def rank(m):
        fmt = m["format_id"]
        release = release_by_id[m["release_id"]]

        if fmt == "12":
            format_rank = 0
        elif fmt == "31":
            format_rank = 1
        elif fmt == "1":
            format_rank = 2
        else:
            format_rank = 3

        return (
            release.get("year", 9999),
            format_rank,
            m["release_id"]
        )

    media.sort(key=rank)

    selected_media[key] = media[0]


print()
print(
    f"Selected media for "
    f"{len(selected_media)} albums."
)


# ---------------------------------------------------------
# THE MONSTER
#
# Scan track exactly once.
#
# track:
# 0 id
# 1 gid
# 2 recording
# 3 medium
# 4 position
# 5 number
# 6 name
# ---------------------------------------------------------

medium_to_key = {
    m["medium_id"]: key
    for key, m in selected_media.items()
}

tracks_by_key = defaultdict(list)

print()
print("Scanning track...")
print("This is the big one.")

count = 0
found = 0

for row in read_tsv("track"):

    count += 1

    if count % 5_000_000 == 0:
        print(
            f"  scanned {count:,} tracks..."
        )

    if len(row) < 7:
        continue

    medium_id = row[3]

    if medium_id not in medium_to_key:
        continue

    key = medium_to_key[medium_id]

    try:
        position = int(row[4])
    except ValueError:
        position = 9999

    tracks_by_key[key].append({
        "position": position,
        "number": row[5],
        "title": row[6]
    })

    found += 1


print()
print(
    f"Found {found:,} tracks "
    "for selected albums."
)


# ---------------------------------------------------------
# Build final compact dataset
# ---------------------------------------------------------

output = []

for seed in seeds:

    key = seed["key"]

    if key in hardcoded:
        output.append(hardcoded[key])
        continue

    tracks = tracks_by_key.get(key, [])

    tracks.sort(
        key=lambda t: t["position"]
    )

    if not tracks:
        print(f"NO TRACKS: {key}")
        continue

    output.append({
        "artist": seed["artist"],
        "album": seed["album"],
        "year": years_by_key.get(key),
        "release_group_mbid": groups_by_key[key],
        "release_mbid": next(
            (
                r["mbid"]
                for r in releases_by_key[key]
                if r["id"] ==
                selected_media[key]["release_id"]
            ),
            None
        ),
        "format_id": selected_media[key]["format_id"],
        "tracks": [
            t["title"]
            for t in tracks
        ]
    })


with OUTPUT.open(
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        indent=2,
        ensure_ascii=False
    )


print()
print("----------------------------------------")
print(f"Wrote: {OUTPUT}")
print(f"Albums written: {len(output)} / {len(seeds)}")

print()
print("Opening tracks:")
print()

for album in output:
    if album["tracks"]:
        print(
            f"{album['artist']} — "
            f"{album['album']} -> "
            f"{album['tracks'][0]}"
        )
