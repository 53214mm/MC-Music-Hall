"""可行域实测：方案要"把侧廊扩到净宽 5 格"，先量清楚核心两侧到底有多少可自由占用的空间。

只读。用法：python tools/build/measure_side_channels.py
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_music_hall as B
from hall_connections import generate_connections

modules, placement = B.load_modules()
shell = B.make_shell()
control, report = generate_connections(modules, B.transform, B.is_north)

X0, X1 = -7, 49        # 核心机房的 X 范围（43 宽机房 + 两侧检修带）
Z0, Z1 = -37, 38       # 核心机房 Z 范围

print('=' * 78)
print('核心机房两侧：现状占用 vs 可自由占用（设计坐标）')
print('=' * 78)

# 按 X 统计：该列上属于"模块 / 外壳 / 控制电路"的方块数与高度范围
per_x = defaultdict(lambda: {'module': 0, 'shell': 0, 'control': 0, 'y': []})
for (x, y, z), s in modules.items():
    if X0 <= x <= X1 and Z0 <= z <= Z1:
        per_x[x]['module'] += 1
        per_x[x]['y'].append(y)
for (x, y, z), s in shell.items():
    if X0 <= x <= X1 and Z0 <= z <= Z1:
        per_x[x]['shell'] += 1
        per_x[x]['y'].append(y)
for (x, y, z), s in control.items():
    if X0 <= x <= X1 and Z0 <= z <= Z1:
        per_x[x]['control'] += 1
        per_x[x]['y'].append(y)

print(f'{"X":>4}{"模块":>7}{"外壳":>7}{"控制":>7}{"Y范围":>16}  说明')
for x in range(X0, X1 + 1):
    d = per_x.get(x)
    if not d:
        print(f'{x:>4}{0:>7}{0:>7}{0:>7}{"—":>16}  完全空闲')
        continue
    ylo, yhi = (min(d['y']), max(d['y'])) if d['y'] else ('-', '-')
    note = []
    if d['module']: note.append('机房模块')
    if d['control']: note.append('控制电路')
    if d['shell'] and not d['module']: note.append('外壳填充')
    print(f'{x:>4}{d["module"]:>7}{d["shell"]:>7}{d["control"]:>7}'
          f'{f"{ylo}..{yhi}":>16}  {"、".join(note)}')

print()
print('=' * 78)
print('按区域汇总：核心两侧的 X 带')
print('=' * 78)
for name, xa, xb in [('西侧带', X0, X0 + 7), ('东侧带', X1 - 7, X1)]:
    m = sum(per_x[x]['module'] for x in range(xa, xb + 1) if x in per_x)
    s = sum(per_x[x]['shell'] for x in range(xa, xb + 1) if x in per_x)
    c = sum(per_x[x]['control'] for x in range(xa, xb + 1) if x in per_x)
    print(f'{name} X={xa}..{xb}（{xb-xa+1} 格）：模块 {m}  外壳 {s}  控制 {c}')

print()
print('控制电路在这条带里的 X 分布：')
band_x = Counter()
for (x, y, z) in control:
    if X0 <= x <= X1 and Z0 <= z <= Z1:
        band_x[x] += 1
for x in sorted(band_x):
    bar = '#' * min(60, band_x[x] // 90)
    print(f'  X={x:>3}  {band_x[x]:>5} 块  {bar}')

print()
print('控制电路在这条带里的 Z 分布（前 12）：')
band_z = Counter()
for (x, y, z) in control:
    if X0 <= x <= X1 and Z0 <= z <= Z1:
        band_z[z] += 1
for z, n in sorted(band_z.items())[:12]:
    print(f'  Z={z:>3}  {n:>5} 块')
