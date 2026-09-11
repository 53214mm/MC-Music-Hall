"""体块冲突探测：方案的新增体块落在哪些现状方块上？有没有碰到不可动的部分？

只读。用法：
  python tools/build/probe_new_massing.py            # 新增体块 × 现状占用
  python tools/build/probe_new_massing.py --towers   # 南端现状塔的精确几何
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_music_hall as B

modules, placement = B.load_modules()
shell = B.make_shell()

# 方案 §四 的平面（设计坐标）
PORTAL = ('外凸门廊', 20, 24, 6)          # 宽 20、深 6、从 Z=86 往南
NAVE_EXT = ('中殿段', 28, 44, 44)         # 净宽 28、长 44、高 44
APSE = ('后殿', 40, 12, 30)               # 宽约 40、深 12

NEW_Z_RANGES = {
    '南端门廊': (86, 91),
    '南端中殿段': (42, 85),
    '北端后殿': (-49, -38),
}
# 核心体块自身（现状已存在），不列为新增
CORE_Z = (-37, 38)

MODULE_TAG = lambda s: s[2]


def scan(z0, z1):
    """统计给定 Z 范围内的方块归属与最高点。"""
    groups = Counter()
    top = 0
    offlimits = []
    for (x, y, z), (name, props, group) in shell.items():
        if z0 <= z <= z1:
            groups[f'外壳·{name}'] += 1
            top = max(top, y)
    for (x, y, z), (name, props, group) in modules.items():
        if z0 <= z <= z1:
            groups[f'模块{group}·{name}'] += 1
            top = max(top, y)
            offlimits.append((x, y, z, name, group))
    return groups, top, offlimits


def report_towers():
    """南端现状塔的精确几何：X 带、Z 带、尖顶高度。"""
    tall = defaultdict(list)
    for (x, y, z), (name, _, _) in shell.items():
        if 42 <= z <= 91 and y >= 60:
            tall[x].append((y, z, name))
    if not tall:
        print('南端 Z=42..91、Y>=60 没有方块')
        return
    xs = sorted(tall)
    tops = {x: max(y for y, _, _ in tall[x]) for x in xs}
    print('=' * 84)
    print('南端现状塔（Z=42..91，Y>=60）')
    print('=' * 84)
    print(f'  X 范围：{xs[0]}..{xs[-1]}（共 {len(xs)} 列有高方块）')
    print(f'  Z 范围：{min(z for x in xs for _, z, _ in tall[x])}..'
          f'{max(z for x in xs for _, z, _ in tall[x])}')
    print(f'  最高点：Y={max(tops.values())}（出现在 X={[x for x in xs if tops[x] == max(tops.values())]}）')
    print()
    print('  两个连续区段（按 X 断裂处切分）：')
    bands, current = [], [xs[0]]
    for x in xs[1:]:
        if x - current[-1] <= 2:
            current.append(x)
        else:
            bands.append(current)
            current = [x]
    bands.append(current)
    for band in bands:
        width = band[-1] - band[0] + 1
        peak = max(tops[x] for x in band)
        print(f'    X={band[0]}..{band[-1]}  宽 {width} 格  尖顶 Y={peak}')
    print()
    print('  对照方案：方案塔宽 19 格 —— 与实测宽度一致，塔位置可作为重构基准。')


def main():
    if '--towers' in sys.argv:
        report_towers()
        return

    print('=' * 82)
    print('方案新增体块 × 现状占用（设计坐标；核心体块 Z=-37..38 不在新增范围内）')
    print('=' * 82)
    for label, (z0, z1) in NEW_Z_RANGES.items():
        groups, top, offlimits = scan(z0, z1)
        total = sum(groups.values())
        print(f'\n【{label}】Z={z0}..{z1}（{z1-z0+1} 格）')
        print(f'  现状方块 {total} 个，最高点 Y={top if total else "-"}')
        if offlimits:
            print(f'  ⚠ 落在音乐模块上：{len(offlimits)} 格 —— 不可动！')
            for item in offlimits[:5]:
                print(f'      {item}')
        else:
            print('  ✅ 不涉及任何音乐模块')
        if groups:
            print('  归属前 6：')
            for name, n in groups.most_common(6):
                print(f'      {name:<28}{n:>7}')

    print()
    print('=' * 82)
    print('结论')
    print('=' * 82)
    all_ok = True
    for label, (z0, z1) in NEW_Z_RANGES.items():
        _, top, offlimits = scan(z0, z1)
        status = '可自由重建' if not offlimits else f'⚠ 压到模块 {len(offlimits)} 格'
        if offlimits:
            all_ok = False
        print(f'  {label:<12} Z={z0}..{z1:<5} 现状最高 Y={top:<4} {status}')
    print()
    print('  全部新增区域都不涉及音乐模块' if all_ok
          else '  存在与音乐模块重叠的区域，方案必须修改')
    print('  注：南端最高 Y=93 是现状两座钟楼，它们与方案的双塔位置重叠，需一并重建。')
    print('      想看塔的精确几何：python tools/build/probe_new_massing.py --towers')


if __name__ == '__main__':
    main()
