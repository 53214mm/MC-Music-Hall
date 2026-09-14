"""V13 offline construction artifact from the actual saved block model."""
import hashlib
import json
from collections import Counter
from castle_detail import ROOT,read_model
from castle_interior import interior_castle,interior_lighting
from castle_finish import EMISSION
from build_craft_integration import encode
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/interior_v13'
TITLE='余响堡_V13生活与藏谱内饰.html'
ZONE_NAMES={'shelter':'收容长屋','kitchen':'熄火厨房','archive':'藏谱下厅','upper':'藏谱上廊'}


def main():
    m=interior_castle();d=m['data'];b=m['before'];a=m['after'];light=interior_lighting();OUT.mkdir(exist_ok=True)
    files=[ROOT/'castle_v3/light_v12/castle_v12.json']+sorted((ROOT/'nbt_save').glob('*.nbt'))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    assets=VanillaAssets();colors=dict(d['colors']);names=dict(d['names'])
    for n,cn in [('white_carpet','白色地毯'),('red_carpet','红色地毯'),('green_carpet','绿色地毯'),('brown_carpet','棕色地毯'),('oak_slab','橡木台阶'),('oak_planks','橡木木板'),('crafting_table','工作台'),('furnace','熔炉'),('brick_slab','红砖台阶'),('brick_stairs','红砖楼梯')]:names[n]=cn
    states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in ('shell','terrain')}
    for n,props in sorted(states):assets.elements(n,props);colors[n]=assets.swatch(n,props)
    delta=[dict(pos=p,before=b.get(p),after=a.get(p)) for p in sorted(m['changed'])]
    removed=Counter(b[p][0] for p in m['changed'] if p in b);placed=Counter(a[p][0] for p in m['changed'] if p in a)
    fixtures=[]
    for f in m['features']:
        for p in map(tuple,f['parts']):
            if a[p][0] in EMISSION:
                fixtures.append(dict(name=f['name']+'工作灯',zone='厨房',kind='家具座灯',pos=p,parts=[p],supports=[(p[0],p[1]-1,p[2])]))
    report=dict(version='V13',date='2026-09-13',source='light_v12/castle_v12.json',totalBlocks=len(a),
        changedCoordinates=len(delta),added=sum(c['before'] is None for c in delta),removed=sum(c['after'] is None for c in delta),
        replaced=sum(c['before'] is not None and c['after'] is not None for c in delta),features=len(m['features']),zones=4,
        routes=len(d['routes'])+len(m['routes']),oldRoutes=len(d['routes']),newRoutes=len(m['routes']),
        lightBlocks=sum(s[0] in EMISSION for s in a.values()),noteBlocks=sum(s[0]=='note_block' for s in a.values()),
        musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in a.values()),size=d['size'],
        designMin=d['report']['designMin'],designMax=d['report']['designMax'],
        modelStatesChecked=len(states),sourceHashes=hashes,sourceHashesUnchanged=True,fullModelRoundtrip=True,
        target='26.3-snapshot-9',dataVersion=5011,newNBT=False,browserTest=False,inGameTest=False,
        mechanismStatus='S1/S2旧手动测试、S3及正式捷径机关未完成；本轮厨房是常开室内环线。')
    def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    interior=dict(features=m['features'],routes=m['routes'],openings=m['openings'],railUpdates=[dict(pos=p,state=s) for p,s in m['railUpdates'].items()],
                  zones=ZONE_NAMES,replaceable=sorted(m['replaceable']),content='木床不能睡眠；桶/熔炉/工作台未写入物品、燃料或书籍实体。')
    full={**d,**encode(a,d['offset']),'colors':colors,'names':names,'report':report,
          'routes':d['routes']+m['routes'],'features':d['features']+m['features'],'fixtures':d['fixtures']+fixtures,
          'interiorV13':interior,'featureProvenance':d['featureProvenance']+' V13 14 interior furnishings.'}
    write('castle_v13.json',full);_,readback=read_model(OUT/'castle_v13.json');assert a==readback
    write('v13_changes.json',delta);write('内饰与室内通路.json',interior);write('照明代理.json',light)
    write('validation.json',report);write('材料增减.json',dict(place=placed,recover=removed,net={n:placed[n]-removed[n] for n in sorted(set(placed)|set(removed))}))
    wanted=set()
    for f in m['features']:
        r=f['region'];wanted.update((x,y,z) for x in range(r[0]-2,r[1]+3) for y in range(r[2]-2,r[3]+3) for z in range(r[4]-2,r[5]+3))
    # Include removed railing positions and their neighboring context, too.
    for px,py,pz in m['openings']:
        wanted.update((x,y,z) for x in range(px-2,px+3) for y in range(py-1,py+4) for z in range(pz-2,pz+3))
    opening_features=[]
    for i,(x,y,z) in enumerate(m['openings']):
        opening_features.append(dict(name=f'室内栏杆开口{i+1}',zone='kitchen' if z<30 else 'shelter',region=[x-1,x+1,y,y,z-1,z+1],
            note='仅拆中央旧石砖墙格，两侧收回朝开口伸出的连接臂；脚下及四邻同高地板保持，不是临空栏杆。',build='先核对Y0为连续地板，再拆图中旧墙；不要扩大到外墙或灯柱。'))
    payload=dict(**encode({p:a[p] for p in wanted if p in a},d['offset']),offset=d['offset'],names=names,colors=colors,
                 features=m['features']+opening_features,changes=delta,report=report,lighting=light,newRoutes=m['routes'])
    html=(ROOT/'tools/castle_interior_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
    (OUT/TITLE).write_text(html,encoding='utf-8')
    lines=['# V13 生活与藏谱内饰施工','',f'完整模型{len(a):,}格；本轮{len(delta)}个坐标变化，新增{report["added"]}、拆除{report["removed"]}、替换{report["replaced"]}。',
           '', '所有位置是设计坐标，必须使用统一世界偏移。V12保存，真实存档未修改。精确状态与旧→新见逐层页和v13_changes.json。',
           '', '## 推荐施工顺序','', '1. 检查5个栏杆开口脚下与四邻的同高地板，再拆旧栏杆并收回两侧连接臂。保留全部原灯柱。',
           '2. 依次改四张木床、厨房炉台，再放独立储物与工作台。',
           '3. 建藏谱下厅桌柜，再沿原楼梯上到Y32楼板，搭两组上廊柜。中央挑空和旧梯井不加地板。',
           '4. 检查厨房两盏工作灯：(-64,2,12)在桶柜上；(-56,4,10)在上半台阶帽上。熔炉保持未点燃。',
           '', '## 已落地方块的叙事','']
    for f in m['features']:
        lines += [f'### {ZONE_NAMES[f["zone"]]} / {f["name"]}','',f['note'],'',f['build'],'',f'包围范围 X{f["region"][0]}…{f["region"][1]} / Y{f["region"][2]}…{f["region"][3]} / Z{f["region"][4]}…{f["region"][5]}。','']
    lines+=['## 同高室内开口','']+[f'- 拆除 {p} 的旧石砖墙；具体邻接状态按逐格差异。' for p in m['openings']]
    lines+=['','## 材料增减','','替换时先拆旧材料再放新材料，下表分别统计，不能只看净增。默认存量可回收再用；实际回收取决于工具、玩法与掉落。','', '| 材料 | 需放置 | 拆下 | 数量差（放置−拆下） |','|---|---:|---:|---:|']
    for n in sorted(set(placed)|set(removed),key=lambda n:-placed[n]):lines.append(f'| {names.get(n,n)} / {n} | {placed[n]} | {removed[n]} | {placed[n]-removed[n]:+} |')
    lines+=['','## 新路线与照明','','原35条路支撑/三格净空保持；新增5条宽1格的室内支路/环线，全部接旧主路。厨房环线不是单向解锁机关。',
            '', '| 新路线 | 独立步点 | 最低照明代理值 |','|---|---:|---:|']
    for r in light['newRoutes']:lines.append(f'| {r["name"]} | {r["after"]["samples"]} | {r["after"]["minimum"]} |')
    lines+=['','原路线同算法前后没有变暗；新路线无零代理值，最低4。保守整格遮挡，不含天空光/反射，不能代替游戏光照或刷怪验收。',
            '', '## 尚未交付','','未设置床的重生点、桶内物品、书本实体或文字；原版书架仅为外观。正式S1/S2/S3机关、其余房间叙事和最终全堡施工/NBT/实机验收仍未完成。',
            '', '没有浏览器交互或游戏测试，图片是原版方块模型裁切图，不是游戏截图。']
    (OUT/'内饰施工与材料.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text(f'# V13生活与藏谱内饰\n\n打开 `{TITLE}`。4处场景、14组家具、5处室内栏杆开口，附5条新通路和逐层方块图。\n\n先看床位/厨房近景，再看藏谱上下层剖视与路线图；剖去的墙/屋顶仅为了展示，完整JSON仍保留。\n\n发送整个interior_v13文件夹给朋友，6张PNG不能漏。无需Python或网页服务，旧版链接需要保留light_v12目录。\n\n木床不是功能床，桶内/熔炉未配置内容；不是已完成全部内饰/捷径。无新版NBT，无真实存档修改，无浏览器/游戏测试。\n',encoding='utf-8')
    for p in files:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))]
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
