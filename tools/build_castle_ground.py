"""Deliver a full V9 model and bounded ground-skin review without changing V8."""
import hashlib
import json
from collections import Counter
from build_craft_integration import encode
from castle_detail import ROOT,read_model
from castle_ground import recolor_ground
from castle_finish import EMISSION
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/ground_v9'
ZONES=[('露天铺地','平滑砂岩 / 同形楼梯','主入口坡道与露天前庭提亮，长路保留灰色横缝。范围限登记路线Y≤0及西前庭Y=0铺地，不延伸至室内或高架游廊。'),
       ('墙根暖石','切制砂岩 / 平滑砂岩','低部墙根两格邻域内的小范围暖石收边，让暖色墙体自然落地；冻结灯座和陡坎保留。'),
       ('道路土肩','泥坯 / 砂土','与道路高差不超过3格的近路地表使用黄褐色，路面和自然地面之间有缓和的色差。'),
       ('自然地表','泥坯 / 砂土 / 凝灰岩 / 苔石 / 苔藓块','连片的裸土、岩石和少量苔色，不做均匀散点；陡坎边缘和深裂隙仍保留裸岩。')]


def main():
    paths=[ROOT/f'castle_v3/{folder}/{name}' for folder,name in [('palette_v8','castle_v8.json'),('integration_v7','castle_v7.json'),('finish_v6','castle_v6.json')]]+sorted((ROOT/'nbt_save').glob('*.nbt'))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    m=recolor_ground();data=m['data'];a=m['after'];b=m['before'];delta=m['changed'];assets=VanillaAssets()
    OUT.mkdir(exist_ok=True)
    names={**data['names'],'coarse_dirt':'砂土','packed_mud':'泥坯','moss_block':'苔藓块','mossy_cobblestone':'苔石','tuff':'凝灰岩'}
    colors=dict(data['colors']);states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in ('shell','terrain')}
    for n,props in sorted(states):assets.elements(n,props);colors[n]=assets.swatch(n,props)
    counts=Counter(s[0] for s in a.values());oldcounts=Counter(s[0] for s in b.values());swaps=Counter((b[p][0],a[p][0]) for p in delta)
    assert a.keys()==b.keys() and all(a[p][1:]==s[1:] for p,s in b.items())
    assert all(p[1]==m['top'][p[0],p[2]] for p in delta)
    report=dict(version='V9',date='2026-09-13',source='palette_v8/castle_v8.json',scope='地基露天地表单层换材',totalBlocks=len(a),changedCoordinates=len(delta),
                terrainSurfaceChanges=sum(b[p][2]=='terrain' for p in delta),pavingChanges=sum(b[p][2]=='shell' for p in delta),zones=dict(m['zones']),added=0,removed=0,
                sameCoordinates=True,sameProperties=True,oneTopCellPerColumn=True,subsurfaceUnchanged=True,size=data['size'],offset=data['offset'],
                noteBlocks=counts['note_block'],musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in a.values()),lightBlocks=sum(counts[n] for n in EMISSION),routes=len(data['routes']),
                target='26.3-snapshot-9',dataVersion=5011,modelStatesChecked=len(states),sourceHashes=hashes,newNBT=False,inGameTest=False,browserTest=False,
                currentPlanStep=3,remainingPlanSteps=[3,4,5])
    def write(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    full={**data,**encode(a,data['offset']),'names':names,'colors':colors,'report':report}
    write('castle_v9.json',full)
    _,roundtrip=read_model(OUT/'castle_v9.json');assert roundtrip==a
    report['fullModelRoundtrip']=True
    write('v9_changes.json',[dict(pos=p,zone=m['labels'][p],before=b[p],after=a[p]) for p in sorted(delta)])
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))],p
    report['sourceHashesUnchanged']=True;write('validation.json',report)
    payload=dict(report=report,names=names,colors=colors,zones=[dict(name=n,materials=mat,note=t,count=m['zones'][n]) for n,mat,t in ZONES],
                 swaps=[dict(before=n,after=N,count=c) for (n,N),c in swaps.most_common()])
    html=(ROOT/'tools/castle_ground_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
    (OUT/'余响堡_V9地表配色对照.html').write_text(html,encoding='utf-8')
    lines=['# V9 地表配色：范围与材料','',f'相对V8换材{len(delta):,}格：地形表层{report["terrainSurfaceChanges"]:,}格、露天铺地{report["pavingChanges"]:,}格。完整模型仍为{len(a):,}格，范围189×170×267，设计最小角(-90,-48,-84)。',
           '','每个X/Z竖列只替换原模型最上面1格；不挖地下、不增土层、不改下面岩壁。表层方块如同时露出侧面，该方块的一格侧面也会随材质变化，不能仅替换一个方块的顶面纹理。深裂隙和陡坎边缘保留岩石。',
           '','## 分区','','| 区域 | 本轮换材格数 | 材料 | 用法 |','|---|---:|---|---|']
    lines += [f'| {n} | {m["zones"][n]:,} | {mat} | {t} |' for n,mat,t in ZONES]
    lines += ['','## 实际换材操作量','','按材料名称汇总；楼梯方向与半格状态见逐格差异JSON。以下是V8→V9操作量，不是从零手建的总采购量。','', '| 原材料 | 新材料 | 数量 |','|---|---|---:|']
    lines += [f'| {names.get(n,n)} | {names.get(N,N)} | {c:,} |' for (n,N),c in swaps.most_common()]
    lines += ['','## 全模型材料现状','','包含建筑、地形和音乐机；仍是审阅稿，不是最终采购清单。','', '| 材料 | V8 | V9 | 净变化 |','|---|---:|---:|---:|']
    lines += [f'| {names.get(n,n)} | {oldcounts[n]:,} | {counts[n]:,} | {counts[n]-oldcounts[n]:+} |' for n in sorted(set(counts)|set(oldcounts),key=lambda n:-counts[n])]
    lines += ['','## 保持与待验','','V8墙体和屋顶配色保留。32,260格音乐/控制、2,307个音符盒、471个光源及灯具组件/支撑保持；35条路线的坐标、宽度、净空和台阶方向不变，部分露天路面颜色改变。所有非表层内容不变。',
              '','原V8/V7/V6及12个NBT未改；没有新版NBT，没有修改服务器或存档。当前仍为第3步中的配色补充，其余几何精修、照明协调和施工包/实机验收未完成。',
              '','图片使用本机26.3-snapshot-9原版方块模型/纹理绘制，不是游戏截图；省略UV锁定、环境遮蔽、游戏光照和生物群系染色，动画取首帧。网页仅静态检查，未浏览器交互或游戏实机验收。']
    (OUT/'地表材料与改动清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text('''# V9 地表配色

打开 `余响堡_V9地表配色对照.html`，左侧V8、右侧V9。先看两个整堡角度，再看入口坡道和地表近景。网页附四个配色区域与实际替换数量。

本轮只换地基最外面的地表层及少量露天铺地，不增加土层，不改变地下和下部岩壁。露出侧面的顶层方块会连同自身侧面变色。建筑墙体、屋顶、音乐和灯具保持。

`castle_v9.json`包含完整城堡和音乐；`v9_changes.json`包含本轮设计坐标、材料、状态与分区。坐标不是服务器世界坐标，材料表不是最终采购单。旧NBT不是V9外观。

发给朋友时发送整个ground_v9文件夹，3张PNG不要漏掉。离线查看无需Python或网页服务。回看V8链接需要同时保留palette_v8目录。

本轮没有新版NBT或游戏实测。原计划剩余立面几何精修、照明协调、施工包和隔离创造档验收仍待继续。网页仅静态检查，不绕过此前本地浏览器自动访问限制。
''',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
