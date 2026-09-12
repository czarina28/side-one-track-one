import csv
from pathlib import Path

csv.field_size_limit(10_000_000)

MBDUMP = Path(r"C:\Users\maria\Downloads\mbdump\mbdump")

LED_ZEPPELIN_CREDITS = set()

# Find every artist_credit ID whose displayed credit
# is exactly Led Zeppelin.
with (MBDUMP / "artist_credit").open(
    "r",
    encoding="utf-8",
    errors="replace",
    newline=""
) as f:

    for row in csv.reader(f, delimiter="\t"):
        if len(row) >= 2 and row[1].strip().casefold() == "led zeppelin":
            LED_ZEPPELIN_CREDITS.add(row[0])


print("Led Zeppelin artist credits:", LED_ZEPPELIN_CREDITS)
print()
print("Possible fourth-album release groups:")
print("--------------------------------------")

with (MBDUMP / "release_group").open(
    "r",
    encoding="utf-8",
    errors="replace",
    newline=""
) as f:

    for row in csv.reader(f, delimiter="\t"):

        if len(row) < 5:
            continue

        artist_credit = row[3]
        title = row[2].strip()
        primary_type = row[4]

        if artist_credit not in LED_ZEPPELIN_CREDITS:
            continue

        # Albums only
        if primary_type != "1":
            continue

        t = title.casefold()

        # Only plausible names for the untitled fourth album.
        if (
            t == "iv"
            or t == "led zeppelin iv"
            or t == "untitled"
            or t == "four symbols"
            or t == "zoso"
            or "four symbols" in t
        ):
            print(f"{row[1]} | {title}")