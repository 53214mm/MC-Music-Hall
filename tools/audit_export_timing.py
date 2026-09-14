"""Read-only static audit of this project's OpenNBS exports; NOT a game simulation."""
import csv
from collections import Counter
from pathlib import Path

from nbt_structure_to_json import structure_payload


ROOT = Path(__file__).resolve().parents[1]


def audit():
    with (ROOT / "departures_piano_final/departures_note_schedule.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        schedule = list(csv.DictReader(handle))
    total = 0
    for number in range(1, 12):
        filename = "module_01.nbt" if number == 1 else f"departures_module_{number:02d}.nbt"
        data = structure_payload(ROOT / "nbt_save" / filename)
        blocks = {tuple(block["p"]): block for block in data["blocks"]}
        actual = Counter()
        seen_notes = set()
        # Each music deck has repeaters at Y=2+3*n and rows at Z=3+3*n.
        for height in range(2, data["size"][1] - 2, 3):
            tick = 0
            for z in range(3, data["size"][2], 3):
                repeaters = [b for b in data["blocks"] if b["n"] == "repeater"
                             and b["p"][1:] == [height, z]]
                if not repeaters:
                    continue
                facings = {b["q"]["facing"] for b in repeaters}
                assert len(facings) == 1 and facings <= {"east", "west"}, facings
                # Java repeater facing points toward INPUT. Output is opposite.
                direction = -1 if "east" in facings else 1
                for repeater in sorted(repeaters, key=lambda b: direction * b["p"][0]):
                    tick += int(repeater["q"]["delay"])
                    x = repeater["p"][0]
                    for dx, dy in ((2, -1), (1, 0)):
                        for dz in (-1, 1):
                            pos = (x + direction * dx, height + dy, z + dz)
                            note = blocks.get(pos)
                            if note and note["n"] == "note_block":
                                assert pos not in seen_notes, (number, pos)
                                seen_notes.add(pos)
                                actual[(tick - 1, int(note["q"]["note"]))] += 1
        expected = Counter((int(r["local_tick"]), int(r["right_clicks"]))
                           for r in schedule if int(r["module"]) == number)
        assert actual == expected, (number, actual - expected, expected - actual)
        assert len(seen_notes) == data["counts"]["note_block"]
        # Audit the observed tower / ingress components. Connectivity and device
        # physics are derived separately in the report, not simulated here.
        torches = [b for b in data["blocks"] if b["n"] == "redstone_wall_torch"]
        expected_torches = 2 if number == 11 else 4
        assert len(torches) == expected_torches
        bus_delay = {}
        for height in range(2, data["size"][1] - 2, 3):
            bus_delay[height] = sum(int(b["q"]["delay"]) for b in data["blocks"]
                                   if b["n"] == "repeater" and b["p"][1:] == [height, 0])
        assert bus_delay == ({2: 2} if number == 11 else {2: 2, 5: 4}), bus_delay
        total += len(seen_notes)
        lead = 5 if number == 11 else 7
        print(f"module {number:02}: {len(seen_notes):3} notes MATCH; "
              f"first local_tick={min(t for t, _ in actual):2}; "
              f"torches={len(torches)}; bus={bus_delay}; derived input lead={lead}")
    assert total == 2307
    print(f"PASS: all {total} notes match CSV local_tick and pitch.")
    print("Static structure/export audit only; Minecraft playback NOT tested.")
    print("Original wool-input spacing: 320 ticks for 01->02 through 09->10; 322 for 10->11.")


if __name__ == "__main__":
    audit()
