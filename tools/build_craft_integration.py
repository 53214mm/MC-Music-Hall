"""Publish the first V7 integrated pass without rewriting V6, source music or NBT."""
import hashlib
import json
from collections import Counter
from castle_craft_integration import ROOT, integrate_castle, zone_at
from castle_detail import read_model
from castle_finish import EMISSION
from build_craft_samples import NAMES as SAMPLE_NAMES
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/integration_v7'
NAMES={**SAMPLE_NAMES,'sandstone':'砂岩','cut_sandstone_slab':'切制砂岩台阶'}


def encode(blocks,offset):
    palette=[];lookup={};items=[]
    for p,(n,props,g) in sorted(blocks.items()):
        key=(n,tuple(sorted(props.items())),g)
        if key not in lookup:lookup[key]=len(palette);palette.append([n,props,g])
        items.append([*(p[i]+offset[i] for i in range(3)),lookup[key]])
    return dict(palette=palette,blocks=items)


def main():
    paths=[ROOT/'castle_v3/finish_v6/castle_v6.json',*sorted((ROOT/'nbt_save').glob('*.nbt'))]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    m=integrate_castle();before=m['before'];after=m['after'];assets=VanillaAssets();data=m['data']
    OUT.mkdir(exist_ok=True);names={**data['names'],**NAMES}
    lo=[min(p[i] for p in after) for i in range(3)];hi=[max(p[i] for p in after) for i in range(3)];offset=[-v for v in lo]
    delta=m['changed'];counts=Counter(s[0] for s in after.values());oldcounts=Counter(s[0] for s in before.values())
    states={(s[0],tuple(sorted(s[1].items()))) for s in after.values() if s[2] in ('shell','terrain')}
    colors={}
    for n,props in sorted(states):assets.elements(n,props);colors.setdefault(n,assets.swatch(n,props))
    report=dict(totalBlocks=len(after),changedCoordinates=len(delta),added=sum(p not in before for p in delta),removed=sum(p not in after for p in delta),replaced=sum(p in before and p in after for p in delta),
                size=[hi[i]-lo[i]+1 for i in range(3)],designMin=lo,designMax=hi,noteBlocks=counts['note_block'],musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in after.values()),
                lightBlocks=sum(counts[n] for n in EMISSION),routes=len(data['routes']),features=len(m['features']),zoneSurfaceReplacements=dict(m['zone_counts']),
                target='26.3-snapshot-9',dataVersion=5011,source='finish_v6/castle_v6.json',completedPlanSteps=[1,2],remainingPlanSteps=[3,4,5],newNBT=False,inGameTest=False,browserTest=False,
                modelStatesChecked=len(states),sourceHashes=hashes)
    def write(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    full=dict(**encode(after,offset),offset=offset,names=names,colors=colors,size=report['size'],routes=data['routes'],connections=data['connections'],fixtures=data['fixtures'],features=m['features'],report=report)
    write('castle_v7.json',full)
    _,roundtrip=read_model(OUT/'castle_v7.json');assert roundtrip==after,'serialized model mismatch'
    report['fullModelRoundtrip']=True
    write('v7_changes.json',[dict(pos=p,before=before.get(p),after=after.get(p)) for p in sorted(delta)])
    write('构件接入坐标.json',m['features'])
    # Only feature neighborhoods are embedded in the review page; the complete model is linked.
    selected={}
    for f in m['features']:
        r=f['region']
        for p,s in after.items():
            if all(r[2*i]-2<=p[i]<=r[2*i+1]+2 for i in range(3)):selected[p]=s
    payload=dict(**encode(selected,offset),offset=offset,names=names,colors=colors,features=m['features'],report=report)
    html=(ROOT/'tools/castle_integration_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
    (OUT/'余响堡_V7整堡接入对照.html').write_text(html,encoding='utf-8')
    lines=['# V7第一轮整堡接入：材料与范围','',f'本轮为5步计划中的第1、2步。共{len(after):,}个非空气方块；接入{len(m["features"])}组构件，相比V6变动{len(delta):,}个坐标。未生成NBT，不是最终采购清单。','',
           '## 材料分区','','| 区域 | 本轮外皮换材格数（不含后续窗洞几何变更） | 用法 |','|---|---:|---|']
    uses={'主堡':'灰石墙身，暖石窗框/扶垛饰面，深色屋顶；中央山墙局部红砖。','塔楼':'灰石塔身、暖石窗廊和檐口；保留各塔不同高度与冠部。','唱诗堂':'红砖填墙、暖石骨架和深灰瓦面；两个错开的变坡老虎窗。','生活翼':'方解石填墙、云杉木构；小窗帽局部铜绿。','南门楼':'保留厚重灰石体量，暖色切石强调门窗与上部檐口。'}
    lines += [f'| {zone} | {count:,} | {uses[zone]} |' for zone,count in m['zone_counts'].items()]
    lines +=['','## 已接入构件','','| 构件 | 设计范围 X / Y / Z | 本次改动格数 |','|---|---|---:|']
    for f in m['features']:
        r=f['region'];lines.append(f'| {f["name"]} | {r[0]}…{r[1]} / {r[2]}…{r[3]} / {r[4]}…{r[5]} | {f["changed"]} |')
    lines +=['','## 全模型现状及相比V6的差额','','这是材料名称汇总，不区分楼梯朝向等状态；状态在逐层图与JSON中。净变化不是手建操作数量，具体拆换以`v7_changes.json`为准。','', '| 材料 | V6 | 本轮V7 | 净变化 |','|---|---:|---:|---:|']
    for n in sorted(set(counts)|set(oldcounts),key=lambda n:-counts[n]):lines.append(f'| {names.get(n,n)} | {oldcounts[n]} | {counts[n]} | {counts[n]-oldcounts[n]:+} |')
    lines +=['','## 接着怎么做','','第3步：其余立面、塔楼、门洞、山墙和扶壁细节；第4步：照明协调与可建性复核；第5步：施工包、NBT与隔离创造档验收。内饰叙事及捷径机关另列一轮。','',
              '本轮保留V6的全部471个光源、灯具组件与支撑，不把光源数保持当作照明验收。所有音乐与控制方块、音乐保护体积、登记路线的路幅和三格净空保持。原NBT和真实存档没有改变。']
    (OUT/'材料分区与改动清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text('''# V7第一轮整堡接入

打开 `余响堡_V7整堡接入对照.html`。本轮完成材料分区和12处真实构件接入；尚有立面扩展、照明协调和施工验收3步，不是最终成品。

1. 先看南东、西南两个角度的V6/V7同尺度对照。都读取本机原版模型和纹理；不是游戏截图。远景只显示建筑和岩体，音乐/控制不单独绘出，不代表从模型中删除。
2. 再看窗跨、唱诗堂屋顶、生活翼近景。主堡窗跨按Z裁去唱诗堂前景，其他近景范围也明确裁切；不是建筑真正的切口。
3. 选择12个接入构件中的一个，查看其实际设计坐标与逐层状态。图中加2格邻接范围，不能把邻接范围外的空白理解成全堡空气。
4. `castle_v7.json`是包含音乐的完整接入模型；`v7_changes.json`是相对V6的精确差异；材料和各区用法见`材料分区与改动清单.md`。坐标不是服务器世界坐标。

与朋友分享时发送整个integration_v7文件夹，PNG不可遗漏。返回V6、试样和研究链接还需要父目录。离线查看无需Python或网页服务。

本轮无新NBT，未修改旧文件和真实存档。保护规则及路线经过静态检查；楼梯转角、栅栏/墙连接、活板门放置、光照、防跌落和音乐试听还需实机复核。不能直接把旧NBT当成这个新外观。

预览省略游戏光照、环境遮蔽、UV锁定、生物群系染色；动画纹理取首帧。网页仅做脚本与链接检查，未进行浏览器交互验收，也不绕过此前本地自动访问限制。
''',encoding='utf-8')
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))],p
    report['sourceHashesUnchanged']=True;write('validation.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
