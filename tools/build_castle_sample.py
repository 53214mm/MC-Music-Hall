"""Export the west-wing sample with exact block counts and small NBT tiles."""
import gzip
import json
from collections import Counter
from pathlib import Path
from castle_sample import build_sample,validate_route
from build_music_hall import encode_structure

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'castle_v3'/'west_wing_sample'
NAMES={'stone_bricks':'石砖','mossy_stone_bricks':'苔石砖','andesite':'安山岩','polished_andesite':'磨制安山岩','stone_brick_wall':'石砖墙','stone_brick_stairs':'石砖楼梯','chiseled_stone_bricks':'錾制石砖','spruce_planks':'云杉木板','spruce_log':'云杉原木','spruce_slab':'云杉木台阶','spruce_stairs':'云杉木楼梯','bookshelf':'书架','barrel':'木桶','iron_bars':'铁栏杆','lantern':'灯笼','ladder':'梯子','deepslate_brick_slab':'深板岩砖台阶','deepslate_tile_stairs':'深板岩瓦楼梯','deepslate_tiles':'深板岩瓦'}


def main():
    s=build_sample();blocks=s.pop('blocks')
    for r in s['routes']:
        errors=validate_route(blocks,r['points'])
        if errors:raise ValueError((r['name'],errors))
    low=[min(p[i] for p in blocks) for i in range(3)]
    high=[max(p[i] for p in blocks) for i in range(3)]
    size=[high[i]-low[i]+1 for i in range(3)]
    offset=[-v for v in low]
    normalized={tuple(p[i]+offset[i] for i in range(3)):v for p,v in blocks.items()}
    palette=[];lookup={};data=[]
    for p,(name,props,_) in sorted(normalized.items()):
        key=(name,tuple(sorted(props.items())))
        if key not in lookup:lookup[key]=len(palette);palette.append([name,props,'shell'])
        data.append([*p,lookup[key]])
    materials=dict(Counter(v[0] for v in blocks.values()))
    report=dict(size=size,designMin=low,designMax=high,offset=offset,totalBlocks=len(blocks),materials=materials,routeCount=len(s['routes']),
                status='西翼样板；静态三格净高与三格路幅检查通过，尚未在Minecraft实走。不是完整城堡，也不含音乐机。')
    payload=dict(**s,size=size,offset=offset,palette=palette,blocks=data,report=report,names=NAMES)
    OUT.mkdir(exist_ok=True)
    (OUT/'sample.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (OUT/'sample_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    old=(ROOT/'tools'/'music_hall_viewer.html').read_text(encoding='utf-8')
    renderer=old[old.index('function shape('):old.index('function inView(')]+old[old.index('function draw('):old.index("$('view').onchange=")]
    renderer=renderer.replace("if(n.endsWith('_wall'))return [[.25,0,.25,.75,1,.75]];", "if(n.endsWith('_wall')){const boxes=[[.25,0,.25,.75,1.5,.75]];for(const[k,box]of Object.entries({north:[.3,0,0,.7,1.2,.5],south:[.3,0,.5,.7,1.2,1],east:[.5,0,.3,1,1.2,.7],west:[0,0,.3,.5,1.2,.7]}))if(p[k]&&p[k]!=='none')boxes.push(box);return boxes;}")
    template=(ROOT/'tools'/'castle_sample_viewer.html').read_text(encoding='utf-8')
    html=template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')).replace('__RENDERER__',renderer)
    (OUT/'西翼回廊_逐格样板.html').write_text(html,encoding='utf-8')
    tiles=[];tile_dir=OUT/'structure_tiles';tile_dir.mkdir(exist_ok=True)
    # Explicit air is intentional: a test import must preserve the designed voids.
    for x0 in range(0,size[0],32):
        for y0 in range(0,size[1],32):
            for z0 in range(0,size[2],32):
                extent=[min(32,size[i]-v) for i,v in enumerate((x0,y0,z0))]
                tile={}
                for x in range(extent[0]):
                    for y in range(extent[1]):
                        for z in range(extent[2]):tile[x,y,z]=normalized.get((x+x0,y+y0,z+z0),('air',{},'air'))
                filename=f'west_{x0//32}_{y0//32}_{z0//32}.nbt'
                (tile_dir/filename).write_bytes(gzip.compress(encode_structure(tile,5011),mtime=0))
                tiles.append(dict(file=filename,offset=[x0,y0,z0],size=extent,solidBlocks=sum(v[0]!='air' for v in tile.values())))
    (OUT/'tile_manifest.json').write_text(json.dumps(tiles,ensure_ascii=False,indent=2),encoding='utf-8')
    table='\n'.join(f'| {NAMES.get(n,n)} | {c} | {c//64}组+{c%64} |' for n,c in sorted(materials.items(),key=lambda t:-t[1]))
    (OUT/'样板材料表.md').write_text(f'# 西翼样板材料表\n\n仅本样板，不是全城堡。共{len(blocks):,}个非空气方块，范围{size[0]}×{size[1]}×{size[2]}格。不含施工脚手架、损耗、六架待补捷径梯子。书架、木桶按放置方块计，不含存放物品。\n\n| 材料 | 数量 | 64一组 |\n|---|---:|---:|\n{table}\n',encoding='utf-8')
    tile_table='\n'.join(f'| `{m["file"][:-4]}` | {", ".join(map(str,m["offset"]))} | {"×".join(map(str,m["size"]))} |' for m in tiles)
    guide=f'''# 西翼样板：创造档测试与手建

本样板是余响堡的一个施工单元，不含音乐机。先在单机创造测试，暂不建议直接手建到朋友的正式服务器。

## 范围与起点

尺寸 **{size[0]}×{size[1]}×{size[2]}格**，{len(blocks):,}个非空气方块。设计范围从 `{tuple(low)}` 到 `{tuple(high)}`。

城堡设计坐标可以为负；样板施工坐标从0开始：

`样板施工坐标 = 城堡设计坐标 + {tuple(offset)}`

选一个空白区域的最小角作为世界起点O：`世界坐标 = O + 样板施工坐标`。不要把样板起点直接当成全堡设计原点。

## 分块导入

**这些NBT明确包含空气，会清除覆盖范围内原有方块。只用空白创造测试区，先备份世界。** 本轮没有替你修改游戏存档。

1. 使用你之前成功导入module_01的结构文件目录规则，另建命名空间 `departures_castle`，把 `structure_tiles` 内的24个NBT复制进去。保留旧音乐模块的文件。
2. 结构名称写 `departures_castle:west_0_0_0` 这样的完整名字，不加`.nbt`，不要让游戏自动补成 `minecraft:`。
3. 每块的目标最小角为 `O + 下表偏移`。如果结构方块放在该目标的正下方一格，相对位置就用(0,1,0)。若放在别处，则相对位置=目标最小角−结构方块世界坐标。
4. 旋转0°，不镜像，完整性1.0，不含实体。按你已成功的加载方式预览边界，再执行加载。分块每轴不超过32。
5. 下表包括部分主要用于挖空的分块，不要只导入有大量实体的块。完整导入后检查连接处与梯子，再游览。

| 结构名（前加 departures_castle:） | 偏移 X,Y,Z | 尺寸 |
|---|---|---|
{tile_table}

## 从哪里开始走

前庭地板的设计坐标是(-38,0,74)，对应样板施工坐标{tuple([-38+offset[0],offset[1],74+offset[2]])}。玩家脚底应比地板块Y高1格。

依次走前庭→西阶→藏谱下厅→东阶→上廊；返回后走井旁回廊→蓄水池→前庭。网页“游览与测试”页列出了全部路线起终点。

S1测试时人工拆9个铁栏杆：X=-32…-30，Y=1…3，Z=60。S2人工补6架梯子：X=-46，Y=17…22，Z=2，梯子贴西侧木板、面朝东。它们只是手动捷径样板，尚无单向门闩或自动放梯电路。

## 手建顺序

1. 先定位样板最小角，参照逐层图做井底、蓄水池、基础和支撑。
2. 做地面回廊；井口和下行楼梯上方必须留空，不要把整个地坪铺满。
3. 做西阶与Y=16的悬桥/藏谱下厅，再做Y=32的上廊。先确认路线，再装栏杆。
4. 加书架、桌椅、灯、门廊、圆窗及偏置抄谱间，最后封屋顶。
5. 按网页逐格信息核对楼梯facing与half、台阶type、原木axis。材料表统计的是放置结果，楼梯/墙/台阶不能全部替成整块。

## 已检查与未检查

已检查：普通路线三格宽度与三格净高、相邻台阶方向、缺支撑检测、原音乐保护范围避让、24块NBT逐格回读与空气覆盖、目标26.3-snapshot-9方块ID。

尚未检查：游戏内实际走动、自动方块状态更新、亮度/刷怪、防跌落、S2爬梯、完整城堡与音乐核心对接。只有所列路线通过静态检查，不代表所有屋顶和窗台均可安全行走。
'''
    (OUT/'创造档测试说明.md').write_text(guide,encoding='utf-8')
    print(f'Sample: {len(blocks)} blocks, size {size}, {len(tiles)} air-inclusive tiles, {len(s["routes"])} checked routes.')


if __name__=='__main__':main()
