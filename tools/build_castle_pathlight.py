"""Publish additive V12 lights without altering previous outputs."""
import hashlib
import json
from collections import Counter
from castle_detail import ROOT,read_model
from castle_pathlight import pathlight_castle,pathlight_audit
from castle_finish import EMISSION
from build_craft_integration import encode
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/light_v12'


def main():
    paths=[ROOT/f'castle_v3/{folder}/{name}' for folder,name in [('detail_v11','castle_v11.json'),('detail_v10','castle_v10.json'),('ground_v9','castle_v9.json'),('palette_v8','castle_v8.json'),('integration_v7','castle_v7.json'),('finish_v6','castle_v6.json')]]+sorted((ROOT/'nbt_save').glob('*.nbt'))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    m=pathlight_castle();lighting,_=pathlight_audit();data=m['data'];a=m['after'];b=m['before'];assets=VanillaAssets()
    OUT.mkdir(exist_ok=True);colors=dict(data['colors']);counts=Counter(s[0] for s in a.values())
    states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in ('shell','terrain')}
    for n,props in sorted(states):assets.elements(n,props);colors[n]=assets.swatch(n,props)
    materials=dict(Counter(a[p][0] for p in m['added']));offset=data['offset']
    report=dict(version='V12',date='2026-09-13',source='detail_v11/castle_v11.json',scope='原28个零值点：入口端柱与试听走廊梁下定点补灯',
        totalBlocks=len(a),changedCoordinates=len(m['added']),added=len(m['added']),removed=0,replaced=0,features=len(m['features']),newFixtures=len(m['fixtures']),materials=materials,
        size=data['size'],designMin=data['report']['designMin'],designMax=data['report']['designMax'],
        noteBlocks=counts['note_block'],musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in a.values()),routes=len(data['routes']),
        previousLightBlocks=sum(s[0] in EMISSION for s in b.values()),lightBlocks=sum(s[0] in EMISSION for s in a.values()),
        allOldBlocksUnchanged=all(a[p]==s for p,s in b.items()),musicHaloUnchanged=not bool(m['added']&m['musicHalo']),
        exactMusicExceptionCells=len(m['approved']),musicSeparation=m['separation'],
        target='26.3-snapshot-9',dataVersion=5011,modelStatesChecked=len(states),sourceHashes=hashes,
        newNBT=False,inGameTest=False,browserTest=False,planStatus='原28个零值点代理改善；余下24个低值点及真实光照/音乐验收仍待核对。')
    def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    approval=[dict(pos=p,state=s) for p,s in sorted(m['approved'].items())]
    full={**data,**encode(a,offset),'report':report,'colors':colors,'features':data['features']+m['features'],
        'featureProvenance':'V7 12; V10 46; V11 28; V12 7. Counts refer to their construction pass.',
        'fixtures':data['fixtures']+m['fixtures'],'musicAirLightingExceptions':approval}
    write('castle_v12.json',full);_,roundtrip=read_model(OUT/'castle_v12.json');assert roundtrip==a
    edits=[dict(pos=p,before=None,after=a[p]) for p in sorted(m['added'])]
    write('v12_changes.json',edits);write('音乐区精确例外.json',approval)
    write('灯具定位.json',dict(features=m['features'],fixtures=m['fixtures'],musicSeparation=m['separation']))
    write('照明代理与剩余待验点.json',lighting)
    for p in paths:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))]
    report.update(fullModelRoundtrip=True,sourceHashesUnchanged=True);write('validation.json',report)
    wanted=set()
    for f in m['features']:
        r=f['region'];wanted.update((x,y,z) for x in range(r[0]-2,r[1]+3) for y in range(r[2]-2,r[3]+3) for z in range(r[4]-2,r[5]+3))
    payload=dict(**encode({p:a[p] for p in wanted if p in a},offset),offset=offset,names=data['names'],colors=colors,features=m['features'],report=report,changes=edits,lighting=lighting)
    html=(ROOT/'tools/castle_pathlight_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
    (OUT/'余响堡_V12入口与试听走廊照明.html').write_text(html,encoding='utf-8')
    lines=['# V12 入口与试听走廊：灯具施工','',f'仅新增{len(m["added"])}格，零拆除、零换材；完整模型{len(a):,}格。光源501→508。',
        '', '## 本轮材料','','- 灯笼：7','- 铁链：19（1＋9＋9）','- 雕纹凝灰岩砖：4','- 原梁、栏杆柱、土面：利用原构件，不新增。',
        '', '## 精确搭建顺序','','所有位置为设计坐标，需要统一偏移后才是服务器坐标。上半/朝向状态见逐层图，不能随意把灯挪到音符盒或线路边。',
        '', '1. 中央试听位：确认(20,3,4)是原磨制安山岩梁。其下(20,2,4)接竖铁链，(20,1,4)挂灯笼。原试听平台支撑Y=-3，走路三格净空Y=-2…0保持。',
        '2. 高桥中/东段：分别确认(30,15,5)、(38,15,5)为原梁；在同X/Z的Y14往下接到Y6，各9格铁链，再在Y5挂灯笼。桥面Y1不动，Y2…4三格通行净空保持。不另搭新横梁，不跨接到音乐模块。',
        '3. 前庭落差：原栏杆柱(-51,-4,85)、(-47,-4,85)各上叠1格雕纹凝灰岩砖，灯笼放在Y=-2。',
        '4. 南入口坡道：西侧原栏杆柱(-46,-23,170)上加灯座，灯笼Y=-21。东侧(-40,-22,170)原地表高一格，保留土面，灯座Y=-21、灯笼Y=-20。不要为了强行同高挖掉地表。',
        '', '## 灯与原支撑','','| 灯具 | 灯 X,Y,Z | 原支撑 | 新增格数 |','|---|---|---|---:|']
    for f in m['fixtures']:lines.append(f'| {f["name"]} | {f["pos"]} | {f["supports"][0]} | {len(f["parts"])} |')
    lines+=['','## 音乐区例外不是整片放开','','音乐区只允许音乐区精确例外.json列出的22个位置和状态：3灯笼、19铁链，且原来必须为空气。所有旧方块、音乐/控制及一格邻域、音符盒上方一格、全部路线支撑和三格净空都冻结。三个灯组离音乐方块的最小切比雪夫距离为2、2、3格；不相邻。',
        '', '## 照明与未验项目','','35条路线6,331个全宽去重采样：零值28→0，低于5的87→24，最低0→3，平均9.35→9.44；原28个零值点均提高到8～12，音乐走廊最低0→5，没有变暗点。',
        '','算法沿用V11六邻域空气代理，不透明异形方块整格遮挡；不含天空光、反射、方块自动连接或生物生成规则。5不是刷怪阈值。剩余24个3～4值点见照明代理与剩余待验点.json。零值消失不代表全堡光照或音乐已实机验收。',
        '', '## 全模型材料现状','','含地形和音乐，仅供对账，不是最终采购单。','', '| 材料 | 当前数量 |','|---|---:|']
    for n in sorted(counts,key=lambda n:-counts[n]):lines.append(f'| {data["names"].get(n,n)} | {counts[n]:,} |')
    lines+=['','独立light_v12模型；旧版本、源NBT和真实存档不动。无新版NBT，无浏览器交互或游戏实测。配图为原版模型裁切/数值示意，非游戏截图。内饰、捷径与最终施工包仍待后续。']
    (OUT/'灯具施工与材料清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text('''# V12 入口与试听走廊照明

打开 `余响堡_V12入口与试听走廊照明.html`，先看试听走廊与两处入口的真实方块近景，再看照明采样图。音乐区图包含邻近音乐/控制方块，裁切外不代表空气。

只在原空气新增30格：灯笼7、铁链19、雕纹凝灰岩砖4，旧方块一个不拆。音乐实际方块和一格邻域保持，大保护盒内仅允许列明的22格挂灯位置＋状态，不能随意放开整个区域。

原28个零代理值点已提高到8～12；35条路线共6,331个采样没有变暗，剩余24个3～4值点仍待核对。这不是游戏光照或刷怪验收，未试听音乐。

页面提供7套灯具逐层图和精确坐标；完整JSON、30格新增表和材料清单同目录。设计坐标不是服务器坐标。无新版NBT，不要将旧NBT当作V12。

分享时发送整个light_v12目录，4张PNG不能漏，离线不需要Python或网页服务。旧版链接需要保留detail_v11。未浏览器交互测试，不绕过本地自动访问限制；真实存档未修改。
''',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
