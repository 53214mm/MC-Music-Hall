"""立面分格：把体块数字落成"开间 / 扶壁 / 窗"的可整除网格，并检查窗宽是否合规。

这一层的价值在于：开间除不尽会在施工中途才发现，而且改起来要动整面墙。
只读，不改建筑。用法：python tools/build/plan_facade_rhythm.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plan_massing as P

# 室内竖向三段（哥特标准剖面）：拱廊 / 三层拱廊(triforium) / 高侧窗
NAVE_H = P.NAVE_H               # 44
AISLE_TOP = 18                  # 实测系数：中殿净高 × 0.42
CLERESTORY_SILL_MIN = AISLE_TOP + 2      # 高侧窗底必须在侧廊屋面之上 2 格
TRIFORIUM_H = 9                 # 服务性楼层，4~10 格即可

WINDOW_W_MAX = 5                # 窗宽上限（超过就成玻璃幕墙）
MIN_PIER = 1                    # 相邻窗之间至少留 1 格（该格即扶壁/壁柱）
BAY_CANDIDATES = [4, 5, 6, 7, 8]


def interior_levels():
    """把中殿净高切成三段的可行方案（拱廊尽量占大头，符合真实比例）。"""
    results = []
    for arcade in range(14, 30):
        triforium_top = arcade + TRIFORIUM_H
        if triforium_top >= NAVE_H:
            continue
        if arcade < CLERESTORY_SILL_MIN:
            continue
        clerestory = NAVE_H - triforium_top
        if not (8 <= clerestory <= 16):
            continue
        results.append({
            'arcade': arcade,
            'triforium': (arcade, triforium_top),
            'clerestory': (triforium_top, NAVE_H),
            'clerestory_h': clerestory,
        })
    return results


def fit_bays(length, bays_wanted):
    """给定总长，找出能整除的开间宽度。"""
    out = []
    for bay in BAY_CANDIDATES:
        if length % bay == 0:
            out.append((bay, length // bay))
    return out


def window_layout(bay, window_w):
    """一个开间里放一扇窗，两侧留墩。返回 (墩宽, 窗宽) 或 None。"""
    pier = bay - window_w
    if pier < 0:
        return None
    return pier, window_w


def main():
    print('=' * 86)
    print('立面分格与开间（数字来自 plan_massing，改动前先在这里对齐）')
    print('=' * 86)

    print()
    print('【一】中殿室内竖向三段：拱廊 / triforium / 高侧窗')
    print(f'  中殿净高 {NAVE_H}；侧廊屋面 {AISLE_TOP}；拱廊底 0')
    rows = interior_levels()
    print(f'  {"拱廊":>10}{"triforium":>14}{"高侧窗":>14}{"窗高":>6}  判定')
    for r in rows:
        arcade = r['arcade']
        tf = r['triforium']
        cl = r['clerestory']
        window_h = r['clerestory_h']
        ok = 8 <= window_h <= 12
        print(f'  {f"0..{arcade}":>10}{f"{tf[0]}..{tf[1]}":>14}'
              f'{f"{cl[0]}..{cl[1]}":>14}{window_h:>6}'
              f'  {"可用" if ok else "窗偏高，建议缩 triforium"}')

    print()
    print('【二】各立面的开间能否整除')
    surfaces = [
        ('中殿侧立面（长）', P.NAVE_LEN, '窗'),
        ('侧廊外立面（长）', P.NAVE_LEN, '窗'),
        ('核心东/西立面（长）', P.CORE_Z1 - P.CORE_Z0 + 1, '窗'),
        ('核心南/北立面（宽）', P.CORE_W, '盲拱窗'),
        ('塔楼各立面', 19, '窗'),
    ]
    for name, length, kind in surfaces:
        fits = fit_bays(length, None)
        if fits:
            text = '、'.join(f'{b} 格开间 × {n} 间' for b, n in fits)
        else:
            text = f'4~8 格开间都无法整除 {length} 格 → 需要留一段非标准端间'
        print(f'  {name:<20} 长 {length:>3} 格：{text}')

    print()
    print(f'【三】一个开间里的窗宽是否合规（窗宽 ≤{WINDOW_W_MAX}，两侧各留 ≥{MIN_PIER} 格做扶壁/壁柱）')
    print(f'  {"开间":>6}{"窗宽":>6}{"两侧各留":>10}  判定')
    for bay in BAY_CANDIDATES:
        for window_w in (3, 4, 5):
            if window_w > WINDOW_W_MAX:
                continue
            pier = bay - window_w
            if pier < 2 * MIN_PIER:
                continue
            per_side = pier / 2
            print(f'  {bay:>6}{window_w:>6}{per_side:>10.1f}  可用')

    print()
    print('【四】推荐分格（全部由上面的整除结果推出，不硬编码）')
    plan = [
        ('中殿侧立面', P.NAVE_LEN, [(4, 3), (6, 4)]),
        ('侧廊外立面', P.NAVE_LEN, [(4, 3)]),
        ('核心东/西立面', P.CORE_Z1 - P.CORE_Z0 + 1, [(6, 4), (4, 3)]),
        ('核心南/北立面', P.CORE_W, [(6, 4), (5, 3)]),
        ('塔楼各立面', 19, [(5, 3), (6, 4)]),
    ]
    for name, length, prefs in plan:
        # 选优顺序：能整除优先 → 端间余数小优先 → 开间更接近 6 格优先
        options = []
        for bay, win in prefs:
            n = length // bay
            rest = length % bay
            if n >= 2 and bay - win >= 2 * MIN_PIER:
                options.append((rest, abs(bay - 6), bay, win, n))
        if options:
            rest, _, bay, win, n = min(options)
            note = '' if rest == 0 else f'，余 {rest} 格并入端间（端间做加宽处理）'
            print(f'  {name:<16} {length:>3} 格：{bay} 格开间 × {n} 间'
                  f'（窗宽 {win}，两侧各留 {(bay-win)//2} 格）{note}')
        else:
            print(f'  {name:<16} {length:>3} 格：候选开间都不合适，需要专门设计')


if __name__ == '__main__':
    main()
