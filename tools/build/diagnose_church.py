"""只读诊断：把生成的教堂外壳当体素模型量出来，用于建筑学批判。

不修改任何建筑、不写入任何产物，只在终端打印并在 build/music_hall/diagnose_church.txt 留档。
用法：python tools/build/diagnose_church.py
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_music_hall as B

CHAR = {
    'white_concrete': 'W', 'smooth_quartz': 'Q', 'light_blue_stained_glass': 'b',
    'purple_stained_glass': 'p', 'smooth_stone': 's', 'polished_andesite': 'a',
    'sea_lantern': 'L', 'dark_prismarine': 'D', 'amethyst_block': 'A',
    'spruce_stairs': 't', 'smooth_quartz_stairs': 'S', 'ladder': 'h',
    'stone': 'o', 'repeater': 'r', 'redstone_wire': '.', 'note_block': 'N',
    'dirt': 'd', 'packed_ice': 'i', 'oak_planks': 'w', 'blue_wool': 'B',
    'redstone_wall_torch': 'f', 'stone_button': 'u',
}


class Diagnose:
    def __init__(self):
        self.lines = []
        modules, placement = B.load_modules()
        shell = B.make_shell()
        self.modules = modules
        self.shell = shell
        self.blocks = {**modules, **shell}
        self.placement = placement

    def say(self, line=''):
        self.lines.append(line)
        print(line)

    def run(self):
        b = self.blocks
        xs = [p[0] for p in b]; ys = [p[1] for p in b]; zs = [p[2] for p in b]
        self.bounds = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
        x0, x1, y0, y1, z0, z1 = self.bounds
        self.say('=' * 76)
        self.say('教堂实例 · 建筑学实测（只读，未改动任何建筑）')
        self.say('=' * 76)
        self.say(f'包围盒  X {x0}..{x1} = {x1-x0+1}格 | Y {y0}..{y1} = {y1-y0+1}格 | Z {z0}..{z1} = {z1-z0+1}格')
        self.say(f'方块总数 {len(b)}（模块 {len(self.modules)} + 外壳 {len(self.shell)}）')
        self.height_map()
        self.skyline_side()
        self.skyline_front()
        self.cross_section()
        self.floor_plans()
        self.material_layers()
        self.interior_void()
        self.ratio_notes()
        return self.lines

    # ---------- 1. 列顶高度：识别体块与塔 ----------
    def height_map(self):
        x0, x1, y0, y1, z0, z1 = self.bounds
        top = {}
        for (x, y, z) in self.blocks:
            k = (x, z)
            if k not in top or y > top[k]:
                top[k] = y
        self.say()
        self.say('【1】列顶高度分布（有几列最高点是这个高度）')
        for y, n in sorted(Counter(top.values()).items(), reverse=True)[:14]:
            self.say(f'   Y={y:3}  {n:5} 列   {"█" * min(60, n // 20)}')

    # ---------- 2. 天际线：沿 Z 看东立面 ----------
    def skyline_side(self):
        x0, x1, y0, y1, z0, z1 = self.bounds
        top = defaultdict(lambda: -99)
        for (x, y, z) in self.blocks:
            if y > top[z]:
                top[z] = y
        self.say()
        self.say('【2】东立面轮廓（每列=Z的一个切面，取该切面最高方块；X 方向被压平）')
        for y in range(y1, y0 - 1, -1):
            self.say(f'{y:4} ' + ''.join('#' if top[z] >= y else ' ' for z in range(z0, z1 + 1)))
        self.say('     Z ' + ' ' * 4 + f'{z0} (南) 向右递增到 {z1} (北)')

    # ---------- 3. 天际线：沿 X 看南立面 ----------
    def skyline_front(self):
        x0, x1, y0, y1, z0, z1 = self.bounds
        top = defaultdict(lambda: -99)
        for (x, y, z) in self.blocks:
            if y > top[x]:
                top[x] = y
        self.say()
        self.say('【3】南立面/北立面轮廓（每列=X的一个切面，取最高方块）')
        for y in range(y1, y0 - 1, -1):
            self.say(f'{y:4} ' + ''.join('#' if top[x] >= y else ' ' for x in range(x0, x1 + 1)))
        self.say(f'     X {x0} 向左 <- 到 -> {x1} 向右')

    # ---------- 4. 主轴纵剖面 ----------
    def cross_section(self):
        x0, x1, y0, y1, z0, z1 = self.bounds
        axis = 21  # 教堂中轴
        self.say()
        self.say(f'【4】中轴纵剖面（X={axis} 处，Z 向右，Y 向上）')
        self.say('     空格=空气 / 字母=材质（见文末图例）')
        col = {}
        for (x, y, z), (name, _, _) in self.blocks.items():
            if x == axis:
                col[(y, z)] = name
        for y in range(y1, y0 - 1, -1):
            self.say(f'{y:4} ' + ''.join(CHAR.get(col.get((y, z), ''), '#') for z in range(z0, z1 + 1)))

    # ---------- 5. 分层平面 ----------
    def floor_plans(self):
        x0, x1, y0, y1, z0, z1 = self.bounds
        self.say()
        self.say('【5】水平切面（取该 Y 以下最高的方块材质；空格=该列完全无方块）')
        picks = [0, 24, 48, 69, 79, 91, 99]
        for want in picks:
            self.say()
            self.say(f'--- Y <= {want} 的平面（每格=1方块，X向右，Z向下）---')
            cut = {}
            for (x, y, z), (name, _, _) in self.blocks.items():
                if y <= want:
                    k = (x, z)
                    if k not in cut or y > cut[k][0]:
                        cut[k] = (y, name)
            header = '     ' + ''.join(str(x // 10 % 10) if x % 5 == 0 else ' ' for x in range(x0, x1 + 1))
            self.say(header)
            for z in range(z0, z1 + 1):
                row = ''.join(CHAR.get(cut[(x, z)][1], '#') if (x, z) in cut else ' ' for x in range(x0, x1 + 1))
                self.say(f'{z:4} {row}')

    # ---------- 6. 材质词频 ----------
    def material_layers(self):
        self.say()
        self.say('【6】材质用量（按数量排序，只用外壳）')
        counts = Counter(name for name, _, _ in self.shell.values())
        total = sum(counts.values())
        for name, n in counts.most_common():
            self.say(f'   {name:28} {n:6}  {100*n/total:5.1f}%')

    # ---------- 7. 内部空间 ----------
    def interior_void(self):
        x0, x1, y0, y1, z0, z1 = self.bounds
        self.say()
        self.say('【7】各层"封闭空腔"规模（该 Y 层被实体围住、可达面积很小的区域=实际可走的室内）')
        # 逐层做洪水填充：从包围盒外侧灌入，灌不到且非实体的格子=室内
        for y in range(0, 100, 6):
            solid = {(x, z) for (x, yy, z) in self.blocks if yy == y}
            if not solid:
                continue
            outside = set()
            stack = [(x0 - 1, z0), (x1 + 1, z0), (x0, z0 - 1), (x0, z1 + 1)]
            seen = set()
            while stack:
                p = stack.pop()
                if p in seen:
                    continue
                seen.add(p)
                if p in solid:
                    continue
                px, pz = p
                if not (x0 - 2 <= px <= x1 + 2 and z0 - 2 <= pz <= z1 + 2):
                    continue
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((px + d[0], pz + d[1]))
            inside = 0
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    if (x, z) not in solid and (x, z) not in seen:
                        inside += 1
            self.say(f'   Y={y:3}  实体 {len(solid):5} 格   室内空腔 {inside:5} 格')

    def ratio_notes(self):
        x0, x1, y0, y1, z0, z1 = self.bounds
        w = x1 - x0 + 1
        d = z1 - z0 + 1
        h = y1 - y0 + 1
        self.say()
        self.say('【8】关键比例（现实哥特教堂常见值作对照）')
        self.say(f'   总高/总宽 = {h}/{w} = {h/w:.2f}   现实大教堂中殿 高:宽 常在 2.5~3.5')
        self.say(f'   总长/总宽 = {d}/{w} = {d/w:.2f}   现实大教堂 长:宽 常在 3~5')
        self.say(f'   总高/总长 = {h}/{d} = {h/d:.2f}')
        core = 43
        self.say(f'   音乐机房净宽 {core} 格，占建筑总宽 {core/w*100:.0f}%')
        self.say()
        self.say('图例： W白混凝土 Q平滑石英 b淡蓝玻璃 p紫玻璃 s平滑石 a磨制安山岩')
        self.say('       L海晶灯 D暗海晶石 A紫水晶 S石英楼梯 t云杉楼梯 h梯子')
        self.say('       o石 r中继器 N音符盒 d泥土 i浮冰 w木板 B蓝羊毛 #其他')


if __name__ == '__main__':
    tool = Diagnose()
    lines = tool.run()
    target = Path(__file__).resolve().parents[2] / 'build' / 'music_hall' / 'diagnose_church.txt'
    target.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'\n已留档：{target}')
