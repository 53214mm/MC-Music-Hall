"""Export a merged front/west study; no game save is modified."""
import gzip
import json
from collections import Counter
from pathlib import Path
from castle_front import combined_model,route_cells
from castle_sample import validate_route
from build_music_hall import encode_structure
from build_castle_sample import NAMES

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'castle_v3'/'gate_west_combined'
TITLE='余响堡_门楼与西翼联建图'


def main():
    s=combined_model();blocks=s.pop('blocks')
    for r in s['routes']:
        assert not validate_route(blocks,r['points']),r['name']
        for p in route_cells(r['points'],r['width']):assert not validate_route(blocks,[p]),(r['name'],p)
    low=[min(p[i] for p in blocks) for i in range(3)];high=[max(p[i] for p in blocks) for i in range(3)]
    size=[high[i]-low[i]+1 for i in range(3)];offset=[-v for v in low]
    normalized={tuple(p[i]+offset[i] for i in range(3)):v for p,v in blocks.items()}
    palette=[];lookup={};data=[]
    for p,(name,props,group) in sorted(normalized.items()):
        group='terrain' if group=='terrain' else 'shell'
        key=(name,tuple(sorted(props.items())),group)
        if key not in lookup:lookup[key]=len(palette);palette.append([name,props,group])
        data.append([*p,lookup[key]])
    materials=dict(Counter(v[0] for v in blocks.values()))
    terrain=dict(Counter(v[0] for v in blocks.values() if v[2]=='terrain'))
    building=dict(Counter(v[0] for v in blocks.values() if v[2]!='terrain'))
    names=dict(NAMES,stone='石头',tuff='凝灰岩')
    report=dict(size=size,designMin=low,designMax=high,offset=offset,totalBlocks=len(blocks),materials=materials,terrainMaterials=terrain,buildingMaterials=building,routeCount=len(s['routes']),
                status='南门/岩岬/西翼合并施工样板，不是完整城堡；仅静态几何检查，未在游戏内实走。',integration=s['integration'])
    payload=dict(**s,size=size,offset=offset,palette=palette,blocks=data,report=report,names=names)
    OUT.mkdir(exist_ok=True)
    (OUT/'combined.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (OUT/'combined_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    old=(ROOT/'tools'/'music_hall_viewer.html').read_text(encoding='utf-8')
    renderer=old[old.index('function shape('):old.index('function inView(')]+old[old.index('function draw('):old.index("$('view').onchange=")]
    renderer=renderer.replace("if(n.endsWith('_wall'))return [[.25,0,.25,.75,1,.75]];", "if(n.endsWith('_wall')){const boxes=[[.25,0,.25,.75,1.5,.75]];for(const[k,box]of Object.entries({north:[.3,0,0,.7,1.2,.5],south:[.3,0,.5,.7,1.2,1],east:[.5,0,.3,1,1.2,.7],west:[0,0,.3,.5,1.2,.7]}))if(p[k]&&p[k]!=='none')boxes.push(box);return boxes;}")
    renderer=renderer.replace("st[2]==='shell'||st[2]==='control'","st[2]==='shell'||st[2]==='control'||st[2]==='terrain'")
    overlay="""
  if($('showRoute').checked){const r=D.routes[Number($('route').value)];ctx.beginPath();r.points.forEach((p,i)=>{const q=p.map((v,j)=>v+D.offset[j]);q[1]+=1.4;const uv=project(...q);i?ctx.lineTo(...uv):ctx.moveTo(...uv)});ctx.strokeStyle='#f7f2cb';ctx.lineWidth=5;ctx.stroke();ctx.strokeStyle='#b35432';ctx.lineWidth=2.2;ctx.stroke();}
"""
    cut=renderer.rfind('}');renderer=renderer[:cut]+overlay+renderer[cut:]
    template=(ROOT/'tools'/'castle_front_viewer.html').read_text(encoding='utf-8')
    (OUT/(TITLE+'.html')).write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')).replace('__RENDERER__',renderer),encoding='utf-8')
    print(f'HTML/model: {len(blocks)} blocks, size {size}. Exporting tiles...',flush=True)
    tile_dir=OUT/'structure_tiles';tile_dir.mkdir(exist_ok=True);tiles=[]
    for x0 in range(0,size[0],32):
        for y0 in range(0,size[1],32):
            for z0 in range(0,size[2],32):
                extent=[min(32,size[i]-v) for i,v in enumerate((x0,y0,z0))]
                tile={(x,y,z):normalized.get((x+x0,y+y0,z+z0),('air',{},'air')) for x in range(extent[0]) for y in range(extent[1]) for z in range(extent[2])}
                filename=f'front_{x0//32}_{y0//32}_{z0//32}.nbt'
                (tile_dir/filename).write_bytes(gzip.compress(encode_structure(tile,5011),mtime=0))
                tiles.append(dict(file=filename,offset=[x0,y0,z0],size=extent,solidBlocks=sum(v[0]!='air' for v in tile.values())))
    (OUT/'tile_manifest.json').write_text(json.dumps(tiles,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 门楼与西翼联建材料表','',f'只统计本联建单元：建筑 {sum(building.values()):,} 块、岩体表层 {sum(terrain.values()):,} 块，合计 {len(blocks):,} 块。不是全堡采购表。岩体可利用现成山崖，但需重新测量避让；若按图人工造山，必须计入右列。内部空腔不是游览路线。','','| 方块 | 建筑部分 | 岩体部分 | 合计 |','|---|---:|---:|---:|']
    lines += [f'| {names.get(n,n)} | {building.get(n,0)} | {terrain.get(n,0)} | {c} |' for n,c in sorted(materials.items(),key=lambda t:-t[1])]
    lines+=['','不含施工损耗、脚手架、工具和S2另补的6架梯子。材料统计把放置状态不同的同种方块合并；台阶和楼梯仍单独计数。']
    (OUT/'联建材料表.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    table='\n'.join(f'| `front_{m["offset"][0]//32}_{m["offset"][1]//32}_{m["offset"][2]//32}` | {", ".join(map(str,m["offset"]))} | {"×".join(map(str,m["size"]))} |' for m in tiles)
    guide=f'''# 门楼—岩岬—西翼：联建与测试

范围 **{size[0]}×{size[1]}×{size[2]}格**；城堡设计最小角 `{tuple(low)}`，最大角 `{tuple(high)}`。这是局部联建图，不含音乐核心及全堡侧翼。

## 导入安全与坐标

本目录{len(tiles)}个分块NBT **明确包含空气，会覆盖整个长方体范围**。只能在备份后的隔离创造测试区导入。不要与旧西翼分块叠加导入，不要覆盖已放置的音乐模块；本组合已经完整包含旧西翼。没有修改任何游戏存档。

- 若选择联建包最小角的世界位置为O：世界位置 = O + 联建施工坐标；分块世界最小角 = O + manifest.offset。
- 联建施工坐标 = 城堡设计坐标 + `{tuple(offset)}`。它与旧西翼施工坐标的零点不同。
- 若选择的是城堡设计原点C：分块世界最小角 = C + `{tuple(low)}` + manifest.offset。O=C+designMin。
- 玩家脚底通常在所列地板块的Y上方1格；下半台阶和楼梯边缘不能简化为固定眼睛高度。

## 创造档加载

沿用你已成功导入module_01的结构文件目录规则，另建命名空间`departures_front`，复制本目录`structure_tiles`内的NBT。

结构名称示例：`departures_front:front_0_0_0`，不加`.nbt`。旋转0°、不镜像、完整性1.0、不含实体。每块目标最小角为上述公式；若结构方块就在目标正下方一格，相对位置填(0,1,0)，否则按目标−结构方块位置计算。不得把文件名或JSON归一化offset误作世界坐标。

| 名称（前加 departures_front:） | 相对联建最小角偏移X,Y,Z | 尺寸 |
|---|---|---|
{table}

有些分块主要用于清空空气，完整测试仍需覆盖；禁止将其随意加载到已有建筑上。

## 手建与试走顺序

1. 原点确定后先建桥台、拱桥和道路，岩体材料单独核算；现成地形只能局部替用，桥下裂隙和通道不能被填死。
2. 主路从设计(-18,-28,178)出发，经五格宽坡道、拱桥到(-43,-12,102)门厅，折转登上前庭(-38,0,74)。
3. 从门厅进入东塔，依次到8、28、42层；8层巡廊跨过门厅，向西塔绕回前庭。先铺所有平台和楼梯，再装墙体、栏杆和屋面。
4. 西翼按原有顺序施工；此联建图保存其所有已交付实体状态，只移除了新加且会挡旧路线的方块。
5. S1、S2仍为手动样板，见网页说明。抬起的城门栅栏只是固定造景，不带红石开关。

## 验收边界

已静态核查普通路线的支撑、连续高差、台阶方向、三格净高、三或五格路宽及新旧交界；不是完整Minecraft物理模拟。仍需实测楼梯更新形状、栏杆、防跌落、刷怪与光照，尤其是东塔顶层和西侧返回台阶。未承诺所有窗台/屋顶均能安全站立。
'''
    (OUT/'联建测试说明.md').write_text(guide,encoding='utf-8')
    print(f'Finished: {len(tiles)} tiles, {len(s["routes"])} routes; building {sum(building.values())}, terrain {sum(terrain.values())}.',flush=True)


if __name__=='__main__':main()
