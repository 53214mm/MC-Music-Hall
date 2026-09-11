"""阶段 1 验收预览图：把阶段 1 体块渲染成 PNG，便于直接查看对比。

渲染方法：正交投影 + 可见面剔除（只画朝向相机的面），按面法线做明暗，
颜色取材质本色。不做游戏内光照模拟，只用于判断体块与轮廓。

只读建筑代码；输出 build/music_hall_phase1/预览图.png。
用法：python tools/build/render_phase1_preview.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_music_hall as B
import phase1_massing as P1

COLOR = {
    'white_concrete': (233, 239, 241),
    'smooth_quartz': (225, 230, 229),
    'smooth_stone': (168, 182, 189),
    'polished_andesite': (135, 155, 168),
    'dark_prismarine': (40, 99, 93),
    'light_blue_stained_glass': (131, 189, 207),
    'purple_stained_glass': (174, 140, 197),
    'sea_lantern': (226, 255, 255),
}
SHADE = {  # 各朝向面的明暗系数
    (0, 0, 1): 1.00, (1, 0, 0): 0.78, (0, 1, 0): 0.92,
    (-1, 0, 0): 0.66, (0, 0, -1): 0.55, (0, -1, 0): 0.45,
}


def rotate(point, degrees):
    x, y, z = point
    a = np.radians(degrees)
    c, s = np.cos(a), np.sin(a)
    return (x * c - z * s, y, x * s + z * c)


def render(blocks, angle_deg, size=(1500, 900), background=(238, 244, 246)):
    keys = set(blocks)
    rotated = {}
    for p, (name, _, _) in blocks.items():
        rotated[p] = (rotate(p, angle_deg), name)

    pts = [rp for rp, _ in rotated.values()]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    scale = min(size[0] * 0.86 / max(1, max(xs) - min(xs)),
                size[1] * 0.86 / max(1, (max(ys) - min(ys)) * 1.05))
    ox, oy = size[0] / 2, size[1] * 0.965
    ybase = min(ys)

    def project(p):
        return (ox + (p[0] - cx) * scale, oy - (p[1] - ybase) * scale * 0.92 - (p[2] - cz) * scale * 0.42)

    image = Image.new('RGB', size, background)
    draw = ImageDraw.Draw(image, 'RGBA')

    # 只画朝向相机的三个面；按深度排序，远的先画
    faces = []
    for p, (rp, name) in rotated.items():
        x, y, z = p
        for normal in ((0, 0, 1), (1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, 0, -1)):
            neighbour = (x + normal[0], y + normal[1], z + normal[2])
            if neighbour in keys:
                continue
            if rotate(normal, angle_deg)[2] <= 0.05:      # 背向相机的面
                continue
            corners = []
            for dx, dy, dz in ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1),
                               (0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)):
                corners.append((x + dx, y + dy, z + dz))
            if normal == (0, 1, 0):
                quad = [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)]
            elif normal == (1, 0, 0):
                quad = [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)]
            elif normal == (-1, 0, 0):
                quad = [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]
            elif normal == (0, 0, 1):
                quad = [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
            else:
                quad = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
            screen = [project(rotate((x + a, y + b, z + c), angle_deg)) for a, b, c in quad]
            # 深度用旋转后的相机坐标（旋转空间里 z 轴即观察方向）
            centre = rotate((x + 0.5, y + 0.5, z + 0.5), angle_deg)
            depth = centre[2]
            base = COLOR.get(name, (200, 200, 200))
            k = SHADE.get(normal, 0.8)
            faces.append((depth, screen, tuple(min(255, int(v * k)) for v in base)))
    faces.sort(key=lambda f: f[0])
    for _, screen, colour in faces:
        draw.polygon(screen, fill=colour)

    return image


def main():
    blocks = P1.generate()
    target = Path(__file__).resolve().parents[2] / 'build' / 'music_hall_phase1'
    target.mkdir(parents=True, exist_ok=True)

    views = [('预览图_东南向.png', 225), ('预览图_西南向.png', 135)]
    for name, angle in views:
        print(f'渲染 {name}（视角 {angle}°）…', flush=True)
        render(blocks, angle).save(target / name)
        print(f'  已保存 {(target / name).stat().st_size // 1024} KB')
    print(f'\n预览图目录：{target}')


if __name__ == '__main__':
    main()
