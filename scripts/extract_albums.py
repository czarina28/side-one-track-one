import csv
from pathlib import Path

csv.field_size_limit(10_000_000)

PROJECT = Path(r"C:\Users\maria\side-one-track-one")
MBDUMP = Path(r"C:\Users\maria\Downloads\mbdump\mbdump")
SEED_FILE = PROJECT / "data" / "seed-albums.txt"


def read_tsv(path):
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        yield from csv.reader(f, delimiter="\t")


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


print("SIDE ONE TRACK ONE — MusicBrainz diagnostic")
print("--------------------------------------------")

seeds = load_seeds()
print(f"Loaded {len(seeds)} seed albums.")


# ---------------------------------------------------------
# 1. Load artist credits we care about
# ---------------------------------------------------------

wanted_artists = {s["artist"].casefold() for s in seeds}

artist_credit_ids = {}
credit_names = {}

print("\nScanning artist_credit...")

for row in read_tsv(MBDUMP / "artist_credit"):
    if len(row) < 2:
        continue

    credit_id = row[0]
    credit_name = row[1].strip()

    if credit_name.casefold() in wanted_artists:
        artist_credit_ids.setdefault(
            credit_name.casefold(), set()
        ).add(credit_id)

        credit_names[credit_id] = credit_name


# ---------------------------------------------------------
# 2. Scan release groups.
#
# Keep:
#   A) exact title + artist matches
#   B) same artist with approximately matching titles
#
# This lets us diagnose punctuation/title differences.
# ---------------------------------------------------------

exact = {i: [] for i in range(len(seeds))}
artist_candidates = {i: [] for i in range(len(seeds))}


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


print("Scanning release_group...")

for row in read_tsv(MBDUMP / "release_group"):
    if len(row) < 5:
        continue

    rg_id = row[0]
    gid = row[1]
    title = row[2].strip()
    artist_credit_id = row[3]

    for i, seed in enumerate(seeds):

        valid_credits = artist_credit_ids.get(
            seed["artist"].casefold(), set()
        )

        if artist_credit_id not in valid_credits:
            continue

        item = {
            "id": rg_id,
            "mbid": gid,
            "title": title,
            "artist": credit_names.get(
                artist_credit_id, "?"
            ),
            "type": row[4] if len(row) > 4 else ""
        }

        artist_candidates[i].append(item)

        if normalize(title) == normalize(seed["album"]):
            exact[i].append(item)


# ---------------------------------------------------------
# 3. Print exact matches first
# ---------------------------------------------------------

print("\n============================================")
print("EXACT MATCHES")
print("============================================")

good = []

for i, seed in enumerate(seeds):
    matches = exact[i]

    if len(matches) == 1:
        good.append((seed, matches[0]))

        print(
            f"OK  {seed['artist']} — {seed['album']}"
        )
        print(f"    {matches[0]['mbid']}")


# ---------------------------------------------------------
# 4. Print only the problem albums
# ---------------------------------------------------------

print("\n============================================")
print("PROBLEM ALBUMS")
print("============================================")

for i, seed in enumerate(seeds):

    matches = exact[i]

    if len(matches) == 1:
        continue

    print()
    print("--------------------------------------------")
    print(f"{seed['artist']} — {seed['album']}")

    if not matches:
        print("STATUS: NOT FOUND")
    else:
        print(f"STATUS: AMBIGUOUS ({len(matches)})")

        print("\nExact-title candidates:")

        for m in matches:
            print(
                f"  {m['mbid']} | "
                f"type={m['type']} | "
                f"{m['artist']} — {m['title']}"
            )

    # Show potentially useful albums by this artist.
    candidates = artist_candidates[i]

    seed_words = {
        word.strip("()[]{}?!.,:'\"").casefold()
        for word in seed["album"].split()
        if len(word.strip("()[]{}?!.,:'\"")) >= 4
    }

    related = []

    for candidate in candidates:

        title_words = {
            word.strip("()[]{}?!.,:'\"").casefold()
            for word in candidate["title"].split()
        }

        overlap = seed_words & title_words

        if overlap:
            related.append(
                (len(overlap), candidate)
            )

    related.sort(
        key=lambda x: (-x[0], x[1]["title"])
    )

    print("\nPossible related release groups:")

    shown = set()
    count = 0

    for score, candidate in related:

        if candidate["mbid"] in shown:
            continue

        shown.add(candidate["mbid"])

        print(
            f"  {candidate['mbid']} | "
            f"type={candidate['type']} | "
            f"{candidate['title']}"
        )

        count += 1

        if count >= 10:
            break

    if count == 0:
        print("  (none found)")


print()
print("============================================")
print(f"Clean exact matches: {len(good)} / {len(seeds)}")
print("============================================")