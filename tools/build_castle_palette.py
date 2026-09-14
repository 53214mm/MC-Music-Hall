"""Publish the independent V8 coordinated palette pass from immutable V7."""
import hashlib
import json
from collections import Counter

from build_craft_integration import encode
from castle_palette import ROOT, recolor_castle
from castle_detail import read_model
from castle_finish import EMISSION
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/palette_v8'
ZONES=[
    ('主堡','泥砖墙身，上层泥坯横带','保留浅砂岩窗套、扶垛和深灰屋顶；暖褐色承担主体，不再让灰墙占据上半部。'),
    ('南门楼','下段暖褐，上段砖红','红砖呼应唱诗堂和西翼，灰色基础与桥墩保留。'),
    ('西翼藏谱馆','暖褐下层，砖红上层','让入口至藏谱馆形成同一组暖色立面。'),
    ('生活翼','方解石填墙，原有云杉木构','浅色小体量穿插在厚重主堡旁，深色屋面与少量铜绿窗帽不变。'),
    ('外围长墙','泥砖墙身，浅砂岩压顶','沿院落边界形成连续的暖褐轮廓，灰石脚与地形继续压住底部。'),
    ('冠塔','暖褐塔身，砖红高层窗廊','塔身与主堡同族，高处少量砖红和浅色构件拉开纵向层次。'),
    ('北阶塔','暖褐塔身，砖红高层窗廊','沿用同一套材料语法，保留原塔高、台阶和冠部轮廓。'),
    ('烽塔','暖褐塔身，砖红高层窗廊','灰色低部保留，不把岩体与塔楼涂成同一颜色。'),
    ('维修塔','暖褐塔身，砖红高层窗廊','与东侧翼连续衔接，屋顶仍为深灰。'),
    ('东侧维修翼','暖褐墙身，浅砂岩饰件','填补原本大面积裸灰的东侧，避免只装饰入口。'),
    ('唱诗堂','延续已有红砖，补齐残余灰墙','保留V7的新老虎窗、屋坡与窗框，不新增另一套主色。'),
    ('回廊与院墙','暖褐围护，浅色细构件','连接各区；路面、登记通路净空与灯具保持。'),
]


def main():
    paths=[ROOT/'castle_v3/integration_v7/castle_v7.json',ROOT/'castle_v3/finish_v6/castle_v6.json',*sorted((ROOT/'nbt_save').glob('*.nbt'))]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    m=recolor_castle();data=m['data'];before=m['before'];after=m['after'];delta=m['changed']
    OUT.mkdir(exist_ok=True)
    names={**data['names'],'mud_bricks':'泥砖','packed_mud':'泥坯','cut_sandstone':'切制砂岩','chiseled_sandstone':'錾制砂岩','bricks':'红砖块','calcite':'方解石'}
    assets=VanillaAssets();colors=dict(data['colors'])
    states={(s[0],tuple(sorted(s[1].items()))) for s in after.values() if s[2] in ('shell','terrain')}
    for n,props in sorted(states):
        assets.elements(n,props)
        colors[n]=assets.swatch(n,props)
    counts=Counter(s[0] for s in after.values());oldcounts=Counter(s[0] for s in before.values())
    swaps=Counter((before[p][0],after[p][0]) for p in delta)
    assert before.keys()==after.keys()
    assert all(a[1:]==before[p][1:] for p,a in after.items())
    assert all(after[p]==before[p] for p in m['frozen'] if p in before)
    lo=[min(p[i] for p in after) for i in range(3)];hi=[max(p[i] for p in after) for i in range(3)];offset=[-v for v in lo]
    report=dict(version='V8',date='2026-09-13',source='integration_v7/castle_v7.json',scope='第3步中的整堡配色扩展；几何精修未完成',
                totalBlocks=len(after),changedCoordinates=len(delta),added=0,removed=0,replaced=len(delta),sameCoordinates=True,sameProperties=True,
                size=[hi[i]-lo[i]+1 for i in range(3)],designMin=lo,designMax=hi,noteBlocks=counts['note_block'],musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in after.values()),
                lightBlocks=sum(counts[n] for n in EMISSION),routes=len(data['routes']),zoneSurfaceReplacements=dict(m['zone_counts']),
                target='26.3-snapshot-9',dataVersion=5011,completedPlanSteps=[1,2],currentPlanStep=3,remainingPlanSteps=[3,4,5],
                newNBT=False,inGameTest=False,browserTest=False,modelStatesChecked=len(states),sourceHashes=hashes)
    def write(name,value):
        (OUT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    full=dict(**encode(after,offset),offset=offset,names=names,colors=colors,size=report['size'],routes=data['routes'],connections=data['connections'],fixtures=data['fixtures'],features=data['features'],report=report)
    # The inherited features describe V7 construction. V8 has no additional geometry.
    full['featureProvenance']='integration_v7: inherited unchanged; counts describe V7 integration, not V8 recoloring'
    write('castle_v8.json',full)
    _,roundtrip=read_model(OUT/'castle_v8.json');assert roundtrip==after
    report['fullModelRoundtrip']=True
    write('v8_changes.json',[dict(pos=p,before=before[p],after=after[p]) for p in sorted(delta)])
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))],p
    report['sourceHashesUnchanged']=True
    write('validation.json',report)
    payload=dict(report=report,colors=colors,names=names,zones=[dict(name=n,palette=p,note=t,count=m['zone_counts'][n]) for n,p,t in ZONES],
                 swaps=[dict(before=a,after=b,count=c) for (a,b),c in swaps.most_common()],
                 materials=[dict(name=n,before=oldcounts[n],after=counts[n]) for n in sorted(set(counts)|set(oldcounts),key=lambda n:-counts[n])])
    html=(ROOT/'tools/castle_palette_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
    (OUT/'余响堡_V8整堡配色对照.html').write_text(html,encoding='utf-8')
    lines=['# V8 整堡配色扩展：材料与改动清单','',
           f'在V7完整模型上原位换材 {len(delta):,} 格。总量仍为 {len(after):,} 格，范围仍为 189×170×267。没有新增/删去坐标，没有改动方块属性和分组。','',
           '这是第3步的配色扩展，不是第3步全部完成。立面几何精修、照明协调和最终施工验收仍待继续；没有新版NBT，也不是最终采购清单。','',
           '## 配色分区','','| 分区 | 换材格数 | 配色 | 设计用法 |','|---|---:|---|---|']
    lines += [f'| {n} | {m["zone_counts"][n]:,} | {p} | {t} |' for n,p,t in ZONES]
    lines += ['','分区是设计坐标规则；统计仅指本轮实际改动格数，不是立面可见像素面积。仅处理shell组横向接触空气的灰色方块，音乐保护区、路线、灯具和低部灰石例外保留。内部朝向空气的墙皮也可能换材，不将这一点冒称内饰设计完成。',
              '','## 原位替换操作量','','| 原材料 | 新材料 | 格数 |','|---|---|---:|']
    lines += [f'| {names.get(a,a)} | {names.get(b,b)} | {c:,} |' for (a,b),c in swaps.most_common()]
    lines += ['','具体坐标和原/新状态见 `v8_changes.json`，使用整堡设计坐标，非服务器世界坐标。台阶仍是台阶、楼梯仍是楼梯、墙仍是墙，保留原方向及上下半等状态；逐种替换已与本机原版模型几何比较。','',
              '## 全模型材料现状','','含建筑、岩体和音乐机。净变化不是施工拆换次数，不区分方向的汇总不能替代状态清单。','',
              '| 材料 | V7 | V8 | 净变化 |','|---|---:|---:|---:|']
    lines += [f'| {names.get(n,n)} | {oldcounts[n]:,} | {counts[n]:,} | {counts[n]-oldcounts[n]:+} |' for n in sorted(set(counts)|set(oldcounts),key=lambda n:-counts[n])]
    lines += ['','## 保持与待验','','32,260格音乐/控制、2,307个音符盒、471个光源及灯具组件、35条登记路线保持。所有地形和深灰屋顶未换材，V7新窗洞与异形构件保持。原V7/V6 JSON、全部12个源NBT未改变。',
              '','配图读取26.3-snapshot-9原版模型和纹理，是方块数据渲染，不是游戏截图。省略UV锁定、环境遮蔽、游戏光照与生物群系染色，动画取首帧。没有浏览器交互和游戏实机验收；灯具未移动不代表完成照明验收。']
    (OUT/'材料分区与改动清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text('''# V8 整堡配色扩展

打开 `余响堡_V8整堡配色对照.html`。先看南东与西南两个同角度远景，再看窗跨和外围长墙近景；所有图左侧V7、右侧V8。下方有各区配色、实际替换数量和完整材料统计。

主堡和长墙采用暖褐泥砖；门楼、西翼及高塔上层以红砖互相呼应；浅砂岩构件统一窗框和檐口。生活翼延续方解石与云杉，深灰屋顶和灰色岩体保留。本轮只改材料，不改形状、音乐、路线或灯具。

`castle_v8.json`是包含音乐的完整模型。`v8_changes.json`是相对V7的逐格替换，使用整堡设计坐标。`材料分区与改动清单.md`不是最终采购清单。需要回看12处构件的逐层形状时可查看V7页面；其配色不代表V8。

与朋友分享时发送整个palette_v8文件夹，4张PNG不要遗漏。本页离线可用，不需要Python或网页服务。回看旧版的链接需要同时保留integration_v7目录。

仍处于第3步：这一轮完成配色扩展，剩余立面几何精修、照明协调、最终施工包与隔离创造档实测尚未完成。没有新版NBT，没有修改真实存档。不要把旧NBT当成V8外观。

网页仅静态检查，未浏览器交互验收。配图为本机原版方块模型/纹理数据渲染，不是游戏截图；不含游戏光照与环境遮蔽等效果。
''',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
