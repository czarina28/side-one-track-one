import csv
from pathlib import Path
from collections import defaultdict

csv.field_size_limit(10_000_000)

MBDUMP = Path(r"C:\Users\maria\Downloads\mbdump\mbdump")

# Candidate release-group MBIDs from our resolver.
PROBLEMS = {
    "The Who — Who's Next": [
        "2c56c32d-f66c-4e26-bb6b-caed0e0cffa4",
        "9584e28b-66a7-3846-8d52-b3008a283539",
    ],

    "The Doors — The Doors": [
        "074f7088-9287-3616-8e2c-4d0e78d23003",
        "8ebffd15-06c3-3b88-a761-ec18c5513287",
        "00a9c3d9-13c7-355b-b216-108c81ad3f78",
        "38eaaeec-92af-4281-afaf-88537d227b27",
    ],

    "Jimi Hendrix — Are You Experienced": [
        "da40e720-2097-3730-8a7f-0c2ddbff4a96",
        "791fdbb8-b19c-4d33-9ba4-d2d2f35abec6",
    ],

    "Led Zeppelin — Led Zeppelin": [
        "f0f76bfa-96e2-4041-9e30-5bdb2c619711",
        "92d5e425-6dff-34d7-8edf-0c82156b46b0",
        "fadd0405-9ba3-496b-890c-ad250336f3c2",
        "7cfaae49-db15-4c27-a3e2-86cfcb7be3ee",
        "362f3fa7-d298-3998-ae1c-4ac0d02b7718",
        "0f18ec88-aa87-38a9-8a65-f03d81763560",
    ],

    "Pink Floyd — Wish You Were Here": [
        "aec8c2eb-0639-436f-99db-9974781f241c",
        "1a272023-10d3-38ee-bab3-317b55fcc21d",
    ],

    "Marvin Gaye — What's Going On": [
        "871b20d7-95bf-4490-8ac1-e3c1143e9d37",
        "c1fa4d2c-ec62-37d5-b01d-6df7f8fd2c90",
    ],
}


def read_tsv(name):
    path = MBDUMP / name

    with path.open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as f:
        yield from csv.reader(f, delimiter="\t")


wanted_mbids = {
    mbid
    for candidates in PROBLEMS.values()
    for mbid in candidates
}

# ---------------------------------------------------------
# Find internal release-group IDs
# ---------------------------------------------------------

groups = {}

print("Scanning release_group...")

for row in read_tsv("release_group"):

    if len(row) < 5:
        continue

    if row[1] in wanted_mbids:
        groups[row[0]] = {
            "id": row[0],
            "mbid": row[1],
            "title": row[2],
            "artist_credit": row[3],
            "type": row[4],
        }


# ---------------------------------------------------------
# Find all releases belonging to those groups
# ---------------------------------------------------------

releases = defaultdict(list)
release_lookup = {}

print("Scanning release...")

for row in read_tsv("release"):

    if len(row) < 5:
        continue

    group_id = row[4]

    if group_id not in groups:
        continue

    item = {
        "id": row[0],
        "mbid": row[1],
        "title": row[2],
        "group_id": group_id,
        "status": row[5] if len(row) > 5 else "",
        "packaging": row[6] if len(row) > 6 else "",
        "language": row[7] if len(row) > 7 else "",
        "script": row[8] if len(row) > 8 else "",
        "barcode": row[9] if len(row) > 9 else "",
    }

    releases[group_id].append(item)
    release_lookup[row[0]] = item


# ---------------------------------------------------------
# Find media belonging to those releases
# ---------------------------------------------------------

print("Scanning medium...")

for row in read_tsv("medium"):

    if len(row) < 4:
        continue

    release_id = row[1]

    if release_id not in release_lookup:
        continue

    release_lookup[release_id].setdefault(
        "media", []
    ).append({
        "medium_id": row[0],
        "position": row[2],
        "format_id": row[3],
    })


# ---------------------------------------------------------
# Report
# ---------------------------------------------------------

group_by_mbid = {
    data["mbid"]: data
    for data in groups.values()
}


print()
print("=" * 78)
print("PROBLEM RELEASE GROUP INSPECTION")
print("=" * 78)

for album, candidates in PROBLEMS.items():

    print()
    print("#" * 78)
    print(album)
    print("#" * 78)

    for mbid in candidates:

        group = group_by_mbid.get(mbid)

        if not group:
            print()
            print(f"MBID: {mbid}")
            print("  NOT FOUND")
            continue

        group_releases = releases[group["id"]]

        print()
        print(f"MBID: {mbid}")
        print(f"TITLE: {group['title']}")
        print(f"TYPE: {group['type']}")
        print(f"RELEASES: {len(group_releases)}")

        # Show a useful sample.
        #
        # Releases with fewer media first, then MBID,
        # so ordinary releases tend to be visible before
        # giant deluxe packages.

        def media_count(r):
            return len(r.get("media", []))

        ordered = sorted(
            group_releases,
            key=lambda r: (
                media_count(r),
                r["mbid"]
            )
        )

        for release in ordered[:15]:

            media = release.get("media", [])

            formats = ",".join(
                m["format_id"]
                for m in media
            ) or "-"

            print(
                "  "
                f"{release['mbid']} | "
                f"media={len(media)} | "
                f"formats={formats} | "
                f"title={release['title']}"
            )

        if len(ordered) > 15:
            print(
                f"  ... +{len(ordered) - 15} more releases"
            )


print()
print("=" * 78)
print("DONE")
print("=" * 78)

print()
print("NOTE: Led Zeppelin IV is intentionally absent here.")
print("We need to locate its MusicBrainz canonical title separately.")