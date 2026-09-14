import argparse
import gzip
import json
import struct
import webbrowser
from collections import Counter
from pathlib import Path


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NBT 结构逐层施工图</title>
<style>
  :root { color-scheme: light dark; font-family: system-ui, "Microsoft YaHei", sans-serif; }
  body { margin: 0; background: #f7f8fa; color: #1f2328; }
  main { max-width: 1500px; margin: auto; padding: 24px; }
  h1 { margin: 0 0 8px; font-size: 24px; }
  .muted { color: #667085; }
  .toolbar { display: flex; gap: 12px; align-items: center; margin: 18px 0 12px; flex-wrap: wrap; }
  button { border: 1px solid #d0d5dd; border-radius: 9px; padding: 8px 14px; background: #fff; color: inherit; cursor: pointer; }
  button:disabled { opacity: .45; cursor: default; }
  input[type=range] { flex: 1; min-width: 220px; }
  .selected { margin: 12px 0; padding: 12px 14px; border: 1px solid #d0d5dd; border-radius: 10px; background: #fff; }
  .scroll { overflow-x: auto; padding-bottom: 8px; }
  .grid { display: grid; gap: 3px; width: max-content; min-width: 100%; }
  .cell, .axis { box-sizing: border-box; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; font-size: 13px; }
  .axis { color: #667085; }
  .cell { padding: 0; border: 1px solid #e1e4e8; border-radius: 9px; background: #fff; }
  .cell.note { background: #fff0c7; }
  .cell.signal { background: #ffe2d9; }
  .cell.support { background: #f9ddeb; }
  .cell.access { background: #dff4ef; }
  .cell.empty { color: #98a2b3; }
  .cell.active { outline: 3px solid #2684ff; outline-offset: -3px; }
  .legend, .materials { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 12px; font-size: 13px; }
  .swatch { width: 12px; height: 12px; border-radius: 3px; display: inline-block; margin-right: 5px; vertical-align: -1px; }
  .swatch.note { background: #f5c75b; } .swatch.signal { background: #ef8d72; }
  .swatch.support { background: #dc8fb6; } .swatch.access { background: #69bda9; }
  @media (prefers-color-scheme: dark) {
    body { background: #101317; color: #edf0f3; }
    .muted, .axis { color: #aab2bd; }
    button, .selected, .cell { background: #191e24; border-color: #38414c; }
    .cell.note { background: #59471b; } .cell.signal { background: #5b2d25; }
    .cell.support { background: #572d43; } .cell.access { background: #214b42; }
  }
</style>
</head>
<body>
<main>
  <h1 id="title"></h1>
  <div class="muted" id="meta"></div>
  <div class="materials muted" id="materials"></div>
  <div class="selected" id="selected">点击格子查看方块信息</div>
  <div class="toolbar">
    <button id="prev" type="button">上一层</button>
    <label for="layer">高度层 Y：<strong id="layerValue">0</strong></label>
    <input id="layer" type="range" min="0" value="0" step="1">
    <button id="next" type="button">下一层</button>
  </div>
  <div class="muted">俯视：X 向右 →，Z 向下 ↓；Y=0 是最底层</div>
  <div class="scroll"><div class="grid" id="grid" role="grid"></div></div>
  <div class="legend">
    <span><i class="swatch note"></i>音符盒 N音高</span>
    <span><i class="swatch signal"></i>红石 R档位+朝向</span>
    <span><i class="swatch support"></i>承托方块</span>
    <span><i class="swatch access"></i>梯子/告示牌</span>
    <span>· 空气</span>
  </div>
</main>
<script>
const data = __STRUCTURE_DATA__;
const [sizeX, sizeY, sizeZ] = data.size;
const map = new Map(data.blocks.map(b => [b.p.join(','), b]));
const names = {
  stone:'石头', repeater:'红石中继器', redstone_wire:'红石粉', note_block:'音符盒', dirt:'泥土',
  ladder:'梯子', redstone_wall_torch:'红石火把', oak_planks:'橡木木板', blue_wool:'蓝色羊毛',
  packed_ice:'浮冰', oak_wall_sign:'橡木墙上告示牌', stone_button:'石按钮'
};
const short = {stone:'石',redstone_wire:'线',dirt:'土',ladder:'梯',redstone_wall_torch:'炬',oak_planks:'木',blue_wool:'蓝',packed_ice:'冰',oak_wall_sign:'牌',stone_button:'钮'};
const arrows = {north:'↑',south:'↓',east:'→',west:'←',up:'↑',down:'↓'};
const grid = document.getElementById('grid');
const selected = document.getElementById('selected');
const layerInput = document.getElementById('layer');
const layerValue = document.getElementById('layerValue');
let layer = 0;

function kind(name) {
  if (name === 'note_block') return 'note';
  if (['repeater','redstone_wire','redstone_wall_torch','stone_button'].includes(name)) return 'signal';
  if (['ladder','oak_wall_sign'].includes(name)) return 'access';
  return 'support';
}
function label(b) {
  if (!b) return '·';
  if (b.n === 'note_block') return `N${b.q.note ?? '?'}`;
  if (b.n === 'repeater') return `R${b.q.delay ?? '?'}${arrows[{north:'south',south:'north',east:'west',west:'east'}[b.q.facing]] ?? ''}`;
  if (['redstone_wall_torch','ladder','oak_wall_sign','stone_button'].includes(b.n)) return `${short[b.n]}${arrows[b.q.facing] ?? ''}`;
  return short[b.n] ?? b.n.slice(0, 2);
}
function details(b,x,y,z) {
  if (!b) return `坐标 X=${x}, Y=${y}, Z=${z} · 空气`;
  const props = Object.entries(b.q).map(([k,v]) => `${k}=${v}`).join('，');
  return `坐标 X=${x}, Y=${y}, Z=${z} · ${names[b.n] ?? b.n}${props ? ` · ${props}` : ''}`;
}
function render() {
  layerValue.textContent = layer;
  layerInput.value = layer;
  document.getElementById('prev').disabled = layer === 0;
  document.getElementById('next').disabled = layer === sizeY - 1;
  grid.style.gridTemplateColumns = `repeat(${sizeX + 1}, 42px)`;
  grid.replaceChildren();
  const corner = document.createElement('div'); corner.className='axis'; corner.textContent='Z\\X'; grid.appendChild(corner);
  for (let x=0;x<sizeX;x++) { const e=document.createElement('div');e.className='axis';e.textContent=x;grid.appendChild(e); }
  let count=0;
  for (let z=0;z<sizeZ;z++) {
    const a=document.createElement('div');a.className='axis';a.textContent=z;grid.appendChild(a);
    for (let x=0;x<sizeX;x++) {
      const b=map.get(`${x},${layer},${z}`); if (b) count++;
      const e=document.createElement('button');e.type='button';e.className=`cell ${b ? kind(b.n) : 'empty'}`;e.textContent=label(b);
      const text=details(b,x,layer,z);e.setAttribute('aria-label',text);
      e.addEventListener('click',()=>{grid.querySelectorAll('.active').forEach(n=>n.classList.remove('active'));e.classList.add('active');selected.textContent=text;});
      grid.appendChild(e);
    }
  }
  document.getElementById('meta').textContent=`尺寸 ${sizeX}×${sizeY}×${sizeZ} · 当前 Y=${layer} · 本层 ${count} 个方块`;
  selected.textContent=`当前 Y=${layer}；点击格子查看坐标、方块状态和朝向`;
}
document.getElementById('title').textContent=`${data.name} 逐层施工图`;
document.getElementById('materials').textContent='材料总表：'+Object.entries(data.counts).map(([n,c])=>`${names[n] ?? n} ×${c}`).join(' · ');
layerInput.max=sizeY-1;
layerInput.addEventListener('input',e=>{layer=Number(e.target.value);render();});
document.getElementById('prev').addEventListener('click',()=>{layer=Math.max(0,layer-1);render();});
document.getElementById('next').addEventListener('click',()=>{layer=Math.min(sizeY-1,layer+1);render();});
render();
</script>
</body>
</html>
'''


class NBTReader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def take(self, size: int) -> bytes:
        chunk = self.data[self.offset:self.offset + size]
        if len(chunk) != size:
            raise ValueError("Unexpected end of NBT data")
        self.offset += size
        return chunk

    def unpack(self, fmt: str):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.take(size))[0]

    def string(self) -> str:
        length = self.unpack(">H")
        start = self.offset
        raw = self.take(length)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(
                f"Invalid UTF-8 NBT string at byte {start}, length {length}: {raw[:32]!r}"
            ) from error

    def payload(self, tag_type: int):
        if tag_type == 1:
            return self.unpack(">b")
        if tag_type == 2:
            return self.unpack(">h")
        if tag_type == 3:
            return self.unpack(">i")
        if tag_type == 4:
            return self.unpack(">q")
        if tag_type == 5:
            return self.unpack(">f")
        if tag_type == 6:
            return self.unpack(">d")
        if tag_type == 7:
            return list(self.take(self.unpack(">i")))
        if tag_type == 8:
            return self.string()
        if tag_type == 9:
            item_type = self.unpack(">B")
            length = self.unpack(">i")
            return [self.payload(item_type) for _ in range(length)]
        if tag_type == 10:
            value = {}
            while True:
                child_type = self.unpack(">B")
                if child_type == 0:
                    return value
                child_name = self.string()
                value[child_name] = self.payload(child_type)
        if tag_type == 11:
            return [self.unpack(">i") for _ in range(self.unpack(">i"))]
        if tag_type == 12:
            return [self.unpack(">q") for _ in range(self.unpack(">i"))]
        raise ValueError(f"Unsupported NBT tag type: {tag_type}")

    def root(self):
        tag_type = self.unpack(">B")
        if tag_type == 0:
            return {}
        self.string()
        return self.payload(tag_type)


def read_nbt(path: Path):
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return NBTReader(raw).root()


def clean_name(name: str) -> str:
    return name.removeprefix("minecraft:")


def structure_payload(path: Path):
    root = read_nbt(path)
    if not all(key in root for key in ("palette", "blocks", "size")):
        raise ValueError("This NBT file is not a Java Edition structure file")

    palette = root["palette"]
    blocks = []
    counts = Counter()
    for entry in root["blocks"]:
        state = palette[entry["state"]]
        name = clean_name(state["Name"])
        if name in {"air", "cave_air", "void_air"}:
            continue
        props = state.get("Properties", {})
        pos = entry["pos"]
        blocks.append({"p": pos, "n": name, "q": props})
        counts[name] += 1

    return {
        "name": path.stem,
        "size": [max(root["size"][axis], max((b["p"][axis] + 1 for b in blocks), default=0)) for axis in range(3)],
        "declaredSize": root["size"],
        "blocks": blocks,
        "counts": dict(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))),
        "dataVersion": root.get("DataVersion"),
    }


def write_html(payload, output: Path):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")
    output.write_text(HTML_TEMPLATE.replace("__STRUCTURE_DATA__", data), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Convert a Minecraft Java structure NBT into JSON or a layer-by-layer HTML viewer")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?", help="Output .json or .html; defaults to *_viewer.html")
    parser.add_argument("--html", action="store_true", help="Write a standalone interactive HTML viewer")
    parser.add_argument("--open", action="store_true", dest="open_browser", help="Open the generated HTML in the default browser")
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.is_file():
        parser.error(f"NBT file not found: {input_path}")

    output = args.output
    if output is None:
        output = input_path.with_name(f"{input_path.stem}_viewer.html")
    else:
        output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    payload = structure_payload(input_path)
    make_html = args.html or output.suffix.lower() in {".html", ".htm"}
    if make_html:
        write_html(payload, output)
    else:
        output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"Created: {output}")
    if args.open_browser:
        if not make_html:
            parser.error("--open can only be used with HTML output")
        webbrowser.open(output.as_uri())


if __name__ == "__main__":
    main()
