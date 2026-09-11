"""阶段 1 验收：现状 vs 阶段 1 的轮廓对比（紧凑表 + 缩放图）。

只读。用法：python tools/build/render_phase1_elevation.py
"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_music_hall as B
import phase1_massing as P1


def current_blocks():
    modules, _ = B.load_modules()
    return {**modules, **B.make_shell()}


def tops(blocks, key):
    top = defaultdict(lambda: -999)
    for (x, y, z) in blocks:
        k = key(x, y, z)
        if y > top[k]:
            top[k] = y
    return top


def profile_table(name, cur, p1, lo, hi, step):
    print(f'--- {name} ---')
    print(f'{"位置":>6}{"现状顶":>8}{"阶段1顶":>8}   变化')
    for k in range(lo, hi + 1, step):
        c, n = cur.get(k, -999), p1.get(k, -999)
        ctext = '—' if c < 0 else str(c)
        ntext = '—' if n < 0 else str(n)
        if c < 0:
            change = '新增'
        elif n < 0:
            change = '移除'
        else:
            d = n - c
            change = f'{d:+d}' if d else '不变'
        print(f'{k:>6}{ctext:>8}{ntext:>8}   {change}')
    print()


def peak_levels(blocks):
    """按列高统计，找出所有"高度层次"（有多少列的顶落在某高度附近）。"""
    top = defaultdict(lambda: -999)
    for (x, y, z) in blocks:
        top[(x, z)] = max(top[(x, z)], y)
    buckets = defaultdict(int)
    for v in top.values():
        if v < 0:
            continue
        buckets[v // 5 * 5] += 1
    return buckets


def main():
    cur = current_blocks()
    p1 = P1.generate()

    cur_z = tops(cur, lambda x, y, z: z)
    p1_z = tops(p1, lambda x, y, z: z)

    allc = [v for v in cur_z.values() if v > 0]
    alln = [v for v in p1_z.values() if v > 0]
    print('=' * 72)
    print('阶段 1 验收 · 轮廓对比')
    print('=' * 72)
    print(f'{"":22}{"现状":>12}{"阶段 1":>12}')
    print(f'{"最高点":22}{max(allc):>12}{max(alln):>12}')
    print(f'{"总宽":22}{len(set(x for x, y, z in cur)):>12}{len(set(x for x, y, z in p1)):>12}')
    print(f'{"总长":22}{len(set(z for x, y, z in cur)):>12}{len(set(z for x, y, z in p1)):>12}')
    print(f'{"方块总数":22}{len(cur):>12}{len(p1):>12}')
    print()

    print('=' * 72)
    print('侧立面轮廓（沿 Z 看）：每个 Z 切面的最高点')
    print('=' * 72)
    zlo = min(min(cur_z), min(p1_z))
    zhi = max(max(cur_z), max(p1_z))
    profile_table('侧立面', cur_z, p1_z, zlo, zhi, 6)

    cur_x = tops(cur, lambda x, y, z: x)
    p1_x = tops(p1, lambda x, y, z: x)
    print('=' * 72)
    print('正立面轮廓（沿 X 看）：每个 X 切面的最高点')
    print('=' * 72)
    xlo = min(min(cur_x), min(p1_x))
    xhi = max(max(cur_x), max(p1_x))
    profile_table('正立面', cur_x, p1_x, xlo, xhi, 4)

    print('=' * 72)
    print('高度层次分布（有多少列的顶落在各高度带）——层次越多，剪影越有起伏')
    print('=' * 72)
    cb, nb = peak_levels(cur), peak_levels(p1)
    keys = sorted(set(cb) | set(nb), reverse=True)
    print(f'{"高度带":>8}{"现状列数":>10}{"阶段1列数":>11}')
    for k in keys:
        print(f'{k:>4}-{k+4:<3}{cb.get(k, 0):>10}{nb.get(k, 0):>11}')


if __name__ == '__main__':
    main()
