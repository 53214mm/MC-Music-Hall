"""Publish V10 exterior geometry, preserving all previously delivered sources."""
import hashlib
import json
from collections import Counter
from castle_sculpt import sculpt_castle
from castle_detail import ROOT,read_model
from castle_finish import EMISSION
from build_craft_integration import encode
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/detail_v10'


def main():
    paths=[ROOT/f'castle_v3/{folder}/{name}' for folder,name in [('ground_v9','castle_v9.json'),('palette_v8','castle_v8.json'),('integration_v7','castle_v7.json'),('finish_v6','castle_v6.json')]]+sorted((ROOT/'nbt_save').glob('*.nbt'))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    m=sculpt_castle();a=m['after'];b=m['before'];data=m['data'];delta=m['changed'];assets=VanillaAssets()
    OUT.mkdir(exist_ok=True);names=data['names'];colors=dict(data['colors']);counts=Counter(s[0] for s in a.values());oldcounts=Counter(s[0] for s in b.values())
    states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in ('shell','terrain')}
    for n,props in sorted(states):assets.elements(n,props);colors[n]=assets.swatch(n,props)
    lo=[min(p[i] for p in a) for i in range(3)];hi=[max(p[i] for p in a) for i in range(3)];offset=[-v for v in lo]
    changed_solids=[a[p] for p in delta if p in a];partial=sum(s[0].endswith(('_stairs','_slab','_wall','_fence','_trapdoor')) for s in changed_solids)
    report=dict(version='V10',date='2026-09-13',source='ground_v9/castle_v9.json',scope='第3步：外围长墙、塔/北窗、长檐与山墙薄收边',totalBlocks=len(a),changedCoordinates=len(delta),
                added=len(set(a)-set(b)),removed=len(set(b)-set(a)),replaced=sum(p in a and p in b for p in delta),features=len(m['features']),featureFamilies=dict(Counter(f['family'] for f in m['features'])),
                changedNonAir=len(changed_solids),changedPartialBlocks=partial,partialRatioOfChangedNonAir=round(partial/len(changed_solids),4),deferredFeatures=m['deferred'],
                size=[hi[i]-lo[i]+1 for i in range(3)],designMin=lo,designMax=hi,noteBlocks=counts['note_block'],musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in a.values()),
                lightBlocks=sum(counts[n] for n in EMISSION),routes=len(data['routes']),target='26.3-snapshot-9',dataVersion=5011,modelStatesChecked=len(states),sourceHashes=hashes,
                currentPlanStep=3,completedPlanSteps=[1,2],remainingPlanSteps=[3,4,5],newNBT=False,inGameTest=False,browserTest=False)
    def write(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    full={**data,**encode(a,offset),'offset':offset,'size':report['size'],'names':names,'colors':colors,'report':report,
          'features':data['features']+m['features'],'featureProvenance':'First 12: integration_v7; next 46: detail_v10. Counts refer to their own construction pass.','deferredFeatures':m['deferred']}
    write('castle_v10.json',full)
    _,roundtrip=read_model(OUT/'castle_v10.json');assert roundtrip==a;report['fullModelRoundtrip']=True
    edits=[dict(pos=p,before=b.get(p),after=a.get(p)) for p in sorted(delta)]
    write('v10_changes.json',edits);write('构件定位与保留项.json',dict(features=m['features'],deferred=m['deferred']))
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))],p
    report['sourceHashesUnchanged']=True;write('validation.json',report)
    wanted=set()
    for f in m['features']:
        r=f['region'];wanted.update((x,y,z) for x in range(r[0]-2,r[1]+3) for y in range(r[2]-2,r[3]+3) for z in range(r[4]-2,r[5]+3))
    selected={p:a[p] for p in wanted if p in a}
    payload=dict(**encode(selected,offset),offset=offset,names=names,colors=colors,features=m['features'],report=report,changes=edits)
    html=(ROOT/'tools/castle_sculpt_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
    (OUT/'余响堡_V10外墙形状精修.html').write_text(html,encoding='utf-8')
    lines=['# V10 外墙形状精修：构件与材料','',f'在V9完整模型上精修{len(m["features"])}组构件；变动{len(delta):,}个坐标，新增{report["added"]:,}、移除{report["removed"]:,}、原位替换{report["replaced"]:,}。完整模型{len(a):,}格，范围{report["size"]}。',
           '',f'改动后非空气方块{len(changed_solids):,}格，其中{partial:,}格为楼梯、台阶、墙、栅栏或活板门，占{partial/len(changed_solids):.1%}。这是本轮改动中的比例，不是全堡异形方块比例。',
           '','## 构件怎么搭','','1. 长墙拱龛：先定位外墙方向，保留两层背墙；只拆最外层的凹龛格子。先做扶垛底脚，再叠墙状细柱，拱头用倒楼梯并补齐陡升的竖段；最后用上半台阶和间隔托石收口。拱龛不通向墙后。',
           '2. 塔窗/北窗：保留原玻璃和通路，按差异拆旧的两层外窗套；放窄砂岩墙立柱、倒楼梯拱头、薄窗台和细栅栏。保留项中的旧方块不能拆，北阶塔的灯链支撑以短石颈回接旧墙。',
           '3. 维修长廊檐口：按实际范围在墙头和原屋坡之间补四格外皮，百叶使用手动打开的云杉活板门；放上半砂岩台阶薄檐，间隔放倒楼梯托架。西侧北端不进入V7窗跨保护范围。',
           '4. 西翼山墙：沿既有屋坡的下缘铺上半台阶，外缘用倒楼梯，间隔加木托。薄收边回接原屋檐，不另加实心三角墙或第二片屋顶。',
           '','逐层图里橙色标记是本轮改动，点击同时看原状态和新状态；空气格可能代表需要拆除旧外饰。所有坐标为设计坐标，不是服务器世界坐标。','',
           '## 实际构件定位','','| 构件 | X / Y / Z 范围 | 操作格数 |','|---|---|---:|']
    for f in m['features']:
        r=f['region'];lines.append(f'| {f["name"]} | {r[0]}…{r[1]} / {r[2]}…{r[3]} / {r[4]}…{r[5]} | {f["changed"]} |')
    lines+=['','## 两组原窗保留，不是漏装','','缩窄和抬高窗框仍会触及真实路线或共用灯座，未把生成失败的半个构件留在模型里。','']
    for f in m['deferred']:lines.append(f'- {f["name"]}：{f["reason"]}')
    lines+=['','## 全模型材料现状与差额','','包含建筑、岩体与音乐；净变化不是操作量，也不是最终采购单。逐格拆换以v10_changes.json为准。','', '| 材料 | V9 | V10 | 净变化 |','|---|---:|---:|---:|']
    lines += [f'| {names.get(n,n)} | {oldcounts[n]:,} | {counts[n]:,} | {counts[n]-oldcounts[n]:+} |' for n in sorted(set(counts)|set(oldcounts),key=lambda n:-counts[n])]
    lines+=['','## 保持与待验','','全部地形和V9地表换材、音乐机和保护区、35条路线的路幅/支撑/三格净空、471个光源及灯具支撑、V7的12组构件及其范围内空气保持。V8材料家族继续沿用，局部外框允许随形状拆换，不把V8逐格颜色完全不变作为条件。',
            '','构件连接是方块格邻接与模型状态检查，不是游戏连接更新、碰撞或建筑力学认证。图片为本机原版模型/纹理渲染，省略游戏光照、AO、UV锁定与生物群系染色，动画取首帧；不是游戏截图。',
            '','仍处第3步，至少两处共用路线窗位须联合精修；照明协调、其余细节、完整施工包与NBT、隔离创造档验收未完成。没有修改旧模型、源NBT或真实存档。网页仅静态检查，未浏览器交互或游戏实机验收。']
    (OUT/'构件施工与材料清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text('''# V10 外墙形状精修

打开 `余响堡_V10外墙形状精修.html`。左右为V9/V10，同原版纹理和相机。先看两个整堡角度，再切换长墙拱龛、北阶塔窗、维修翼檐口与西翼山墙近景。

本轮实际46组：26段长墙拱龛/扶垛、16处塔窗或主堡北窗、2段维修翼长檐、2片西翼山墙薄收边。烽塔与维修塔的南向窗位与登塔路径/灯座共用，整组保留，另列待联合精修项。

页面下部可选择46组中的任一组查看逐层真实状态。每组额外显示2格邻接，超出范围不代表空气；橙色标记表示本轮修改，点格子看原→新状态。详细搭建顺序、坐标和材料在 `构件施工与材料清单.md`。

`castle_v10.json`是含音乐的完整模型，`v10_changes.json`是相对V9的精确差异。设计坐标不是服务器世界坐标，当前清单不是最终采购单。

分享时发送整个detail_v10文件夹，6张PNG不能遗漏。离线可看，无需Python或网页服务。回看V9链接需要同时保留ground_v9目录。

地形、V9地表、音乐、通路、既有灯具与V7构件保持，旧版和源NBT未改。连接只经过静态格邻接和原版模型检查；仍需游戏中的墙/栅栏连接更新、活板门方向、碰撞、照明和音乐验收。无新NBT，无游戏实测，未浏览器交互验收，不绕过本地自动访问限制。
''',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
