"""V14 saved full model plus bounded circuit construction/state artifacts."""
import hashlib
import json
from collections import Counter
from castle_detail import ROOT,read_model
from castle_shortcuts import shortcut_castle,variant,isolation_audit
from castle_front import route_cells
from castle_finish import EMISSION,spread_light
from build_craft_integration import encode
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/shortcuts_v14'
TITLE='余响堡_V14回廊便门与折返梯.html'


def lighting(before,after,routes,access,shortcuts):
    fields={k:spread_light(m,{p:EMISSION[s[0]] for p,s in m.items() if s[0] in EMISSION}) for k,m in [('before',before),('after',after)]}
    points={(x,y+1,z) for r in routes for x,y,z in route_cells(r['points'],r['width'])}
    def stats(field,ps):
        vs=[field.get(p,0) for p in ps]
        return dict(samples=len(vs),minimum=min(vs),mean=round(sum(vs)/len(vs),2),zero=sum(v==0 for v in vs))
    gated=[]
    for c in shortcuts:
        gates=set(map(tuple,c['gateParts']));ps={(x,y+1,z) for x,y,z in c['points']}-gates
        gated.append(dict(id=c['id'],before=stats(fields['before'],ps),after=stats(fields['after'],ps),
                          excludedGateCells=sorted(gates),samples=[dict(pos=p,value=fields['after'].get(p,0)) for p in sorted(ps)]))
    return dict(before=stats(fields['before'],points),after=stats(fields['after'],points),gated=gated,
                dimmerSamples=[dict(pos=p,before=fields['before'].get(p,0),after=fields['after'].get(p,0)) for p in sorted(points) if fields['after'].get(p,0)<fields['before'].get(p,0)],
                access=[dict(name=r['name'],after=stats(fields['after'],{(x,y+1,z) for x,y,z in r['points']})) for r in access],
                method='原保守六邻域传播，梯子按透光格、不透明异形方块按整格遮挡。特殊路线采样排除门/活板门格，包含梯子格；不含天空光/反射/真实更新，不能替代游戏光照。')


def main():
    m=shortcut_castle();d=m['data'];b=m['before'];a=m['after'];OUT.mkdir(exist_ok=True)
    source=[ROOT/'castle_v3/interior_v13/castle_v13.json',*sorted((ROOT/'nbt_save').glob('*.nbt'))]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source}
    assets=VanillaAssets();names={**d['names'],'iron_door':'铁门','iron_trapdoor':'铁活板门','lever':'拉杆','redstone_wire':'红石粉','repeater':'红石中继器','ladder':'梯子','cut_sandstone':'切制砂岩','chiseled_sandstone':'雕纹砂岩'};colors=dict(d['colors'])
    states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in ('shell','terrain')}
    overlays={}
    for c in m['shortcuts']:
        opened=variant(a,c,True)
        overlays[c['id']]=[dict(pos=p,before=a[p],after=opened[p]) for p in sorted(opened) if a[p]!=opened[p]]
        states.update((v['after'][0],tuple(sorted(v['after'][1].items()))) for v in overlays[c['id']])
    for n,p in sorted(states):assets.elements(n,p);colors[n]=assets.swatch(n,p)
    delta=[dict(pos=p,before=b.get(p),after=a.get(p)) for p in sorted(m['changed'])]
    place=Counter(a[p][0] for p in m['changed'] if p in a);recover=Counter(b[p][0] for p in m['changed'] if p in b)
    # Block counts are distinct from items: placing one iron-door item creates two halves.
    items=Counter(place);items['iron_door']=place['iron_door']//2
    materials=dict(placeBlocks=place,removeBlocks=recover,placeItems=items,
                   note='材料为本轮需放置物品，铁门上下两格只消耗1扇门。拆下数量按方块位置计，实际掉落受工具/玩法影响。不是全堡采购单。')
    report=dict(version='V14',date='2026-09-13',target='26.3-snapshot-9',dataVersion=5011,totalBlocks=len(a),
                changedCoordinates=len(delta),added=sum(v['before'] is None for v in delta),removed=sum(v['after'] is None for v in delta),
                replaced=sum(v['before'] is not None and v['after'] is not None for v in delta),
                oldRoutes=len(d['routes']),ordinaryRoutes=len(d['routes'])+len(m['access']),gatedRoutes=2,
                noteBlocks=sum(s[0]=='note_block' for s in a.values()),musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in a.values()),
                lightBlocks=sum(s[0] in EMISSION for s in a.values()),modelStatesChecked=len(states),
                sourceHashes=hashes,size=d['size'],designMin=d['report']['designMin'],designMax=d['report']['designMax'],
                newNBT=False,inGameTest=False,browserTest=False,default='both gates closed')
    meta=dict(shortcuts=m['shortcuts'],access=m['access'],features=m['features'],fixtures=m['fixtures'],replaceable=sorted(m['replaceable']),
              isolation=isolation_audit(b,m['shortcuts'],m['changed']),
              scope='持久拉杆开关，非永久单向锁，非防熊。指定关闭入口眼位到整个拉杆格的距离下界，不是全区域防绕过证明。',
              assumptions='0.6×1.8玩家碰撞体、1.62眼高、4.5格交互阈值；不含飞行/搭块/拆块/风弹/自定义属性。')
    full={**d,**encode(a,d['offset']),'names':names,'colors':colors,'report':report,'routes':d['routes']+m['access'],
          'features':d['features']+m['features'],'fixtures':d['fixtures']+m['fixtures'],'shortcutsV14':meta,'featureProvenance':d['featureProvenance']+' V14 two latched shortcuts.'}
    def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    write('castle_v14.json',full);assert read_model(OUT/'castle_v14.json')[1]==a
    write('v14_changes.json',delta);write('机关与通路.json',meta);write('开启状态覆盖.json',overlays)
    write('材料增减.json',materials);write('validation.json',report)
    light=lighting(b,a,d['routes'],m['access'],m['shortcuts']);write('照明代理.json',light)
    wanted=set()
    for f in m['features']:
        r=f['region'];wanted.update((x,y,z) for x in range(r[0]-2,r[1]+3) for y in range(r[2]-1,r[3]+2) for z in range(r[4]-2,r[5]+3))
    payload=dict(**encode({p:a[p] for p in wanted if p in a},d['offset']),offset=d['offset'],names=names,colors=colors,
                 changes=delta,overlays=overlays,meta=meta,report=report,materials=materials,lighting=light)
    template=(ROOT/'tools/castle_shortcuts_viewer.html').read_text(encoding='utf-8')
    (OUT/TITLE).write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
    lines=['# V14 回廊便门与藏谱折返梯施工','',f'完整模型{len(a):,}格；只改{len(delta)}个坐标：新增{report["added"]}、替换{report["replaced"]}、删除{report["removed"]}。V13和源NBT保留，真实存档未改。','',
           '全部是设计坐标。先选世界中设计原点O，再以世界坐标=设计坐标+O施工。JSON的offset仅用于文件索引，不是服务器放置坐标。','',
           '## S1 回廊便门','',
           '1. 对照旧门洞：X=-32…-30、Y=1…3、Z=60的9格铁栏杆改造。保留Y=4的原凝灰岩横楣。两侧6格放切制砂岩，中央Y=3放雕纹砂岩。',
           '2. 中央(-31,1,60)放1扇铁门，会自动占Y=1、2两格。最终 facing=north、hinge=left、open=false、powered=false。用F3核对状态；若铰链反了，重放门，不能照图将两扇物品叠起来。',
           '3. 按逐层图搭北控制柱、Y=4高位支撑梁和向门柱降落的支撑。原路Y=1…3三格净空留空。必须用所列导电整块，不用玻璃、半砖替换线下支撑。',
           '4. 将下表S1红石线按序铺在支撑上。中继器(-32,1,59)输入在北、输出向南，facing=north、delay=1。朝南放置后用F3确认，不要多右键加档。',
           '5. 拉杆在(-34,4,53)，安装于西邻(-35,4,53)实心柱的东面。站在设计支撑格(-34,0,54)抬头操作。默认关，从回廊内侧拨开后，前庭可直接返回。','',
           '## S2 藏谱折返梯口','',
           '1. 只补(-46,17…22,2)的6架梯子，和原Y=23…32梯子全部朝东。每级西面X=-47必须有原实心背板。不要把整列旧梯子拆光。',
           '2. 原(-46,33,2)的顶梯拆下，换铁活板门：facing=east、half=bottom、open=false、powered=false。顶部必须紧贴同向梯子；打开后的门片在西侧，可作为梯子上端继续爬。',
           '3. 仅把(-47,34,z)，z=-4…2的7格内墙改红石线槽。下方Y=33原支撑、背后X=-48原墙和上方Y=35墙保留。槽内有真实线，不用铁链替代。',
           '4. 在原Y32楼板上，先放(-46,33,-4)和(-46,34,-4)两格切制砂岩柱，上格东侧(-45,34,-4)放拉杆。第一次走原楼梯到上廊，站设计支撑格(-43,32,-4)拨开。控制位已比早期草案北移一格。',
           '5. 终端线(-47,34,2)给下方原木板(-47,33,2)供电，再开启东邻梯口。无需另加火把、按钮或中继器。固定梯子不升降，关闭时不能走此捷径，原普通楼梯仍在。','',
           '## 逐格铺线顺序','', '| 机关/顺序 | 设计坐标 | 开启稳态预期强度 |','|---|---|---:|']
    for c in m['shortcuts']:
        for i,(p,v) in enumerate(zip(c['wire'],c['circuitOn']['wirePower'])):lines.append(f'| {c["id"]}/{i+1} | {p} | {v} |')
    lines+=['','强度由这两种有支撑、无串电的拓扑推导；不是运行游戏测量。S1经1档中继器恢复15；S2终端9。','',
            '## 两处新增照明','',
            'S1门外：(-30,1,65)放雕纹凝灰岩砖，其上(-30,2,65)放落地灯笼。原(-30,0,65)地板不改。',
            'S2梯井：(-46,25,3)放切制砂岩，西面连接原(-47,25,3)砖墙，其上(-46,26,3)放落地灯笼。不要放到Z=2梯子列。',
            '灯笼均hanging=false、水含量false。旧510光源保持，总512；仅门片格不纳入保守代理采样，梯子格有计算，仍需游戏夜间实测。','',
            '## 本轮材料（已有V13时）','',materials['note'],'','| 材料 | 放置物品 | 新状态方块格 | 拆下旧方块格 |','|---|---:|---:|---:|']
    for n in sorted(set(place)|set(recover),key=lambda k:-place[k]):lines.append(f'| {names.get(n,n)} `{n}` | {items[n]} | {place[n]} | {recover[n]} |')
    lines+=['','## 游戏内待验，不可省略','',
            '在独立创造测试档按默认关闭状态搭建：确认两门阻挡→沿普通路线到控制位→拨开→来回通过→拨关→再开。S2需实际爬过梯口并转到上廊，不仅观察门片转动。',
            '两机关保持开启后保存退出、重新进世界，检查拉杆、门和梯子状态。检查中继器北输入/南输出、灯光、邻居更新和区块加载；整曲试听不能因机关操作出现误音。',
            '朋友服务器若版本、红石插件、玩家触及属性不同，须重新验收。不承诺防拆、防飞行、防风弹或权限隔离。不要在服务器直接覆盖含空气的大NBT。','',
            '静态证据：0→1→0稳态、真实门片连续碰撞、梯背/同向、旧路线/家具/音乐冻结、附近旧响应组件隔离。原40路线照明代理无变暗，新3处入口最低8、8、10；梯井全段光照未实测。','',
            '未交付：S3、其余房间内饰、最终全堡采购/手建包及NBT、隔离创造档验收。没有游戏或浏览器交互测试。']
    (OUT/'施工与材料.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text(f'# V14双捷径\n\n打开 `{TITLE}`。页面可切换关/开预期状态、看原版模型近景、逐层核对和按世界原点换算坐标。\n\n分享整个shortcuts_v14目录，四张PNG不能漏。无需Python/联网；回看V13及研究链接需保留上级目录。\n\n完整JSON默认两处关闭；开启覆盖只供预览与状态核对，不能直接当NBT导入。材料区分铁门物品与上下两格方块。无新版NBT、无存档修改、无实机验收。\n',encoding='utf-8')
    for p in source:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))]
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
