"""Compare serialized NBS events, ignoring voice order within chords."""
import io
import struct
from collections import Counter
from pathlib import Path


def read(path):
    f = io.BytesIO(path.read_bytes())
    def unpack(fmt):
        return struct.unpack('<' + fmt, f.read(struct.calcsize('<' + fmt)))
    def string():
        return f.read(unpack('i')[0])
    zero, version, instruments, length, layers = unpack('hBBhh')
    assert (zero, version, instruments) == (0, 5, 16)
    for _ in range(4):
        string()
    tempo, _, _, _ = unpack('hBBB')
    unpack('iiiii')
    string()
    unpack('BBh')
    events = Counter()
    tick = -1
    while (jump := unpack('h')[0]):
        tick += jump
        while unpack('h')[0]:
            events[(tick, *unpack('BBBbh'))] += 1
    for _ in range(layers):
        string()
        unpack('BBB')
    assert unpack('B')[0] == 0 and f.read() == b''
    return length, tempo, events


root = Path(__file__).resolve().parents[1]
preview = read(root / 'plan_preview/departures_full_10tps_piano_v3.nbs')
final = read(root / 'plan_final/departures_full_10tps.nbs')
assert preview == final, 'Approved preview differs from final'
combined = Counter()
for index in range(11):
    length, tempo, events = read(root / f'plan_final/departures_module_{index+1:02d}.nbs')
    assert tempo == 1000 and length == (320 if index < 10 else 275)
    for (tick, *note), count in events.items():
        combined[(tick + 320 * index, *note)] += count
assert combined == final[2], 'Modules differ from whole song'
unisons = Counter()
for (tick, instrument, key, velocity, pan, pitch), count in combined.items():
    unisons[(tick, instrument, key)] += count
print('PASS: preview = final = 11 joined modules; 2307 events')
print('Extra unison triggers preserved:', sum(n-1 for n in unisons.values()))
