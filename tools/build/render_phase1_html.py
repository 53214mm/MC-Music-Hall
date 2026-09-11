"""阶段 1 修订版 · 可旋转查看的 HTML 体块预览。

把体块数据内嵌进一个独立 HTML：鼠标拖拽旋转、滚轮缩放，无需联网、无需服务器。

只读建筑代码；输出 build/music_hall_phase1/体块预览.html。
用法：python tools/build/render_phase1_html.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase1_massing as P1

COLOR = {
    'white_concrete': '#e9eff1',
    'smooth_quartz': '#e1e6e5',
    'smooth_stone': '#a8b6bd',
    'polished_andesite': '#879ba8',
    'dark_prismarine': '#28635d',
    'light_blue_stained_glass': '#83bdcf',
    'purple_stained_glass': '#ae8cc5',
    'sea_lantern': '#e2ffff',
}

TEMPLATE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>阶段 1 体块 · 可旋转预览</title>
<style>
:root{font-family:system-ui,'Microsoft YaHei',sans-serif;color:#213745}
body{margin:0;background:#eef4f6;overflow:hidden}
canvas{display:block;width:100vw;height:100vh;cursor:grab}
canvas.drag{cursor:grabbing}
#hud{position:fixed;left:16px;top:16px;background:rgba(255,255,255,.92);padding:14px 18px;
     border-radius:10px;line-height:1.7;font-size:14px;box-shadow:0 2px 12px rgba(0,0,0,.08)}
#hud b{font-size:16px}
#hud small{color:#5a7280}
kbd{background:#e6edf1;border-radius:4px;padding:1px 5px;font-size:12px}
</style></head><body>
<canvas id="c"></canvas>
<div id="hud">
  <b>阶段 1 · 总体体块（修订版）</b><br>
  <small>拖拽旋转 · 滚轮缩放 · 双击复位</small><br>
  <small id="info"></small>
</div>
<script>
const DATA = __DATA__;
const COLORS = __COLORS__;
const canvas = document.getElementById('c'), ctx = canvas.getContext('2d');
let yaw = 35 * Math.PI / 180, pitch = 22 * Math.PI / 180, zoom = 1, dragging = false, lx = 0, ly = 0;

const blocks = DATA.blocks, palette = DATA.palette, size = DATA.size;
const keys = new Set(blocks.map(b => b[0] + ',' + b[1] + ',' + b[2]));

document.getElementById('info').textContent =
  `${size[0]}×${size[1]}×${size[2]} 格 · ${DATA.total} 个方块 · 无装饰纯体块`;

function project(x, y, z) {
  const cx = x - size[0] / 2, cy = y - size[1] / 2, cz = z - size[2] / 2;
  const x1 = cx * Math.cos(yaw) - cz * Math.sin(yaw);
  const z1 = cx * Math.sin(yaw) + cz * Math.cos(yaw);
  const y1 = cy * Math.cos(pitch) - z1 * Math.sin(pitch);
  const scale = Math.min(canvas.width, canvas.height) / Math.max(size[0], size[1], size[2]) * 1.7 * zoom;
  return [canvas.width / 2 + x1 * scale, canvas.height / 2 - y1 * scale, z1];
}

function draw() {
  const dpr = devicePixelRatio || 1;
  canvas.width = innerWidth * dpr; canvas.height = innerHeight * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#eef4f6'; ctx.fillRect(0, 0, innerWidth, innerHeight);

  const faces = [];
  for (const [x, y, z, pi] of blocks) {
    const colour = COLORS[palette[pi]] || '#b9c6cc';
    for (const [nx, ny, nz, shade] of DATA.normals) {
      if (keys.has((x + nx) + ',' + (y + ny) + ',' + (z + nz))) continue;
      const quad = DATA.quads[DATA.normals.findIndex(n => n[0] === nx && n[1] === ny && n[2] === nz)];
      const pts = quad.map(q => project(x + q[0], y + q[1], z + q[2]));
      const depth = pts.reduce((s, p) => s + p[2], 0) / 4;
      faces.push({ depth, pts, colour, shade });
    }
  }
  faces.sort((a, b) => b.depth - a.depth);
  for (const f of faces) {
    ctx.beginPath();
    f.pts.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]));
    ctx.closePath();
    ctx.fillStyle = f.colour;
    ctx.globalAlpha = f.shade;
    ctx.fill();
    ctx.globalAlpha = 1;
  }
}

canvas.addEventListener('mousedown', e => { dragging = true; lx = e.clientX; ly = e.clientY; canvas.classList.add('drag'); });
addEventListener('mouseup', () => { dragging = false; canvas.classList.remove('drag'); });
addEventListener('mousemove', e => {
  if (!dragging) return;
  yaw += (e.clientX - lx) * 0.008;
  pitch = Math.max(-1.4, Math.min(1.4, pitch + (e.clientY - ly) * 0.006));
  lx = e.clientX; ly = e.clientY; draw();
});
canvas.addEventListener('wheel', e => { e.preventDefault(); zoom = Math.max(0.3, Math.min(4, zoom * (e.deltaY > 0 ? 0.92 : 1.08))); draw(); }, { passive: false });
canvas.addEventListener('dblclick', () => { yaw = 35 * Math.PI / 180; pitch = 22 * Math.PI / 180; zoom = 1; draw(); });
addEventListener('resize', draw);
draw();
</script></body></html>
"""


def main():
    shell = P1.generate()
    xs = [p[0] for p in shell]; ys = [p[1] for p in shell]; zs = [p[2] for p in shell]
    ox, oy, oz = -min(xs), -min(ys), -min(zs)
    palette, index, blocks = [], {}, []
    for (x, y, z), (name, _, _) in sorted(shell.items()):
        if name not in index:
            index[name] = len(palette)
            palette.append(name)
        blocks.append([x + ox, y + oy, z + oz, index[name]])

    normals = [[0, 1, 0, 1.0], [1, 0, 0, 0.82], [0, 0, 1, 0.68], [-1, 0, 0, 0.72],
               [0, 0, -1, 0.58], [0, -1, 0, 0.45]]
    quads = [
        [[0, 1, 0], [1, 1, 0], [1, 1, 1], [0, 1, 1]],
        [[1, 0, 0], [1, 0, 1], [1, 1, 1], [1, 1, 0]],
        [[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]],
        [[0, 0, 0], [0, 0, 1], [0, 1, 1], [0, 1, 0]],
        [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
        [[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]],
    ]
    payload = {
        'size': [max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, max(zs) - min(zs) + 1],
        'total': len(shell), 'palette': palette, 'blocks': blocks,
        'normals': normals, 'quads': quads,
    }
    target = Path(__file__).resolve().parents[2] / 'build' / 'music_hall_phase1' / '体块预览.html'
    html = (TEMPLATE
            .replace('__DATA__', json.dumps(payload, separators=(',', ':')))
            .replace('__COLORS__', json.dumps({k: v for k, v in COLOR.items()})))
    target.write_text(html, encoding='utf-8')
    print(f'已生成 {target}（{target.stat().st_size // 1024} KB，{len(blocks)} 个方块）')


if __name__ == '__main__':
    main()
