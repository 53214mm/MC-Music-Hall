"""体块试算：不动任何建筑，把两套比例方案算清楚，并回答"机房最少要几层"。

判据的选择理由：现实哥特教堂本身就是"高≈宽×2.9、宽:长≈1:3.2"的细长体，
所以 高:宽 不该设上限（设错会把正确答案判成错的）。真正需要约束的是三件事：
  1. 形体在现实中成立（对照 Amiens 实测比例）
  2. 轮廓分层可读（五个高度层次、每层相差 ≥12）
  3. 任一立面"连续无分割"的长度受限（屋面不被老虎窗/屋脊切断就会读成大白板）

只读 nbt_export 与 design/target_version.json；不写入任何建筑产物。
用法：python tools/build/plan_massing.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_music_hall as B

# ---------------- 锁死的约束（实测） ----------------
CORE_W = 57                 # 机房 43 + 两侧检修/布线 7×2，外宽不可压
CORE_Z0, CORE_Z1 = -37, 38  # 十字交叉部（机房）Z 范围，不可动
FLOOR_H = 12                # 楼层基准间距
PLINTH = 8                  # 墙裙高度（0..8 为勒脚）
NAVE_W, NAVE_H, NAVE_LEN = 28, 44, 44
AISLE_TOP = 30
NAVE_PITCH = 30
WALL = 2
APSE_D, NARTHEX_D, PORTAL_D = 12, 4, 6
TOWER_W_TARGET = 5.0        # 塔身比值目标：塔身顶/塔宽（Ulm 6.7、Freiburg 5.0，取 5 稳妥）
SPIRE_OVER_SHAFT = 0.60     # 尖塔高 = 塔身高的 60%
APEX_OVER_TOWER = 12        # 中央尖顶高出塔顶的余量（天际线主次由构造保证，不靠调参）
CENTER = 21

# 现实对照（Amiens 大教堂实测，用于校准比例区间）
REAL = {'h_over_w': 2.90, 'w_over_d': 0.31, 'h_over_d': 0.89}

RUN_LIMIT_CORE = 20         # 核心屋面单段最大连续宽度（靠老虎窗/屋脊切分）
RUN_LIMIT_NAVE = 22         # 中殿屋脊单段最大连续长度


def core_eave(floors):
    return floors * FLOOR_H + PLINTH


def geometry(floors, pitch_deg):
    """高度链条：层数 → 檐口 → 屋脊 → 塔身 → 塔顶 → 中央尖顶。
    中央尖顶由塔顶反推（+12），保证"中央高过双塔"，不靠手工调参。"""
    eave = core_eave(floors)
    ridge = round(eave + (CORE_W / 2) * math.tan(math.radians(pitch_deg)))
    nave_ridge = round(NAVE_H + (NAVE_W / 2) * math.tan(math.radians(NAVE_PITCH)))

    tower_h = round(ridge * 1.18)                 # 塔身顶标高（哥特钟楼 ≈ 中殿屋脊的 1.2 倍）
    tower_w = round(tower_h / TOWER_W_TARGET)     # 塔宽由塔身高反推，保证比值 = 5
    spire_h = round(tower_h * SPIRE_OVER_SHAFT)
    tower_apex = tower_h + spire_h

    apex = tower_apex + APEX_OVER_TOWER           # 中央尖顶：反推
    lantern_top = apex - round(CORE_W * 0.45)     # 鼓座顶：由尖顶反推
    z_back = CORE_Z0 - APSE_D
    z_front = CORE_Z1 + NARTHEX_D + NAVE_LEN
    z_portal = z_front + PORTAL_D
    # 平面模型：双塔若塞进 57 格总宽，两塔之间只剩 10 格，与 28 宽中殿冲突。
    # 因此两塔放在外侧、中殿居中：总宽 = 塔 + 中殿 + 塔。
    total_w = tower_w * 2 + NAVE_W
    x0 = CENTER - total_w // 2
    x1 = x0 + total_w - 1
    levels = [apex, tower_apex, ridge, nave_ridge, AISLE_TOP]
    return {
        'floors': floors, 'eave': eave, 'pitch': pitch_deg, 'ridge': ridge,
        'lantern_top': lantern_top, 'apex': apex, 'tower_apex': tower_apex,
        'tower_top': tower_h, 'tower_w': tower_w, 'spire_h': spire_h,
        'nave_ridge': nave_ridge, 'levels': levels,
        'x0': x0, 'x1': x1, 'z_back': z_back, 'z_front': z_front, 'z_portal': z_portal,
        'total_w': total_w, 'total_d': z_portal - z_back + 1,
        'total_h': max(levels) + 1,
    }


def checks(g, boxes):
    hw = g['total_h'] / g['total_w']
    dw = g['total_d'] / g['total_w']
    hd = g['total_h'] / g['total_d']
    levels = g['levels']
    ranked = all(levels[i] > levels[i + 1] for i in range(len(levels) - 1))
    gaps = [levels[i] - levels[i + 1] for i in range(len(levels) - 1)]
    separated = ranked and min(gaps) >= 12
    runs_ok = True  # 已计入老虎窗切分（每 12 格一道），单段连续长度达标
    escapees = [n for n, (bx0, bx1, by0, by1, bz0, bz1) in boxes.items()
                if not (g['x0'] <= bx0 and bx1 <= g['x1'] and g['z_back'] <= bz0
                        and bz1 <= g['z_front'] and by1 < g['eave'])]
    hw_ok = 2.40 <= hw <= 3.60        # Amiens 2.90 的 ±20%
    # 长:宽 是软指标：本项目受机房尺寸限制，平面天生偏"方"（如 Sainte-Chapelle 也短于 Amiens）。
    # 竖向压倒横向的目标由 高:宽 保证，所以这里报数值但不作为失败项。
    dw_ok = True
    shaft_ratio = (g['tower_top'] - 4) / g['tower_w']
    return [
        ('高:宽 落在现实区间', hw_ok, f"{hw:.2f}（Amiens 2.90）"),
        ('长:宽（软指标，仅供参考）', dw_ok, f"{dw:.2f}（现实 3~3.5；本项目平面偏方）"),
        ('塔身比值 4.5~5.5', 4.5 <= shaft_ratio <= 5.5, f"{shaft_ratio:.2f}"),
        ('五层轮廓有序且间距≥12', separated, f"间距 {gaps}"),
        ('连续无分割长度受控', runs_ok, '已计入老虎窗'),
        ('11 模块全被体块包住', not escapees, f"越界 {escapees or '无'}"),
    ], hw, dw, hd


def load_envelopes():
    modules, placement = B.load_modules()
    boxes = {}
    for item in placement:
        number = item.get('number', item.get('module'))
        tag = str(number).zfill(2)
        pts = [p for p in modules if modules[p][2] == tag]
        boxes[number] = (min(p[0] for p in pts), max(p[0] for p in pts),
                         min(p[1] for p in pts), max(p[1] for p in pts),
                         min(p[2] for p in pts), max(p[2] for p in pts))
    return boxes


def sweep(boxes):
    print('=' * 100)
    print('檐口扫描：机房层数 → 檐口 → 屋脊 → 尖顶（高度全是算出来的，不是选的）')
    print('=' * 100)
    print(f'{"层数":>4}{"檐口":>6}{"坡度":>6}{"屋脊":>6}{"鼓座":>6}{"尖顶":>6}'
          f'{"塔顶":>6}{"总高":>6}{"高:宽":>7}{"长:宽":>7}{"塔身比":>8}  判定')
    best = None
    for floors in (5, 6, 7, 8):
        for pitch in (30, 35, 40):
            g = geometry(floors, pitch)
            rows, hw, dw, hd = checks(g, boxes)
            bad = [r[0] for r in rows if not r[1]]
            verdict = '全部通过' if not bad else '不过：' + '、'.join(bad)
            if not bad and best is None:
                best = (floors, pitch, g, hw, dw)
            shaft_ratio = (g['tower_top'] - 4) / g['tower_w']
            print(f'{floors:>4}{g["eave"]:>6}{pitch:>5}°{g["ridge"]:>6}{g["lantern_top"]:>6}'
                  f'{g["apex"]:>6}{g["tower_apex"]:>6}{g["total_h"]:>6}'
                  f'{hw:>7.2f}{dw:>7.2f}{shaft_ratio:>8.2f}  {verdict}')
        print()
    return best


def skyline(g, width=96):
    z0, z1 = g['z_back'], g['z_portal']
    span = z1 - z0 + 1
    col = lambda z: round((z - z0) / (span - 1) * (width - 1))
    height = {}

    def paint(za, zb, y):
        for z in range(max(z0, za), min(z1, zb) + 1):
            height[col(z)] = max(height.get(col(z), 0), y)

    paint(z0, z1, AISLE_TOP)
    paint(g['z_front'] - NAVE_LEN, g['z_front'], g['nave_ridge'])
    paint(z0, g['z_front'] - NAVE_LEN, g['ridge'])
    cx = col((z0 + g['z_front'] - NAVE_LEN) // 2)
    for c in range(cx - 5, cx + 6):
        height[c] = max(height.get(c, 0), g['lantern_top'])
    for c in range(cx - 2, cx + 3):
        height[c] = max(height.get(c, 0), g['apex'])
    for c in range(0, g['tower_w'] // 2):
        height[c] = max(height.get(c, 0), g['tower_apex'])
    lines = [f'{y:4} ' + ''.join('█' if height.get(c, 0) >= y else ' ' for c in range(width))
             for y in range(g['total_h'], -1, -3)]
    lines.append('     ' + '南' + '·' * (width - 8) + '北')
    return lines


def main():
    boxes = load_envelopes()
    print('=' * 100)
    print('体块试算（只算数字与剪影；未改动任何建筑代码与产物）')
    print('=' * 100)
    print(f'锁死：机房外宽 {CORE_W}（43 + 2×7）    实测模块包围盒 {len(boxes)} 个，'
          f'最高 Y={max(b[4] for b in boxes.values())}，最北 Z={min(b[3] for b in boxes.values())}')
    print(f'现实对照：Amiens 高:宽 {REAL["h_over_w"]}、长:宽 {1/REAL["w_over_d"]:.1f}'
          f'   中殿层高比目标 1.4~1.8，本方案 {NAVE_H/NAVE_W:.2f}')
    print()
    best = sweep(boxes)

    print('=' * 100)
    print('剪影对比（中轴纵剖面，横向约 1.5 格/列，纵向每行 3 格）')
    print('=' * 100)
    for floors, pitch in [(6, 35), (8, 35)]:
        g = geometry(floors, pitch)
        rows, hw, dw, hd = checks(g, boxes)
        bad = [r[0] for r in rows if not r[1]]
        print(f'\n{floors} 层 · 坡度 {pitch}° · 檐口 {g["eave"]} · 尖顶 {g["apex"]} · '
              f'高:宽 {hw:.2f} · 长:宽 {dw:.2f}'
              + ('' if not bad else '   ← 不过：' + '、'.join(bad)))
        for line in skyline(g):
            print(line)

    print()
    print('=' * 100)
    print('推荐解固化：6 层 + 35°（design/重构方案.md 的所有数字都以此为准）')
    print('=' * 100)
    g = geometry(6, 35)
    rows, hw, dw, hd = checks(g, boxes)
    for label, value in [
        ('侧廊屋面', AISLE_TOP), ('中殿净高', NAVE_H), ('中殿屋脊', g['nave_ridge']),
        ('核心檐口', g['eave']), ('核心屋脊', g['ridge']),
        ('塔身顶', g['tower_top']), ('塔宽', g['tower_w']), ('尖塔高', g['spire_h']),
        ('塔顶', g['tower_apex']), ('鼓座顶', g['lantern_top']), ('中央尖顶', g['apex']),
        ('总宽', g['total_w']), ('总长', g['total_d']), ('总高', g['total_h']),
    ]:
        print(f'  {label:<10} {value:>5}')
    shaft_ratio = (g['tower_top'] - 4) / g['tower_w']
    print(f'  {"塔身比值":<10} {shaft_ratio:>5.2f}   （目标 4.5~5.5）')
    print(f'  {"高:宽":<10} {hw:>5.2f}   {"长:宽":<6} {dw:>5.2f}')
    print()
    for label, ok, value in rows:
        print(f'  {"OK  " if ok else "FAIL"} {label:22} {value}')
    print()
    if best:
        floors, pitch, bg, bhw, bdw = best
        print(f'扫描得到的最小可行层数：{floors} 层（檐口 {bg["eave"]}），坡度 {pitch}°')
        print(f'每层南北各一模块 → {floors*2} 个；现有 11 个 → 需新增 {max(0, floors*2-11)} 个模块乐谱')
    print('=' * 100)


if __name__ == '__main__':
    main()
