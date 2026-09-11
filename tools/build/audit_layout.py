"""Read-only NBT inspection; outputs the proposed placement audit, not a redstone simulation."""
import json
import math
from pathlib import Path

try:
    from nbt_structure_to_json import structure_payload
except ModuleNotFoundError:  # 允许直接运行
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'viewer'))
    from nbt_structure_to_json import structure_payload

PROJECT = Path(__file__).resolve().parents[2]
CENTER = (21, 32, 3.5)


def main():
    rows = []
    occupied = set()
    collisions = 0
    for number in range(1, 12):
        filename = 'module_01.nbt' if number == 1 else f'departures_module_{number:02}.nbt'
        data = structure_payload(PROJECT / 'nbt_export' / filename)
        floor = (number - 1) // 2
        north = ((number - 1) % 2 == 0) if floor % 2 == 0 else ((number - 1) % 2 == 1)
        distances = []
        for block in data['blocks']:
            x, y, z = block['p']
            position = (42-x if north else x, y+floor*12, -1-z if north else 8+z)
            collisions += position in occupied
            occupied.add(position)
            if block['n'] == 'note_block':
                distances.append(math.dist(CENTER, position))
        rows.append({'module': number, 'size': data['size'], 'declaredSize': data['declaredSize'],
                     'floor': floor+1, 'baseY': floor*12, 'bank': 'north' if north else 'south',
                     'rotationY': 180 if north else 0,
                     'coordinateTransform': '[42-x, y+baseY, -1-z]' if north else '[x, y+baseY, 8+z]',
                     'notes': len(distances), 'maxNoteDistance': round(max(distances), 3),
                     'startScoreTick': (number-1)*320, 'materials': data['counts']})
    report = {'status': 'spatial proposal; redstone timing not simulated', 'listeningPoint': CENTER,
              'collidingNonAirBlocks': collisions, 'noteCount': sum(row['notes'] for row in rows),
              'maxNoteDistance': max(row['maxNoteDistance'] for row in rows), 'modules': rows}
    output = PROJECT / 'design' / 'layout_audit.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'modules'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
