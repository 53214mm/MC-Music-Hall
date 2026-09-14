from __future__ import annotations

import argparse
import csv
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path

from analyze_midi import midi_note_name, parse_track, read_vlq, tick_to_seconds


REDSTONE_TPS = 10
MODULE_TICKS = 320  # 16 bars at 120 BPM and 10 redstone ticks/second.
FULL_SONG_TICKS = 3475


def parse_midi(path: Path) -> tuple[int, list[dict], list[tuple[int, int]]]:
    blob = path.read_bytes()
    if blob[:4] != b"MThd":
        raise ValueError("Not a Standard MIDI file")
    header_length = struct.unpack(">I", blob[4:8])[0]
    _, track_count, division = struct.unpack(">HHH", blob[8:14])
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
    notes = []
    for track in tracks:
        for tick, kind, value in track["events"]:
            if kind != "note_on":
                continue
            channel, midi_note, velocity = value
            seconds = tick_to_seconds(tick, tempo_map, division)
            notes.append(
                {
                    "source_tick": tick,
                    "seconds": seconds,
                    "redstone_tick": round(seconds * REDSTONE_TPS),
                    "track": track["index"],
                    "channel": channel + 1,
                    "midi_note": midi_note,
                    "velocity": velocity,
                }
            )
    return division, notes, tempo_map


def map_note(midi_note: int, piano: bool = False) -> dict:
    original = midi_note
    transposed = False
    if midi_note < 30:
        midi_note += 12
        transposed = True
    if piano and 42 <= midi_note <= 53:
        midi_note += 12
        transposed = True
    if 30 <= midi_note <= 53:
        instrument = 1
        instrument_name = "Double Bass"
        support = "Oak Planks"
        support_zh = "橡木木板"
        clicks = midi_note - 30
    elif 54 <= midi_note <= 78:
        instrument = 0
        instrument_name = "Harp/Piano"
        support = "Dirt"
        support_zh = "泥土"
        clicks = midi_note - 54
    elif 79 <= midi_note <= 102:
        instrument = 8
        instrument_name = "Chime"
        support = "Packed Ice"
        support_zh = "浮冰"
        clicks = midi_note - 78
    else:
        raise ValueError(f"Pitch {midi_note_name(original)} cannot be mapped to vanilla note blocks")
    return {
        "original_note": midi_note_name(original),
        "played_note": midi_note_name(midi_note),
        "transposed": transposed,
        "instrument": instrument,
        "instrument_name": instrument_name,
        "support": support,
        "support_zh": support_zh,
        "clicks": clicks,
        "nbs_key": 33 + clicks,
    }


def encode_delay(delta: int) -> list[int]:
    if delta < 0:
        raise ValueError("Negative delay")
    delays = [4] * (delta // 4)
    if delta % 4:
        delays.append(delta % 4)
    return delays


def write_string(handle, value: str) -> None:
    encoded = value.encode("utf-8")
    handle.write(struct.pack("<i", len(encoded)))
    handle.write(encoded)


def write_nbs(path: Path, title: str, notes: list[dict], length: int, source_name: str) -> None:
    by_tick = defaultdict(list)
    for note in notes:
        by_tick[note["local_tick"]].append(note)
    max_layers = max((len(values) for values in by_tick.values()), default=1)
    with path.open("wb") as handle:
        handle.write(struct.pack("<hBBhh", 0, 5, 16, length, max_layers))
        write_string(handle, title)
        write_string(handle, "Generated for a Minecraft redstone build")
        write_string(handle, "ryo / EGOIST")
        write_string(handle, "10 t/s vanilla-compatible quantization; low outliers raised one octave")
        handle.write(struct.pack("<hBBB", 1000, 0, 10, 4))
        handle.write(struct.pack("<iiiii", 0, 0, 0, len(notes), 0))
        write_string(handle, source_name)
        handle.write(struct.pack("<BBh", 0, 0, 0))

        previous_tick = -1
        for tick in sorted(by_tick):
            handle.write(struct.pack("<h", tick - previous_tick))
            previous_tick = tick
            previous_layer = -1
            for layer, note in enumerate(sorted(by_tick[tick], key=lambda item: item["midi_note"])):
                handle.write(struct.pack("<h", layer - previous_layer))
                previous_layer = layer
                velocity = max(1, min(100, round(note["velocity"] * 100 / 127)))
                handle.write(
                    struct.pack(
                        "<BBBbh",
                        note["instrument"],
                        note["nbs_key"],
                        velocity,
                        100,
                        0,
                    )
                )
            handle.write(struct.pack("<h", 0))
        handle.write(struct.pack("<h", 0))

        for layer in range(max_layers):
            write_string(handle, f"Chord voice {layer + 1}")
            handle.write(struct.pack("<BBB", 0, 100, 100))
        handle.write(struct.pack("<B", 0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("midi", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument('--piano', action='store_true', help='Approved piano v3 voicing')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    _, notes, _ = parse_midi(args.midi)
    for note in notes:
        note.update(map_note(note["midi_note"], piano=args.piano))
        note["module"] = note["redstone_tick"] // MODULE_TICKS + 1
        note["local_tick"] = note["redstone_tick"] % MODULE_TICKS
    transposed_source_count = sum(note["transposed"] for note in notes)

    merged_notes = {}
    for note in notes:
        # Preserve the exact v3 preview: merge only the collisions already
        # merged in v1, not new unisons introduced by the approved voicing.
        base = map_note(note['midi_note'])
        key = (note["redstone_tick"], base["instrument"], base["nbs_key"])
        current = merged_notes.get(key)
        if current is None or note["velocity"] > current["velocity"]:
            merged_notes[key] = note
    duplicate_count = len(notes) - len(merged_notes)
    notes = list(merged_notes.values())

    schedule_path = args.output / "departures_note_schedule.csv"
    with schedule_path.open("w", newline="", encoding="utf-8-sig") as handle:
        fields = [
            "module", "global_tick", "local_tick", "seconds", "bar", "beat",
            "chord_voice", "original_note", "played_note", "transposed",
            "instrument", "support_block", "right_clicks", "velocity",
            "source_tick", "track", "channel",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        chord_positions = Counter()
        for note in sorted(notes, key=lambda item: (item["redstone_tick"], item["midi_note"])):
            chord_positions[note["redstone_tick"]] += 1
            writer.writerow(
                {
                    "module": note["module"],
                    "global_tick": note["redstone_tick"],
                    "local_tick": note["local_tick"],
                    "seconds": f'{note["seconds"]:.3f}',
                    "bar": note["redstone_tick"] // 20 + 1,
                    "beat": f'{(note["redstone_tick"] % 20) / 5 + 1:.1f}',
                    "chord_voice": chord_positions[note["redstone_tick"]],
                    "original_note": note["original_note"],
                    "played_note": note["played_note"],
                    "transposed": "yes" if note["transposed"] else "no",
                    "instrument": note["instrument_name"],
                    "support_block": note["support_zh"],
                    "right_clicks": note["clicks"],
                    "velocity": note["velocity"],
                    "source_tick": note["source_tick"],
                    "track": note["track"],
                    "channel": note["channel"],
                }
            )

    module_count = math.ceil(FULL_SONG_TICKS / MODULE_TICKS)
    module_stats = []
    total_repeaters = 0
    timing_path = args.output / "departures_timing_modules.csv"
    with timing_path.open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["module", "event", "local_tick", "delta_ticks", "repeater_settings", "notes_at_event"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for module in range(1, module_count + 1):
            module_notes = [note for note in notes if note["module"] == module]
            ticks = sorted({note["local_tick"] for note in module_notes})
            module_length = MODULE_TICKS if module < module_count else FULL_SONG_TICKS - MODULE_TICKS * (module - 1)
            previous_tick = 0
            repeaters = 0
            for event_number, tick in enumerate(ticks, 1):
                delta = tick - previous_tick
                settings = encode_delay(delta)
                repeaters += len(settings)
                writer.writerow(
                    {
                        "module": module,
                        "event": event_number,
                        "local_tick": tick,
                        "delta_ticks": delta,
                        "repeater_settings": "-".join(map(str, settings)) or "start",
                        "notes_at_event": sum(note["local_tick"] == tick for note in module_notes),
                    }
                )
                previous_tick = tick
            tail = module_length - previous_tick
            tail_settings = encode_delay(tail)
            repeaters += len(tail_settings)
            writer.writerow(
                {
                    "module": module,
                    "event": "handoff",
                    "local_tick": module_length,
                    "delta_ticks": tail,
                    "repeater_settings": "-".join(map(str, tail_settings)) or "immediate",
                    "notes_at_event": 0,
                }
            )
            active_ticks = len(ticks)
            max_chord = max((sum(note["local_tick"] == tick for note in module_notes) for tick in ticks), default=0)
            module_stats.append(
                {
                    "module": module,
                    "length_ticks": module_length,
                    "notes": len(module_notes),
                    "active_ticks": active_ticks,
                    "max_chord": max_chord,
                    "repeaters": repeaters,
                }
            )
            total_repeaters += repeaters
            write_nbs(
                args.output / f"departures_module_{module:02d}.nbs",
                f"Departures - module {module:02d}",
                module_notes,
                module_length,
                args.midi.name,
            )

    all_notes_for_nbs = []
    for note in notes:
        copied = dict(note)
        copied["local_tick"] = note["redstone_tick"]
        all_notes_for_nbs.append(copied)
    write_nbs(
        args.output / "departures_full_10tps.nbs",
        "Departures - Guilty Crown",
        all_notes_for_nbs,
        FULL_SONG_TICKS,
        args.midi.name,
    )

    supports = Counter(note["support_zh"] for note in notes)
    placed_redstone_reserve = len(notes) + sum(item["active_ticks"] for item in module_stats) + 256
    raw_redstone = len(notes) + total_repeaters * 3 + placed_redstone_reserve
    materials = {
        "voicing": "approved_piano_v3" if args.piano else "original",
        "note_blocks": len(notes),
        "support_blocks": dict(supports),
        "timing_repeaters_exact": total_repeaters,
        "placed_redstone_dust_reserve": placed_redstone_reserve,
        "raw_planks_for_note_blocks": len(notes) * 8,
        "raw_stone_for_repeaters": total_repeaters * 3,
        "raw_sticks_for_repeaters": total_repeaters * 2,
        "raw_redstone_dust_including_crafting_and_reserve": raw_redstone,
        "source_notes_transposed_one_octave": transposed_source_count,
        "merged_duplicate_triggers": duplicate_count,
        "modules": module_stats,
    }
    (args.output / "departures_materials.json").write_text(
        json.dumps(materials, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    guide = f"""# Departures 红石音乐机施工数据

音色方案：{'用户确认的钢琴 v3；F#2–F3 升八度用钢琴，保留深低音及钟琴。' if args.piano else '原始音色方案。'}
此目录为独立版本，旧版仍保留。中继器数量是逻辑时间线统计；尚未包含经实机验证的空间布线、隔离和控制器。NBS 模块仍需导出并测试，不能视作已验证的逐方块蓝图。

## 固定参数

- 量化速度：10 红石刻/秒
- 模块：{module_count} 个，每个 16 小节；最后一模块保留到 MIDI 的 5:47.5
- 音符盒：{len(notes)}
- 时间线中继器：{total_repeaters}（已按 4、3、2、1 刻压缩空拍，并包含模块交接尾段）
- 线路红石粉储备：{placed_redstone_reserve}
- 调整了八度的原始音符事件：{transposed_source_count}
- 升八度后与既有音重合并合并的触发：{duplicate_count}

## 音色垫块

"""
    for support, count in supports.items():
        guide += f"- {support}：{count}\n"
    guide += "\n## 文件用途\n\n"
    guide += "- `departures_full_10tps.nbs`：整首试听和总校验。\n"
    guide += "- `departures_module_01.nbs` 至 `departures_module_11.nbs`：分别在 OpenNBS 中导出结构。\n"
    guide += "- `departures_note_schedule.csv`：每个音符盒的时间、音高、垫块和右击次数。\n"
    guide += "- `departures_timing_modules.csv`：主时间线每一段中继器的档位。\n"
    guide += "- `departures_materials.json`：精确逻辑材料统计。\n"
    guide += "\n## 施工规则\n\n"
    guide += "1. 每模块从 `local_tick=0` 接收启动脉冲。\n"
    guide += "2. 按 timing CSV 依次放置中继器；`4-4-2` 表示连续放两个四档、一个二档中继器。\n"
    guide += "3. 每到一个事件点，从主线侧面引出该行所有音符盒；同一 global_tick 的音必须同时供电。\n"
    guide += "4. 音符盒下面按 schedule CSV 放对应垫块，然后从默认 F# 音高右击指定次数。\n"
    guide += "5. 每模块 handoff 行的最后一个中继器输出接下一模块启动端。\n"
    guide += "6. 音符盒顶部始终留空气；相邻事件分支用中继器或实体方块隔离，禁止红石粉串线。\n"
    (args.output / "README.md").write_text(guide, encoding="utf-8")

    print(json.dumps(materials, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
