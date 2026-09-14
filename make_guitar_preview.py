"""Create an A/B listening variant without changing the existing build plan."""
import csv
import argparse
from collections import Counter
from pathlib import Path

from build_departures_plan import write_nbs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--piano', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    source = root / 'departures_redstone' / 'departures_note_schedule.csv'
    variant = 'piano_v3' if args.piano else 'guitar_v2'
    destination = root / ('departures_piano_preview' if args.piano else 'departures_guitar_preview')
    destination.mkdir(exist_ok=True)
    notes = []
    changed = 0
    with source.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            instrument = {'Double Bass': 1, 'Harp/Piano': 0, 'Chime': 8}[row['instrument']]
            clicks = int(row['right_clicks'])
            pitch = {1: 30, 0: 54, 8: 78}[instrument] + clicks
            original_pitch = pitch
            if instrument == 1 and 42 <= pitch <= 53:
                instrument = 0 if args.piano else 5
                if args.piano:
                    pitch += 12
                clicks = pitch - (54 if args.piano else 42)
                changed += 1
            assert {1: 30, 0: 54, 8: 78, 5: 42}[instrument] + clicks == pitch
            assert pitch - original_pitch in (0, 12) if args.piano else pitch == original_pitch
            notes.append(dict(local_tick=int(row['global_tick']), midi_note=pitch,
                              instrument=instrument, nbs_key=33 + clicks,
                              velocity=int(row['velocity'])))
    write_nbs(destination / f'departures_full_10tps_{variant}.nbs',
              f'Departures - {variant}', notes, 3475, source.name)
    # A short excerpt starts at source time 12s, retaining the same timing and dynamics.
    excerpt = [dict(n, local_tick=n['local_tick'] - 120)
               for n in notes if 120 <= n['local_tick'] < 200]
    write_nbs(destination / f'departures_12s_to_20s_{variant}.nbs',
              f'Departures - 12s to 20s - {variant}', excerpt, 80, source.name)
    target = [n for n in notes if n['local_tick'] == 151]
    assert len(target) == 1 and target[0]['instrument'] == (0 if args.piano else 5) and target[0]['nbs_key'] == 43
    print(dict(notes=len(notes), changed_to_guitar=changed,
               instruments=dict(Counter(n['instrument'] for n in notes)), excerpt_notes=len(excerpt)))


if __name__ == '__main__':
    main()
