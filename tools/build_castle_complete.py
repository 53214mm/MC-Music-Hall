"""Generate the separate full-castle construction package; never touch game saves."""
import gzip
import json
from pathlib import Path
from collections import Counter,defaultdict
from castle_complete import complete_model
from castle_front import route_cells
from castle_sample import validate_route
from build_music_hall import encode_structure
from build_castle_sample import NAMES as STONE_NAMES
from hall_material_names import NAMES as MUSIC_NAMES

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'castle_v3'/'full_castle'
TITLE='余响堡_V3全堡施工图'


def main():
    model=complete_model();blocks=model['blocks']
    for r in model['routes']:
        errors=validate_route(blocks,r['points'])
        for p in route_cells(r['points'],r['width']):errors+=validate_route(blocks,[p])
        assert not errors,(r['name'],errors[:8])
    for p,v in model['originalMusic'].items():assert blocks[p[0],p[1]-32,p[2]]==v
    assert sum(v[0]=='note_block' for v in blocks.values())==2307
    low=[min(p[i] for p in blocks) for i in range(3)];high=[max(p[i] for p in blocks) for i in range(3)]
    offset=[-v for v in low];size=[high[i]-low[i]+1 for i in range(3)]
    normalized={tuple(p[i]+offset[i] for i in range(3)):v for p,v in blocks.items()}
    palette=[];lookup={};data=[];groups=defaultdict(Counter)
    for p,(n,props,g) in sorted(normalized.items()):
        g='shell' if g=='sample' else g
        key=(n,tuple(sorted(props.items())),g)
        if key not in lookup:lookup[key]=len(palette);palette.append([n,props,g])
        data.append([*p,lookup[key]]);groups[g][n]+=1
    materials=Counter(v[0] for v in blocks.values());machine=Counter()
    for g,c in groups.items():
        if g.isdigit() or g=='control':machine.update(c)
    names={**MUSIC_NAMES,**STONE_NAMES,'tuff':'凝灰岩','stone_brick_slab':'石砖台阶'}
    report=dict(size=size,offset=offset,designMin=low,designMax=high,totalBlocks=len(blocks),noteBlocks=materials['note_block'],
                materials=dict(materials),buildingMaterials=dict(groups['shell']),terrainMaterials=dict(groups['terrain']),musicMaterials=dict(machine),
                byGroup={g:dict(c) for g,c in groups.items()},routeCount=len(model['routes']),integration=model['integration'],signal=model['signal'],
                status='V3全堡逐格数据；静态验收不等于游戏验收。S1/S2为手动捷径，所有装饰均不附带剧情书本或自动机关。')
    payload={k:v for k,v in model.items() if k not in ('blocks','originalMusic','previousBlocks')}
    payload.update(size=size,offset=offset,palette=palette,blocks=data,report=report,names=names)
    OUT.mkdir(parents=True,exist_ok=True)
    packed=json.dumps(payload,ensure_ascii=False,separators=(',',':'))
    (OUT/'castle.json').write_text(packed,encoding='utf-8')
    for name,obj in [('build_report',report),('connection_report',model['connections'])]:
        (OUT/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    old=(ROOT/'tools'/'music_hall_viewer.html').read_text(encoding='utf-8')
    renderer=old[old.index('function shape('):old.index('function inView(')]+old[old.index('function draw('):old.index("$('view').onchange=")]
    renderer=renderer.replace("if(n.endsWith('_wall'))return [[.25,0,.25,.75,1,.75]];","if(n.endsWith('_wall')){const a=[[.25,0,.25,.75,1.5,.75]];for(const[k,b]of Object.entries({north:[.3,0,0,.7,1.2,.5],south:[.3,0,.5,.7,1.2,1],east:[.5,0,.3,1,1.2,.7],west:[0,0,.3,.5,1.2,.7]}))if(p[k]&&p[k]!=='none')a.push(b);return a;}")
    renderer=renderer.replace("st[2]==='shell'||st[2]==='control'","st[2]==='shell'||st[2]==='control'||st[2]==='terrain'")
    overlay="""if($('showRoute').checked){ctx.beginPath();D.routes[+$('route').value].points.forEach((p,i)=>{const q=p.map((v,j)=>v+D.offset[j]);q[1]+=1.4;const v=project(...q);i?ctx.lineTo(...v):ctx.moveTo(...v)});ctx.strokeStyle='#fff3b5';ctx.lineWidth=4;ctx.stroke();ctx.strokeStyle='#bb5738';ctx.lineWidth=2;ctx.stroke();}"""
    ix=renderer.rfind('}');renderer=renderer[:ix]+overlay+renderer[ix:]
    template=(ROOT/'tools'/'castle_complete_viewer.html').read_text(encoding='utf-8')
    (OUT/(TITLE+'.html')).write_text(template.replace('__DATA__',packed.replace('</','<\\/')).replace('__RENDERER__',renderer),encoding='utf-8')
    print(f'Model ready: {len(blocks):,} blocks, {size}, {len(model["routes"])} routes.',flush=True)
    tile_dir=OUT/'structure_tiles';tile_dir.mkdir(exist_ok=True);manifest=[]
    for x0 in range(0,size[0],32):
        for y0 in range(0,size[1],32):
            for z0 in range(0,size[2],32):
                origin=[x0,y0,z0];extent=[min(32,size[i]-origin[i]) for i in range(3)]
                tile={(x,y,z):normalized.get((x+x0,y+y0,z+z0),('air',{},'air')) for x in range(extent[0]) for y in range(extent[1]) for z in range(extent[2])}
                name=f'castle_{x0//32}_{y0//32}_{z0//32}.nbt'
                (tile_dir/name).write_bytes(gzip.compress(encode_structure(tile,5011),mtime=0))
                manifest.append(dict(file=name,offset=origin,size=extent,solidBlocks=sum(v[0]!='air' for v in tile.values())))
        print(f'NBT column X={x0}: {len(manifest)} tiles exported.',flush=True)
    (OUT/'tile_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 余响堡 V3 全堡材料','',f'完整图纸实体合计 **{len(blocks):,}**。建筑 {sum(groups["shell"].values()):,}；岩体表层 {sum(groups["terrain"].values()):,}；音乐机与连接 {sum(machine.values()):,}（含2307音符盒）。',
           '', '| 材料 | 建筑 | 岩体 | 音乐机与连接 | 总计 | 64格/组换算 |','|---|---:|---:|---:|---:|---|']
    for n,c in materials.most_common():lines.append(f'| {names.get(n,n)} `{n}` | {groups["shell"][n]} | {groups["terrain"][n]} | {machine[n]} | {c} | {c//64}组+{c%64} |')
    lines+=['','不含脚手架、工具、施工损耗、S2另补的6架梯子。现成山体不必按表造山，但必须保持音乐内堡、蓄水池、桥洞与步行净空。所有桶/书架为空，木床只是造景。',
            '音符盒下方材质决定乐器，不能为了外观统一替换。表内计数按方块数量，不是原料合成成本。保留源NBT和署名资料；原模块内的11块生成器告示牌没有复制。']
    (OUT/'全堡材料表.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    write_guide(report,model,manifest)
    print(f'Complete package: {len(manifest)} tiles.',flush=True)


def write_guide(r,m,tiles):
    s=r['size'];low=r['designMin'];offset=r['offset']
    lines=['# 余响堡 V3：施工、连接与创造档验收','',f'本版整合全堡及11段音乐机。尺寸 **{s[0]}×{s[1]}×{s[2]}**，设计坐标最小角 `{tuple(low)}`、最大角 `{tuple(r["designMax"])}`。共 {len(tiles)} 个分块。',
           '', '## 先分清三套坐标','',
           f'- 图纸设计坐标有负数；全堡施工坐标 = 设计坐标 + `{tuple(offset)}`。',
           '- 选全堡最小角的世界位置为 O：世界坐标 = O + 全堡施工坐标。每个NBT最小角 = O + tile_manifest.offset。',
           f'- 选城堡设计原点的世界位置为 C：世界坐标 = C + 设计坐标；此时 O = C + `{tuple(low)}`。',
           '- 不沿用 V2 的归一化偏移，也不沿用西翼或门楼局部包的起点。所有结构旋转0°、无镜像；若旋转城堡必须整体转换方向和坐标。',
           '- 本表路线Y是脚下方块的Y，站立脚底一般为Y+1。请先核对世界高度下限/上限，使整个全堡Y范围都在可建范围内。',
           '', '## 施工顺序','',
           '1. 在独立创造档放样，标出主堡、门塔、桥台和三条关键标高：前庭0、唱诗堂16、试听台-3。',
           '2. 先铺基础、道路、各层地板和所有楼梯，完整走通主路、两个返回环路和高塔支路。岩体是表层壳，不是实心山。',
           '3. 建门楼、西翼、低矮生活翼与唱诗堂；再建音乐机。音符盒顶上留空气，乐器底块严格照图，不往红石线旁加装饰。',
           '4. 依次核对01—11，逐条完成连接。打开网页“模块连接”，选择01→02等，按输入线、80个蛇形计时中继器、跨模块线的顺序施工。',
           '5. 先在音乐周边无遮盖时试听通过，再加厚石主堡、深色屋面和局部水晶采光。最后做北塔、冠塔、外墙和家具。',
           '6. 灯笼点位只是构图照明，尚未做生存防刷怪覆盖。创造测试后再补照明、危险边缘与施工设施，补灯不得靠近线路。',
           '', '## 原音乐完全保留，怎么启动','',
           '- 整机及原控制线仅下移32格。主按钮设计位置 **(23,-23,-3)**；中央试听台地板 **(21,-3,4)**。',
           '- 正常20游戏刻/秒时，01—10的音乐零点间隔320红石刻=32秒；10→11电路总延迟322红石刻，用来补偿11段内部启动差。不要将最后一条强行改成320。',
           '- 播放期间不要再次按启动键。朋友可负责原按钮启动，听众提前站好；本版未新增远程启动或自动复位。原按钮的生存维护接近方式需单独验收，不宣称所有测试按钮都属于游览步行路线。',
           '- 中继器格标注 R档位+输出箭头；新放后右击“档位-1”次。音符格 N数字表示新音符盒右击次数，点击可看乐器和下方材料。',
           '- 原01按钮保留。02—11的正面位置是输入中继器，侧面另有测试按钮；不要把中继器拆回按钮。',
           '', '| 模块 | 地基设计Y | 方向 | 原输入位置（01按钮，其余中继器） | 测试按钮 |','|---|---:|---|---|---|']
    for p in m['placement']:lines.append(f'| {p["module"]:02} | {p["baseY"]} | {"北/180°" if p["north"] else "南/0°"} | {p["originalInputPosition"]} | {p["testButton"]} |')
    lines+=['','## NBT测试安全','',f'{len(tiles)}个NBT明确包含空气，会清空整个尺寸范围。只导入备份后的空白创造测试区；不要直接覆盖朋友的服务器、旧V2音乐馆或门楼/西翼分块。本版已含它们，应从空白测试区整体加载。没有向游戏存档写入任何内容。',
            '沿用你已成功加载module_01的当前版本结构文件目录规则，另外使用命名空间 `departures_castle`；把 `structure_tiles` 内NBT复制进去。结构名例如 `departures_castle:castle_0_0_0`，不加后缀。完整性1.0，不包含实体。',
            '结构方块若放在该分块目标最小角正下方，相对位置(0,1,0)。否则相对位置=目标最小角−结构方块位置。每个分块位置分别查表，不以“前一块旁边”估计。',
            '', '| NBT名称（前加 departures_castle:） | 相对全堡最小角偏移 | 尺寸 |','|---|---|---|']
    for t in tiles:lines.append(f'| `{Path(t["file"]).stem}` | {t["offset"]} | {t["size"]} |')
    lines+=['','## 实机验收清单','',
            '- 普通步行路线不依赖飞行/跳跃；检测是整数支撑和三格净高，并不模拟所有楼梯自动形状、墙体碰撞或边缘跌落。实机逐条试走。',
            '- S1：人工拆 X=-32…-30、Y=1…3、Z=60 的9个铁栏杆，形成前庭便门。',
            '- S2：人工补 X=-46、Y=17…22、Z=2 的6架梯子，面朝东、背靠西侧木板。不是自动放梯机关。',
            '- 先分别试听模块，再连播全曲；确认无串音、重触发、缺音、节奏接缝。网页模型无法代替服务端方块更新和音频验收。',
            '- 主按钮和各层测试按钮属于维护区；维护梯井要另查头顶、出入口和防跌落。',
            '- 全堡照明、防刷怪、屋面防跌落尚未实测；只承诺图中列出的静态通路，不承诺每个窗台和所有屋面可走。',
            '- 本轮HTML只做脚本/数据检查。此前自动浏览器本地URL被安全策略阻止，没有绕过该限制；请手动打开检查交互。']
    (OUT/'施工与验收指南.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':main()
