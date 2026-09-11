"""侧廊可行性探测：两侧 7 格带里到底是"墙"还是"实心"?逐 Y 层量。

只读。用法：python tools/build/probe_aisles.py
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_music_hall as B

modules, _ = B.load_modules()
shell = B.make_shell()
blocks = {**modules, **shell}

WEST = list(range(-7, 0))     # X=-7..-1
EAST = list(range(43, 50))    # X=43..49
Z0, Z1 = -37, 38


def census(xs, y):
    """某一 Y 层、给定 X 带、核心 Z 范围内的方块数与非空 Z 段。"""
    occupied = set()
    for (x, yy, z), (name, _, _) in blocks.items():
        if yy == y and x in xs and Z0 <= z <= Z1:
            occupied.add(z)
    return occupied


print('=' * 80)
print('侧廊可行性：两侧 7 格带逐层占用（核心 Z=-37..38，共 76 列）')
print('=' * 80)
solid_levels = []
for y in range(-3, 105):
    w = census(WEST, y)
    e = census(EAST, y)
    if not w and not e:
        continue
    solid_levels.append((y, len(w), len(e)))

print(f'两侧带在 Y={solid_levels[0][0]}..{solid_levels[-1][0]} 全部有方块；'
      f'其中"整层填满（≥70 列）"的层数：'
      f'西 {sum(1 for _, w, _ in solid_levels if w >= 70)}，'
      f'东 {sum(1 for _, _, e in solid_levels if e >= 70)}')

print()
print('=' * 80)
print('如果要挖出侧廊，需要移除多少方块')
print('=' * 80)
print(f'{"方案":<34}{"移除量":>10}  说明')
for aisle_w, height in [(5, 20), (5, 30), (6, 20)]:
    per_side = aisle_w * 76 * height
    print(f'{"净宽 " + str(aisle_w) + " × 进深 76 × 高 " + str(height):<34}'
          f'{per_side * 2:>10}  两侧合计（约为外壳 70835 的 {per_side*2/70835*100:.0f}%）')

print()
print('=' * 80)
print('保留的内墙厚度（挖掉后剩余）')
print('=' * 80)
print(f'  两侧带各 7 格；挖掉净宽 5 格后，内墙剩 {7-5} 格，外墙再另算')
print(f'  → 内墙 2 格厚，正好等于方案 §九 要求的"墙体 2~3 格厚"')

