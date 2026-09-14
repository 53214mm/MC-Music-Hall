"""Publish V11 route-aware window bays and niche lamps independently of V10."""
import hashlib
import json
from collections import Counter
from castle_detail import ROOT, read_model
from castle_joint import joint_castle
from castle_joint_lighting import lighting_audit
from castle_finish import EMISSION
from build_craft_integration import encode
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/detail_v11'


def main():
    sources=[ROOT/f'castle_v3/{folder}/{name}' for folder,name in [('detail_v10','castle_v10.json'),('ground_v9','castle_v9.json'),('palette_v8','castle_v8.json'),('integration_v7','castle_v7.json'),('finish_v6','castle_v6.json')]]+sorted((ROOT/'nbt_save').glob('*.nbt'))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    m=joint_castle();lighting,_=lighting_audit();a=m['after'];b=m['before'];data=m['data'];delta=m['changed'];assets=VanillaAssets()
    OUT.mkdir(exist_ok=True);colors=dict(data['colors']);counts=Counter(s[0] for s in a.values());oldcounts=Counter(s[0] for s in b.values())
    states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in ('shell','terrain')}
    for n,props in sorted(states):assets.elements(n,props);colors[n]=assets.swatch(n,props)
    lo=[min(p[i] for p in a) for i in range(3)];hi=[max(p[i] for p in a) for i in range(3)];offset=[-v for v in lo]
    report=dict(version='V11',date='2026-09-13',source='detail_v10/castle_v10.json',scope='两处平台窗廊适配、四盏侧挂灯与26盏拱龛挂灯',
        totalBlocks=len(a),changedCoordinates=len(delta),added=len(set(a)-set(b)),removed=len(set(b)-set(a)),replaced=sum(p in a and p in b for p in delta),
        features=len(m['features']),featureFamilies=dict(Counter(f['family'] for f in m['features'])),newFixtures=len(m['fixtures']),resolvedV10Deferrals=m['resolved'],
        size=[hi[i]-lo[i]+1 for i in range(3)],designMin=lo,designMax=hi,noteBlocks=counts['note_block'],musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in a.values()),
        previousLightBlocks=sum(s[0] in EMISSION for s in b.values()),lightBlocks=sum(s[0] in EMISSION for s in a.values()),routes=len(data['routes']),
        target='26.3-snapshot-9',dataVersion=5011,modelStatesChecked=len(states),sourceHashes=hashes,newNBT=False,inGameTest=False,browserTest=False,
        planStatus='两处共用窗位已适配；照明协调进入代理检查。其余细节、内饰、捷径与最终施工/实机验收未完成。')
    def write(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    full={**data,**encode(a,offset),'offset':offset,'size':report['size'],'colors':colors,'report':report,
        'features':data['features']+m['features'],'featureProvenance':'First 12: V7; next 46: V10; last 28: V11. Counts describe each construction pass.',
        'fixtures':data['fixtures']+m['fixtures'],'deferredFeatures':[],'resolvedV10Deferrals':m['resolved']}
    write('castle_v11.json',full);_,roundtrip=read_model(OUT/'castle_v11.json');assert roundtrip==a
    edits=[dict(pos=p,before=b.get(p),after=a.get(p)) for p in sorted(delta)]
    manifest=dict(features=m['features'],fixtures=m['fixtures'],resolvedV10Deferrals=m['resolved'],bayRegions=m['bayRegions'])
    write('v11_changes.json',edits);write('构件与新灯定位.json',manifest);write('照明代理与待验坐标.json',lighting)
    for p in sources:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))]
    report.update(fullModelRoundtrip=True,sourceHashesUnchanged=True);write('validation.json',report)
    wanted=set()
    for f in m['features']:
        r=f['region'];wanted.update((x,y,z) for x in range(r[0]-2,r[1]+3) for y in range(r[2]-2,r[3]+3) for z in range(r[4]-2,r[5]+3))
    payload=dict(**encode({p:a[p] for p in wanted if p in a},offset),offset=offset,names=data['names'],colors=colors,features=m['features'],report=report,changes=edits,lighting=lighting)
    html=(ROOT/'tools/castle_joint_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
    (OUT/'余响堡_V11窗廊与暖灯.html').write_text(html,encoding='utf-8')
    lines=['# V11 窗廊与暖灯：构件施工和材料','',f'相对V10影响{len(delta):,}个坐标：新增{report["added"]}、移除{report["removed"]}、原位替换{report["replaced"]}。完整模型{len(a):,}格，范围{report["size"]}。',
        '','## 建造顺序','','坐标均为设计坐标，不是服务器世界坐标。先在逐层图定位，橙框是V11改动；材料表不是最终采购单。',
        '', '1. 烽塔南窗：先标记Y64/76平台和Y65/77栏杆，原样保留；共用灯座(-55,66,-31)及其组件不能拆。按差异拆旧外框，保留玻璃。先放Y62上半窗台及下托，Y63薄柱；Y68起做上窗廊的砂岩墙细柱，右柱向下接Y65端柱；拱最高只到Y75。下部有支撑的中央旧实柱改细云杉栅栏；上部Y68至70失去下接点的三格旧窗棂移除，避免留下悬空木杆，后方玻璃不拆。',
        '2. 维修塔南窗：原Y54平台、Y55栏杆和Y58以上檐口保留。拆两层旧外框的可改成员，做Y43上半窗台、Y42倒楼梯托石；Y44至51薄柱，低拱顶部最高Y53。原玻璃和后方灯座保留。',
        '3. 窗边侧挂灯：先在原实墙上做两格石颈，再以倒楼梯向侧面伸一格，下面一格铁链、一盏挂灯笼。烽塔灯在(-56,69,-31)、(-46,69,-31)，维修塔灯在(62,49,17)、(72,49,17)。放灯前应核对支撑与链条，不靠红石驱动。',
        '4. 长墙26个拱龛：在各凹龛最上方的空气格放一格竖铁链，链下面放挂灯笼；链上方直接连接原实心龛顶。高墙灯Y12、低墙灯Y5、北墙灯Y14，准确X/Z见下表。不要拆后面两层背墙，也不改砂岩拱框。',
        '', '## 实际构件定位','','| 构件 | X / Y / Z 范围 | 操作格数 |','|---|---|---:|']
    for f in m['features']:
        r=f['region'];lines.append(f'| {f["name"]} | {r[0]}…{r[1]} / {r[2]}…{r[3]} / {r[4]}…{r[5]} | {f["changed"]} |')
    lines+=['','## 30盏新增灯位','','| 名称 | 灯笼 X,Y,Z | 实墙/拱顶锚点 |','|---|---|---|']
    for f in m['fixtures']:lines.append(f'| {f["name"]} | {f["pos"]} | {f["supports"]} |')
    lines+=['','## 本轮材料操作量','','新增和移除按状态变更分别计数：同格换材计入旧材料移除和新材料放置；不能只看净增量备料。','', '| 材料 | 放置 | 拆除 | 净变化 |','|---|---:|---:|---:|']
    placed=Counter(a[p][0] for p in delta if p in a);removed=Counter(b[p][0] for p in delta if p in b)
    for n in sorted(set(placed)|set(removed),key=lambda n:-placed[n]):lines.append(f'| {data["names"].get(n,n)} | {placed[n]} | {removed[n]} | {placed[n]-removed[n]:+} |')
    lines+=['','灯光部分新增灯笼30、铁链30。没有替换原471个光源或插入红石元件。','', '## 完整模型材料现状','','包含地形、音乐和所有旧建筑，供审阅对账，不是最终采购数量。','', '| 材料 | V10 | V11 | 净变化 |','|---|---:|---:|---:|']
    for n in sorted(set(counts)|set(oldcounts),key=lambda n:-counts[n]):lines.append(f'| {data["names"].get(n,n)} | {oldcounts[n]:,} | {counts[n]:,} | {counts[n]-oldcounts[n]:+} |')
    lines+=['','## 照明检查与待验','','35条登记路线全宽上方共6,331个去重采样点，代理平均值9.35、零值28、低于5有87，前后不变且无变暗点。26个拱龛前方空气格因新增挂灯变亮；这是外墙装饰灯，不等于室内/音乐区全部照明完成。',
        '','零值坐标与所处方块列在照明代理与待验坐标.json；其中25个位于音乐保护体积，不在本轮直接插灯。该六邻域算法把不透明异形方块当整格遮挡，无天空光/刷怪判定，必须结合实机核对。',
        '','保留所有音乐、地形/V9地表、通路/平台/栏杆、旧灯具与源NBT。V10两处保留项已用适配造型解决；其余外饰、叙事内饰、捷径、完整施工包及游戏验收仍未完成。无新版NBT、无真实存档修改、未浏览器交互测试。']
    (OUT/'构件施工与材料清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text('''# V11 平台窗廊与暖灯

打开 `余响堡_V11窗廊与暖灯.html`。先看三组近景：烽塔分隔窗廊、维修塔低拱窗、长墙龛内灯。两张整堡图供核对轮廓，数值剖面只演示六邻域照明代理，不是游戏夜景。

两处V10保留窗位已分别适配，不动路线、平台/栏杆和灯座。新增30盏灯笼及30格铁链，总光源471→501，既有音乐和地表保持。35条路线代理没有变暗，仍有28个零值采样点须核对，不能声称全堡已照亮或防刷怪。

页面下方可选28组构件看逐层和原→新差异；含音乐的完整模型、精确改动、材料表与灯位同目录。设计坐标不是服务器坐标，材料表不是最终采购单。

发给朋友时发送整个detail_v11目录，6张PNG不能遗漏；回看V10需保留detail_v10。离线看图不需要Python或网页服务。

不覆盖旧模型或NBT，不修改真实存档。暂无新NBT，也未浏览器交互或游戏实机验收；后续照明协调、施工包/实机测试、叙事内饰和捷径仍需继续。
''',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
