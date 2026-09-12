import csv
import json
from pathlib import Path

csv.field_size_limit(10_000_000)

PROJECT = Path(r"C:\Users\maria\side-one-track-one")
MBDUMP = Path(r"C:\Users\maria\Downloads\mbdump\mbdump")

SEED_FILE = PROJECT / "data" / "seed-albums.txt"
OUTPUT_FILE = PROJECT / "data" / "release-candidates.json"


def read_tsv(path):
    with path.open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as f:
        yield from csv.reader(f, delimiter="\t")


def normalize(text):
    return (
        text.casefold()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("‐", "-")
        .replace("–", "-")
        .replace("—", "-")
        .strip()
    )


def load_seeds():
    seeds = []

    with SEED_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            artist, album = line.split("|", 1)

            seeds.append({
                "artist": artist.strip(),
                "album": album.strip()
            })

    return seeds


print("SIDE ONE TRACK ONE — Canonical Release Resolver")
print("------------------------------------------------")

seeds = load_seeds()

print(f"Loaded {len(seeds)} albums.")


# ---------------------------------------------------------
# ARTIST CREDITS
# ---------------------------------------------------------

wanted_artists = {
    normalize(seed["artist"])
    for seed in seeds
}

# Special MusicBrainz credits.
#
# These albums are canonically credited differently from
# our human-friendly seed artist.
credit_aliases = {
    normalize("The Velvet Underground"): {
        normalize("The Velvet Underground"),
        normalize("The Velvet Underground & Nico")
    },

    normalize("Jimi Hendrix"): {
        normalize("Jimi Hendrix"),
        normalize("The Jimi Hendrix Experience")
    },

    normalize("Prince"): {
        normalize("Prince"),
        normalize("Prince and The Revolution")
    }
}


artist_credit_ids = {}
credit_names = {}

print("Scanning artist_credit...")

for row in read_tsv(MBDUMP / "artist_credit"):
    if len(row) < 2:
        continue

    credit_id = row[0]
    credit_name = row[1].strip()
    normalized_credit = normalize(credit_name)

    for seed_artist in wanted_artists:

        acceptable = credit_aliases.get(
            seed_artist,
            {seed_artist}
        )

        if normalized_credit in acceptable:
            artist_credit_ids.setdefault(
                seed_artist,
                set()
            ).add(credit_id)

            credit_names[credit_id] = credit_name


# ---------------------------------------------------------
# RELEASE GROUPS
#
# We want album release groups only.
#
# In the dump:
# primary type 1 = Album
# ---------------------------------------------------------

release_groups = {i: [] for i in range(len(seeds))}

print("Scanning release_group...")

for row in read_tsv(MBDUMP / "release_group"):

    if len(row) < 5:
        continue

    rg_id = row[0]
    rg_mbid = row[1]
    title = row[2].strip()
    artist_credit_id = row[3]
    primary_type = row[4]

    # Album only.
    if primary_type != "1":
        continue

    for i, seed in enumerate(seeds):

        if normalize(title) != normalize(seed["album"]):
            continue

        valid_credits = artist_credit_ids.get(
            normalize(seed["artist"]),
            set()
        )

        if artist_credit_id not in valid_credits:
            continue

        release_groups[i].append({
            "id": rg_id,
            "mbid": rg_mbid,
            "title": title,
            "artist_credit_id": artist_credit_id,
            "artist_credit": credit_names.get(
                artist_credit_id,
                seed["artist"]
            )
        })


# ---------------------------------------------------------
# REPORT RELEASE GROUP STATUS
# ---------------------------------------------------------

print()
print("RELEASE GROUP RESULTS")
print("---------------------")

resolved_groups = {}
problems = []

for i, seed in enumerate(seeds):

    groups = release_groups[i]

    if len(groups) == 1:
        resolved_groups[groups[0]["id"]] = i

        print(
            f"OK          "
            f"{seed['artist']} — {seed['album']}"
        )

    elif len(groups) == 0:
        problems.append(i)

        print(
            f"NOT FOUND   "
            f"{seed['artist']} — {seed['album']}"
        )

    else:
        problems.append(i)

        print(
            f"AMBIGUOUS   "
            f"{seed['artist']} — {seed['album']} "
            f"({len(groups)})"
        )

        for group in groups:
            print(
                f"            {group['mbid']}"
            )


# ---------------------------------------------------------
# RELEASES
#
# release columns begin:
#
# 0 id
# 1 gid / MBID
# 2 name
# 3 artist_credit
# 4 release_group
# 5 status
# 6 packaging
# 7 language
# 8 script
# 9 barcode
# ...
# ---------------------------------------------------------

release_candidates = {
    i: []
    for i in range(len(seeds))
}

print()
print(
    f"Scanning release table for "
    f"{len(resolved_groups)} resolved albums..."
)

for row in read_tsv(MBDUMP / "release"):

    if len(row) < 5:
        continue

    release_group_id = row[4]

    if release_group_id not in resolved_groups:
        continue

    seed_index = resolved_groups[release_group_id]

    release_candidates[seed_index].append({
        "release_id": row[0],
        "release_mbid": row[1],
        "title": row[2],
        "artist_credit_id": row[3],
        "status": row[5] if len(row) > 5 else "",
        "packaging": row[6] if len(row) > 6 else "",
        "language": row[7] if len(row) > 7 else "",
        "script": row[8] if len(row) > 8 else "",
        "barcode": row[9] if len(row) > 9 else ""
    })


# ---------------------------------------------------------
# MEDIUM
#
# This is useful because we ultimately want vinyl releases,
# ideally one medium, with an ordinary album track listing.
# ---------------------------------------------------------

wanted_release_ids = {}

for i, candidates in release_candidates.items():
    for candidate in candidates:
        wanted_release_ids[candidate["release_id"]] = candidate


print("Scanning medium...")

for row in read_tsv(MBDUMP / "medium"):

    if len(row) < 4:
        continue

    release_id = row[1]

    if release_id not in wanted_release_ids:
        continue

    candidate = wanted_release_ids[release_id]

    candidate.setdefault("media", [])

    candidate["media"].append({
        "medium_id": row[0],
        "position": row[2],
        "format_id": row[3]
    })


# ---------------------------------------------------------
# BUILD OUTPUT
# ---------------------------------------------------------

output = []

for i, seed in enumerate(seeds):

    groups = release_groups[i]

    item = {
        "artist": seed["artist"],
        "album": seed["album"],
        "release_groups": groups,
        "releases": release_candidates[i]
    }

    output.append(item)


with OUTPUT_FILE.open(
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
print("------------------------------------------------")
print(f"Wrote: {OUTPUT_FILE}")
print()
print(
    f"Resolved release groups: "
    f"{len(resolved_groups)} / {len(seeds)}"
)

print(
    f"Still requiring manual resolution: "
    f"{len(problems)}"
)

if problems:
    print()
    print("Problem albums:")

    for i in problems:
        seed = seeds[i]

        print(
            f"  {seed['artist']} — "
            f"{seed['album']}"
        )