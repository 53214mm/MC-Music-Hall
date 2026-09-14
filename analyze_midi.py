from __future__ import annotations

import collections
import json
import struct
import sys
from pathlib import Path


GM_NAMES = {
    0: "Acoustic Grand Piano",
    4: "Electric Piano 1",
    24: "Acoustic Guitar (nylon)",
    25: "Acoustic Guitar (steel)",
    32: "Acoustic Bass",
    40: "Violin",
    41: "Viola",
    42: "Cello",
    48: "String Ensemble 1",
    49: "String Ensemble 2",
    52: "Choir Aahs",
    53: "Voice Oohs",
    73: "Flute",
}


def read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    while True:
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, pos


def midi_note_name(note: int) -> str:
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[note % 12]}{note // 12 - 1}"


def parse_track(data: bytes, track_index: int) -> dict:
    pos = 0
    tick = 0
    running_status = None
    events = []
    name = ""
    while pos < len(data):
        delta, pos = read_vlq(data, pos)
        tick += delta
        status = data[pos]
        if status < 0x80:
            if running_status is None:
                raise ValueError("Running status without prior channel status")
            status = running_status
        else:
            pos += 1

        if status == 0xFF:
            meta_type = data[pos]
            pos += 1
            length, pos = read_vlq(data, pos)
            payload = data[pos : pos + length]
            pos += length
            running_status = None
            if meta_type == 0x03:
                name = payload.decode("utf-8", errors="replace")
            elif meta_type == 0x51 and len(payload) == 3:
                events.append((tick, "tempo", int.from_bytes(payload, "big")))
            elif meta_type == 0x58 and len(payload) >= 2:
                events.append((tick, "time_signature", (payload[0], 2 ** payload[1])))
            elif meta_type == 0x59 and len(payload) >= 2:
                sf = payload[0] if payload[0] < 128 else payload[0] - 256
                events.append((tick, "key_signature", (sf, payload[1])))
            continue

        if status in (0xF0, 0xF7):
            length, pos = read_vlq(data, pos)
            pos += length
            running_status = None
            continue

        running_status = status
        event_type = status & 0xF0
        channel = status & 0x0F
        size = 1 if event_type in (0xC0, 0xD0) else 2
        payload = data[pos : pos + size]
        pos += size
        if event_type == 0x90:
            note, velocity = payload
            kind = "note_on" if velocity else "note_off"
            events.append((tick, kind, (channel, note, velocity)))
        elif event_type == 0x80:
            note, velocity = payload
            events.append((tick, "note_off", (channel, note, velocity)))
        elif event_type == 0xC0:
            events.append((tick, "program", (channel, payload[0])))
    return {"index": track_index, "name": name, "end_tick": tick, "events": events}


def tick_to_seconds(tick: int, tempo_map: list[tuple[int, int]], division: int) -> float:
    seconds = 0.0
    previous_tick = 0
    tempo = 500_000
    for change_tick, new_tempo in tempo_map:
        if change_tick >= tick:
            break
        seconds += (change_tick - previous_tick) * tempo / 1_000_000 / division
        previous_tick = change_tick
        tempo = new_tempo
    return seconds + (tick - previous_tick) * tempo / 1_000_000 / division


def main(path: Path) -> None:
    blob = path.read_bytes()
    if blob[:4] != b"MThd":
        raise ValueError("Not a Standard MIDI file")
    header_length = struct.unpack(">I", blob[4:8])[0]
    fmt, track_count, division = struct.unpack(">HHH", blob[8:14])
    if division & 0x8000:
        raise ValueError("SMPTE time division is not supported")
    pos = 8 + header_length
    tracks = []
    for index in range(track_count):
        if blob[pos : pos + 4] != b"MTrk":
            raise ValueError(f"Missing MTrk header at track {index}")
        size = struct.unpack(">I", blob[pos + 4 : pos + 8])[0]
        tracks.append(parse_track(blob[pos + 8 : pos + 8 + size], index))
        pos += 8 + size

    all_events = [event for track in tracks for event in track["events"]]
    tempo_map = sorted({(tick, value) for tick, kind, value in all_events if kind == "tempo"})
    if not tempo_map or tempo_map[0][0] != 0:
        tempo_map.insert(0, (0, 500_000))
    note_ons = [(tick, value, track["index"]) for track in tracks for tick, kind, value in track["events"] if kind == "note_on"]
    programs = collections.defaultdict(list)
    for tick, kind, value in sorted(all_events):
        if kind == "program":
            channel, program = value
            programs[channel].append((tick, program))
    note_counts = collections.Counter(channel for _, (channel, _, _), _ in note_ons)
    pitches = [note for _, (_, note, _), _ in note_ons]
    velocities = [velocity for _, (_, _, velocity), _ in note_ons]
    active_ticks = collections.Counter(tick for tick, _, _ in note_ons)
    quantized_notes = {
        (round(tick_to_seconds(tick, tempo_map, division) * 10), value[1])
        for tick, value, _ in note_ons
    }
    quantized_chords = collections.Counter(tick for tick, _ in quantized_notes)
    max_tick = max(track["end_tick"] for track in tracks)
    time_signatures = [(tick, value) for tick, kind, value in sorted(all_events) if kind == "time_signature"]
    key_signatures = [(tick, value) for tick, kind, value in sorted(all_events) if kind == "key_signature"]
    register_counts = {
        "below_vanilla_B0-F1": sum(note < 30 for note in pitches),
        "bass_F#1-F3": sum(30 <= note <= 53 for note in pitches),
        "harp_F#3-F5": sum(54 <= note <= 78 for note in pitches),
        "high_G5-F#7": sum(79 <= note <= 102 for note in pitches),
        "above_vanilla_G7_plus": sum(note > 102 for note in pitches),
    }
    octave_counts = collections.Counter(note // 12 - 1 for note in pitches)
    ticks_per_bar = division * 4
    module_ticks = ticks_per_bar * 16
    module_counts = collections.Counter(tick // module_ticks + 1 for tick, _, _ in note_ons)

    track_stats = []
    for track in tracks:
        notes = [(tick, value) for tick, kind, value in track["events"] if kind == "note_on"]
        track_pitches = [value[1] for _, value in notes]
        track_stats.append(
            {
                "index": track["index"],
                "name": track["name"],
                "notes": len(notes),
                "pitch_min": midi_note_name(min(track_pitches)) if track_pitches else None,
                "pitch_max": midi_note_name(max(track_pitches)) if track_pitches else None,
                "end_tick": track["end_tick"],
            }
        )

    result = {
        "path": str(path),
        "bytes": len(blob),
        "format": fmt,
        "tracks": track_count,
        "ticks_per_quarter": division,
        "duration_seconds": round(tick_to_seconds(max_tick, tempo_map, division), 3),
        "end_tick": max_tick,
        "tempo_changes": [
            {"tick": tick, "bpm": round(60_000_000 / tempo, 6)} for tick, tempo in tempo_map
        ],
        "time_signatures": time_signatures,
        "key_signatures": key_signatures,
        "total_note_ons": len(note_ons),
        "active_note_ticks": len(active_ticks),
        "maximum_chord_size": max(active_ticks.values(), default=0),
        "last_note_on_seconds": round(
            max(tick_to_seconds(tick, tempo_map, division) for tick, _, _ in note_ons), 3
        ),
        "quantized_10tps_notes": len(quantized_notes),
        "quantized_10tps_active_ticks": len(quantized_chords),
        "quantized_10tps_maximum_chord_size": max(quantized_chords.values(), default=0),
        "pitch_min": midi_note_name(min(pitches)) if pitches else None,
        "pitch_max": midi_note_name(max(pitches)) if pitches else None,
        "register_counts": register_counts,
        "octave_counts": dict(sorted(octave_counts.items())),
        "velocity_min": min(velocities) if velocities else None,
        "velocity_max": max(velocities) if velocities else None,
        "sixteen_bar_module_note_counts": dict(sorted(module_counts.items())),
        "channels": {
            str(channel + 1): {
                "notes": note_counts[channel],
                "programs": [
                    {"tick": tick, "program": program, "name": GM_NAMES.get(program, f"GM {program + 1}")}
                    for tick, program in programs[channel]
                ],
            }
            for channel in sorted(set(programs) | set(note_counts))
        },
        "track_stats": track_stats,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
