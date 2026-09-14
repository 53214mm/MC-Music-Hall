"""Publish V5 review data separately; never overwrite the V4 reference sample."""
import json
import zipfile
from collections import Counter
from castle_detail import ROOT
from castle_envelope import expand_envelope
from castle_sample import validate_route
from castle_front import route_cells

OUT=ROOT/'castle_v3'/'envelope_v5'


def main():
    m=expand_envelope();before=m['before'];after=m['after'];data=m['data']
    for r in data['routes']:
        ps=list(map(tuple,r['points']));assert not validate_route(after,ps),r['name']
        for p in route_cells(ps,r['width']):assert not validate_route(after,[p]),(r['name'],p)
    for p in m['v4_changes']:assert before.get(p)==after.get(p)
    for p,s in before.items():
        if s[2]=='control' or s[2].isdigit():assert after[p]==s
    low=[min(p[i] for p in set(before)|set(after)) for i in range(3)];high=[max(p[i] for p in set(before)|set(after)) for i in range(3)]
    offset=[-v for v in low];size=[high[i]-low[i]+1 for i in range(3)]
    def encode(bs):
        palette=[];lookup={};items=[]
        for p,(n,props,g) in sorted(bs.items()):
            key=(n,tuple(sorted(props.items())),g)
            if key not in lookup:lookup[key]=len(palette);palette.append([n,props,g])
            items.append([*(p[i]+offset[i] for i in range(3)),lookup[key]])
        return dict(palette=palette,blocks=items)
    before_compact=encode(before);after_compact=encode(after)
    names={**data['names'],'polished_andesite_slab':'磨制安山岩台阶','deepslate_tile_slab':'深板岩瓦台阶','deepslate_brick_wall':'深板岩砖墙','gray_stained_glass_pane':'灰色染色玻璃板','cracked_stone_bricks':'裂纹石砖'}
    payload=dict(size=size,offset=offset,names=names,before=before_compact,after=after_compact,features=m['features'],changed=len(m['changes']),routeCount=len(data['routes']),facadeExtras=[])
    palette_names={s[0] for s in after.values()}
    with zipfile.ZipFile(r'E:\PCL\PCL 正式版 2.8.12\.minecraft\versions\26.3-snapshot-9\26.3-snapshot-9.jar') as jar:
        valid=set(jar.namelist())
        for n in palette_names:assert f'assets/minecraft/blockstates/{n}.json' in valid,n
    OUT.mkdir(exist_ok=True)
    (OUT/'envelope_comparison.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    counts=Counter(s[0] for s in after.values())
    complete=dict(size=size,offset=offset,names=names,**after_compact,routes=data['routes'],connections=data['connections'],features=m['features'],report=dict(totalBlocks=len(after),designMin=low,designMax=high,materials=dict(counts),status='V5外饰扩展审阅稿，未生成新NBT，未游戏验收'))
    (OUT/'castle_v5.json').write_text(json.dumps(complete,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (OUT/'v5_changes.json').write_text(json.dumps([dict(pos=p,before=before.get(p),after=after.get(p)) for p in sorted(m['changes'])],ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    # Same-coordinate, same-camera renderer; coarse surfaces are still pure block data.
    source=(ROOT/'tools'/'music_hall_viewer.html').read_text(encoding='utf-8')
    renderer=source[source.index('function shape('):source.index('function inView(')]+source[source.index('function draw('):source.index("$('view').onchange=")]
    renderer=renderer.replace("if(n==='iron_bars')", "if(n.endsWith('_glass_pane'))return p.east==='true'?[[0,0,.44,1,1,.56]]:[[.44,0,0,.56,1,1]];if(n==='iron_bars')")
    renderer=renderer.replace("^iron_bars$|", "^iron_bars$|_glass_pane$|")
    renderer=renderer.replace("if(n.endsWith('_wall'))return [[.25,0,.25,.75,1,.75]];", "if(n.endsWith('_wall')){let out=[[.25,0,.25,.75,1.5,.75]];for(const[k,b]of Object.entries({north:[.3,0,0,.7,1.2,.5],south:[.3,0,.5,.7,1.2,1],east:[.5,0,.3,1,1.2,.7],west:[0,0,.3,.5,1.2,.7]}))if(p[k]&&p[k]!=='none')out.push(b);return out;}")
    renderer=renderer.replace("st[2]==='shell'||st[2]==='control'", "st[2]==='shell'||st[2]==='control'||st[2]==='terrain'")
    renderer=renderer.replace("if($('preview').hidden)return;","if($('preview').hidden||$('canvas').hidden)return;")
    renderer=renderer.replace('let corners=[];',"const vb=VIEWS[$('view').value];lo=[vb[0]+D.offset[0],vb[2]+D.offset[1],vb[4]+D.offset[2]];hi=[vb[1]+1+D.offset[0],vb[3]+1+D.offset[1],vb[5]+1+D.offset[2]];let corners=[];")
    template=(ROOT/'tools'/'castle_envelope_viewer.html').read_text(encoding='utf-8')
    (OUT/'余响堡_V5外壳扩展对照.html').write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')).replace('__RENDERER__',renderer),encoding='utf-8')
    building=Counter(s[0] for s in after.values() if s[2]=='shell');terrain=Counter(s[0] for s in after.values() if s[2]=='terrain');music=counts-building-terrain
    report=dict(totalBlocks=len(after),size=size,designMin=low,designMax=high,changedFromV4=len(m['changes']),v4CoordinatesPreserved=len(m['v4_changes']),musicBlocks=32260,noteBlocks=counts['note_block'],routes=35,target='26.3-snapshot-9',newNBT=False,inGameTest=False,browserTest=False)
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# V5 当前方块材料统计','',f'本版共{len(after):,}个非空气方块。它是外观审阅稿的现状统计，不是已定稿采购清单。','', '| 材料 | 建筑 | 岩体 | 音乐与控制 | 合计 |','|---|---:|---:|---:|---:|']
    for n,c in counts.most_common():lines.append(f'| {names.get(n,n)} | {building[n]} | {terrain[n]} | {music[n]} | {c} |')
    lines+=['','脚手架、工具、损耗、待补的6架捷径梯子另计。音符盒底材不得替换；尚未生存防刷怪及光照验收。']
    (OUT/'当前材料统计.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    notes=f'''# V5 外壳扩展对照

本次从V4继续，精修主堡东/西/北面、四座高塔和屋顶交接。**不是把南立面简单复制到四面**：南面保留圆窗；侧面改为窄长窗；冠塔采用顶部窗廊，烽塔仍为露天城垛。

- 主页面：`余响堡_V5外壳扩展对照.html`。先看静态整堡图，再按需开启可旋转预览。
- “上一版”已经包含V4南立面和唱诗堂；“本次扩展”只比较新增部分。同一取景下相机范围固定。
- 整体图不剖去前景建筑；侧墙特写按坐标裁切，不能把裁切边缘误认成建筑断面漏洞。
- 完整当前方块数据：`castle_v5.json`；差异：`v5_changes.json`；统计：`当前材料统计.md`。
- 改动{len(m['changes']):,}个坐标；V4的{len(m['v4_changes']):,}个改动坐标完整保留。全部32,260格音乐与控制、35条普通路线及旧门楼西翼实体保持。

本轮没有修改原音乐文件、V4样板或真实存档，**没有生成可覆盖世界的新版NBT**。先看整体细节，避免方向未定就重复导入和采购。精修内饰、全城照明/防刷怪、窗台/屋顶防跌落与游戏中完整试听仍未验收。

检验：原坐标/状态保留测试，整条路线及路幅/净空检查，目标版本方块ID核对，HTML脚本/文件检查；实际方块PNG另作人工查看。浏览器交互与Minecraft游戏内效果尚未验证。此前本地HTML浏览器访问被安全策略限制，本轮不以其他通道绕过。
'''
    (OUT/'先看这里.md').write_text(notes,encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
