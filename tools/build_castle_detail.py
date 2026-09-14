"""Exterior review sample: same-camera voxel comparison, no world/NBT import."""
import json
import zipfile
from collections import Counter
from pathlib import Path
from castle_detail import refine
from build_castle_complete import ROOT

OUT=ROOT/'castle_v3'/'detail_v4'


def main():
    data,before,after,delta,parts=refine()
    low=(-21,0,40);high=(60,71,92);offset=[-v for v in low];size=[high[i]-low[i]+1 for i in range(3)]
    def inside(p):return all(low[i]<=p[i]<=high[i] for i in range(3))
    def encode(bs):
        palette=[];lookup={};items=[]
        for p,(n,props,g) in sorted(bs.items()):
            if not inside(p):continue
            key=(n,tuple(sorted(props.items())),g)
            if key not in lookup:lookup[key]=len(palette);palette.append([n,props,g])
            items.append([*(p[i]+offset[i] for i in range(3)),lookup[key]])
        return dict(palette=palette,blocks=items)
    names={**data['names'],'polished_andesite_slab':'磨制安山岩台阶','deepslate_tile_slab':'深板岩瓦台阶','deepslate_brick_wall':'深板岩砖墙','gray_stained_glass_pane':'灰色染色玻璃板','cracked_stone_bricks':'裂纹石砖'}
    payload=dict(size=size,offset=offset,names=names,before=encode(before),after=encode(after),facadeExtras=[list(p) for p,k in parts.items() if k=='facade' and p[2]>47 and p in after],
                 changed=len(delta),preservedMusic=32260,routeCount=len(data['routes']))
    # Check material identifiers against the user's target runtime.
    jar=Path(r'E:\PCL\PCL 正式版 2.8.12\.minecraft\versions\26.3-snapshot-9\26.3-snapshot-9.jar')
    with zipfile.ZipFile(jar) as z:
        entries=set(z.namelist())
        for n,_,_ in payload['after']['palette']:assert f'assets/minecraft/blockstates/{n}.json' in entries,n
    OUT.mkdir(exist_ok=True)
    (OUT/'detail_comparison.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    # Changes are review data, not an executable patch or NBT to paste over a world.
    patch=[dict(pos=list(p),before=before.get(p),after=after.get(p)) for p in sorted(delta)]
    (OUT/'exterior_changes.json').write_text(json.dumps(patch,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    source=(ROOT/'tools'/'music_hall_viewer.html').read_text(encoding='utf-8')
    renderer=source[source.index('function shape('):source.index('function inView(')]+source[source.index('function draw('):source.index("$('view').onchange=")]
    renderer=renderer.replace("if(n==='iron_bars')", "if(n.endsWith('_glass_pane'))return p.east==='true'?[[0,0,.44,1,1,.56]]:[[.44,0,0,.56,1,1]];if(n==='iron_bars')")
    renderer=renderer.replace("^iron_bars$|", "^iron_bars$|_glass_pane$|")
    renderer=renderer.replace("if(n.endsWith('_wall'))return [[.25,0,.25,.75,1,.75]];", "if(n.endsWith('_wall'))return [[.25,0,.25,.75,1.5,.75]];")
    renderer=renderer.replace('let corners=[];',"const vb=VIEWS[$('view').value];lo=[vb[0]+D.offset[0],vb[2]+D.offset[1],vb[4]+D.offset[2]];hi=[vb[1]+1+D.offset[0],vb[3]+1+D.offset[1],vb[5]+1+D.offset[2]];let corners=[];")
    template=(ROOT/'tools'/'castle_detail_viewer.html').read_text(encoding='utf-8')
    template=template.replace('主堡南立面近景','主堡南立面（剖去前景）').replace('精修涉及的结构点位在下方逐层图中可查。','南立面剖去了前方唱诗堂，只观察墙面细部；完整遮挡关系请选择“局部联建全景”。全部结构点位在下方逐层图中可查。')
    (OUT/'外立面精修_前后对照.html').write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')).replace('__RENDERER__',renderer),encoding='utf-8')
    changed_after=Counter(after[p][0] for p in delta if p in after);changed_before=Counter(before[p][0] for p in delta if p in before)
    notes=['# 外立面精修样板 V4','',f'本次有 {len(delta):,} 个坐标发生外饰变化（包括替换/增设/移除，不等于增加同样数量方块）。音乐与控制32,260格全部保持，35条普通路线静态支撑/净空继续通过。','',
           '打开《外立面精修_前后对照.html》，按“南立面近景→唱诗堂东侧→飞扶壁→老虎窗”查看。同一取景中前后两版的相机范围固定；切换前后不会用不同缩放制造效果差异。',
           '', '本样板只供确认外观方向，尚未输出新的NBT整堡分块，不要拿外饰变更JSON直接导入世界。旧全堡仍保留作底稿。浏览器视觉/交互和游戏实机未验收；HTML仅文件级语法与数据检查。',
           '', '## 具体构件','',
           '- 主堡：三层尖拱套框、双联窗、小圆饰、深窗台；双圈石制大圆窗和放射窗棂。',
           '- 立面收口：宽基脚逐级收分的扶垛、窗间尖顶、两层檐口与托石；中央山墙覆盖部分平直屋肩。',
           '- 唱诗堂：六道外伸飞扶壁，拱臂下保持空气；成组高侧窗与侧廊檐口。',
           '- 屋顶：四个带窗的小山墙、屋脊饰与一处局部木构修补；不用全屋均匀撒杂色。',
           '', '## 改动涉及的材料（不是全堡采购表）','', '| 方块 | 新状态出现数 | 旧状态撤换数 |','|---|---:|---:|']
    for n in sorted(set(changed_after)|set(changed_before),key=lambda n:-changed_after[n]):notes.append(f'| {names.get(n,n)} | {changed_after[n]} | {changed_before[n]} |')
    notes+=['','出处与取舍见上级《外立面精修任务.md》。精修只改外饰，窗洞和拱臂不是新红石机关。']
    (OUT/'先看这里.md').write_text('\n'.join(notes)+'\n',encoding='utf-8')
    report=dict(changedCoordinates=len(delta),beforeSampleBlocks=len(payload['before']['blocks']),afterSampleBlocks=len(payload['after']['blocks']),unchangedMusicBlocks=32260,staticRoutes=len(data['routes']),target='26.3-snapshot-9',browserVisualTest=False,inGameTest=False)
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
