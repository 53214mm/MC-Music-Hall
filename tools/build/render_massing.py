"""体块出图：把 plan_massing.py 的数字画成正投影，供批准方案前目视检查。

数字只有一个来源（plan_massing.geometry），所以图和表必然一致。
只读；只在 build/music_hall/massing_preview.txt 留档，不碰任何建筑产物。
用法：python tools/build/render_massing.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plan_massing as P

SCALE_X, SCALE_Y = 2, 2      # 每字符代表 2 格宽 × 2 格高
BLOCK = '██'


def render_side(g):
    """东立面（沿 Z 看）。左 = 北端后殿，右 = 南端门楼双塔。"""
    z0, z1 = g['z_back'], g['z_portal']
    cols = (z1 - z0 + 1) // SCALE_X + 1
    h = [0] * cols

    def paint(za, zb, y):
        for z in range(int(za), int(zb) + 1):
            c = (z - z0) // SCALE_X
            if 0 <= c < cols:
                h[c] = max(h[c], y)

    core_back = g['z_front'] - P.NAVE_LEN - P.NARTHEX_D
    nave_front = g['z_front']
    # 核心体块：逐列算坡屋顶，得到真实的坡面而不是一个方块
    midway = (z0 + core_back) / 2
    half = max(1.0, (core_back - z0) / 2)
    for z in range(z0, core_back + 1):
        c = (z - z0) // SCALE_X
        frac = abs(z - midway) / half
        h[c] = max(h[c], g['ridge'] - round(frac * (g['ridge'] - g['eave'])))
    paint(core_back, core_back + P.NARTHEX_D, g['eave'] - 40)
    paint(core_back + P.NARTHEX_D, nave_front, g['nave_ridge'])
    paint(z0, z1, g['aisle_top'])
    # 中央塔楼（鼓座 + 尖顶），位于核心体块中部
    cx = int(((z0 + core_back) / 2 - z0) // SCALE_X)
    for c in range(max(0, cx - 4), min(cols, cx + 5)):
        h[c] = max(h[c], g['lantern_top'])
    for c in range(max(0, cx - 1), min(cols, cx + 2)):
        h[c] = max(h[c], g['apex'])
    # 南端双塔
    for c in range(max(0, cols - g['tower_w'] // SCALE_X), cols):
        h[c] = max(h[c], g['tower_apex'])
    return h, cols, z0, z1


def render_front(g):
    """南立面（沿 X 看）。左 = 西塔，中 = 中殿，右 = 东塔。"""
    x0, x1 = g['x0'], g['x1']
    cols = (x1 - x0 + 1) // SCALE_X + 1
    h = [0] * cols

    def paint(xa, xb, y):
        for x in range(int(xa), int(xb) + 1):
            c = (x - x0) // SCALE_X
            if 0 <= c < cols:
                h[c] = max(h[c], y)

    paint(x0, x1, g['aisle_top'])
    nave_x0 = P.CENTER - P.NAVE_W // 2
    nave_x1 = P.CENTER + P.NAVE_W // 2
    paint(nave_x0, nave_x1, g['nave_ridge'])
    paint(x0, nave_x0, g['tower_apex'])
    paint(nave_x1, x1, g['tower_apex'])
    return h, cols, x0, x1


def draw(h, cols, total_h, left_label, right_label, axis_label):
    lines = []
    for y in range(total_h, -1, -SCALE_Y):
        lines.append(f'{y:4} ' + ''.join(BLOCK if h[c] >= y else '  ' for c in range(cols)))
    pad = max(2, cols * 2 - len(left_label) - len(right_label) - 4)
    lines.append('     ' + left_label + ' ' * pad + right_label)
    lines.append('     ' + axis_label)
    return lines


def main():
    lines = []

    def say(text=''):
        lines.append(text)
        print(text)

    g = P.geometry(6, 35)
    say('=' * 78)
    say('重构方案体块投影（数字来自 plan_massing.geometry，与方案表格同源）')
    say('=' * 78)
    say(f"檐口 {g['eave']}  核心屋脊 {g['ridge']}  侧廊 {g['aisle_top']}  "
        f"中殿屋脊 {g['nave_ridge']}  塔顶 {g['tower_apex']}  中央尖顶 {g['apex']}")
    say(f"总宽 {g['total_w']}  总长 {g['total_d']}  总高 {g['total_h']}  "
        f"高:宽 {g['total_h']/g['total_w']:.2f}  长:宽 {g['total_d']/g['total_w']:.2f}")
    say(f'比例尺：每字符 {SCALE_X} 格宽 × {SCALE_Y} 格高')

    say()
    say('【东立面】沿 Z 看（左 = 北端后殿，右 = 南端门楼双塔）')
    say('-' * 78)
    h, cols, z0, z1 = render_side(g)
    lines.extend(draw(h, cols, g['total_h'], '后殿', '双塔', f'     Z {z0}（北）-> {z1}（南）'))

    say()
    say('【南立面】沿 X 看（左 = 西塔，中 = 中殿，右 = 东塔）')
    say('-' * 78)
    h, cols, x0, x1 = render_front(g)
    lines.extend(draw(h, cols, g['total_h'], '西塔', '东塔', f'     X {x0}（西）-> {x1}（东）'))

    say()
    say('【天际线高度序列】自上而下，括号内为相邻落差')
    levels = [('中央尖顶', g['apex']), ('塔顶', g['tower_apex']),
              ('核心屋脊', g['ridge']), ('中殿屋脊', g['nave_ridge']),
              ('侧廊屋面', g['aisle_top']), ('地面', 0)]
    prev = None
    for name, y in levels:
        gap = '' if prev is None else f'（落差 {prev - y} 格）'
        say(f'  Y={y:>4}  {name:<8}{gap}')
        prev = y
    smallest = min(g['apex'] - g['tower_apex'], g['tower_apex'] - g['ridge'],
                   g['ridge'] - g['nave_ridge'], g['nave_ridge'] - g['aisle_top'])
    say()
    say(f'判据：相邻层次落差 ≥12 格；本方案最小落差 = {smallest} 格')

    target = Path(__file__).resolve().parents[2] / 'build' / 'music_hall' / 'massing_preview.txt'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'\n已留档：{target}')


if __name__ == '__main__':
    main()
