"""Saved V17 model, increment manifest and self-contained offline drawings."""
import hashlib
import json
from castle_detail import ROOT,read_model
from castle_watchrooms import watchrooms,watch_lighting,ZONES
from castle_finish import EMISSION
from build_craft_integration import encode
from build_castle_story_rooms import materials
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/watch_v17'
TITLE='余响堡_V17水痕与守望.html'
VIEWS=[dict(name='旧蓄水池西壁与检水角',region=[-43,-23,-13,-3,33,55],layer=-11),
       dict(name='烽塔观景台与原登塔口',region=[-61,-43,75,87,-51,-35],layer=84),
       dict(name='冠塔抄谱桌',region=[-12,1,63,70,-27,-12],layer=65),
       dict(name='北阶塔换岗角',region=[-30,-18,47,54,-55,-45],layer=49),
       dict(name='维修塔巡检阁及一阶接入',region=[62,74,53,61,-2,16],layer=55)]


def main():
    m=watchrooms();d=m['data'];b=m['before'];a=m['after'];light=watch_lighting();OUT.mkdir(exist_ok=True)
    assert not light['dimmerSamples'] and all(r['after']['zero']==0 for r in light['newRoutes'])
    assets=VanillaAssets();colors=dict(d['colors']);names={**d['names'],'cauldron':'炼药锅（空检水盆）','mossy_stone_bricks':'苔石砖',
        'tuff_brick_slab':'凝灰岩砖台阶','tuff_brick_stairs':'凝灰岩砖楼梯','spruce_slab':'云杉木台阶'}
    states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in('shell','terrain')}
    for n,p in sorted(states):assets.elements(n,p);colors[n]=assets.swatch(n,p)
    source=[ROOT/'castle_v3/story_v16/castle_v16.json',*sorted((ROOT/'nbt_save').glob('*.nbt'))]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source}
    delta=[dict(pos=p,before=b.get(p),after=a.get(p)) for p in sorted(m['changed'])];mat=materials(b,a,m['changed'])
    mat['note']=mat['note'].replace('V15','V16')
    report=dict(version='V17',date='2026-09-13',source='story_v16/castle_v16.json',target='26.3-snapshot-9',dataVersion=5011,
        totalBlocks=len(a),changedCoordinates=len(delta),added=sum(v['before'] is None for v in delta),removed=sum(v['after'] is None for v in delta),
        replaced=sum(v['before'] is not None and v['after'] is not None for v in delta),newFeatures=len(m['features']),newRoutes=len(m['routes']),oldRoutes=len(d['routes']),routes=len(d['routes'])+len(m['routes']),
        lightBlocks=sum(s[0] in EMISSION for s in a.values()),newLights=len(m['fixtures']),noteBlocks=sum(s[0]=='note_block' for s in a.values()),musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in a.values()),
        modelStatesChecked=len(states),sourceHashes=hashes,size=d['size'],designMin=d['report']['designMin'],designMax=d['report']['designMax'],newNBT=False,browserTest=False,inGameTest=False)
    meta=dict(zones=ZONES,views=VIEWS,features=m['features'],fixtures=m['fixtures'],routes=m['routes'],openings=m['openings'],
        railUpdates=[dict(pos=p,state=s) for p,s in sorted(m['railUpdates'].items())],replacedPositions=sorted(m['changed']&set(b)),watermarks=sorted(m['watermarks']),
        lookoutFloor=sorted(m['lookoutFloor']),sightlines=m['views'],content='无活动水/火焰/新电路；空讲台/桶/炼药锅，不预装乐谱或道具，椅子为楼梯造景。')
    full={**d,**encode(a,d['offset']),'colors':colors,'names':names,'report':report,'routes':d['routes']+m['routes'],'features':d['features']+m['features'],
          'fixtures':d['fixtures']+m['fixtures'],'watchV17':meta,'featureProvenance':d['featureProvenance']+' V17 dry cistern and tower watchrooms.'}
    def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    write('castle_v17.json',full);assert read_model(OUT/'castle_v17.json')[1]==a
    for n,v in [('v17_changes.json',delta),('房间通路与视线.json',meta),('材料增减.json',mat),('照明代理.json',light),('validation.json',report)]:write(n,v)
    wanted=set()
    for f in VIEWS:
        r=f['region'];wanted.update((x,y,z) for x in range(r[0],r[1]+1) for y in range(r[2],r[3]+1) for z in range(r[4],r[5]+1))
    payload=dict(**encode({p:a[p] for p in wanted if p in a},d['offset']),offset=d['offset'],names=names,colors=colors,meta=meta,report=report,changes=delta,materials=mat,lighting=light)
    # Reuse only the established grid interaction and style, not V16 narrative.
    base=(ROOT/'tools/castle_story_rooms_viewer.html').read_text(encoding='utf-8')
    template=(ROOT/'tools/castle_watchrooms_viewer.html').read_text(encoding='utf-8').replace('__STYLE__',base.split('<style>')[1].split('</style>')[0])
    template=template.replace('__SCRIPT__',base.split('<script>')[1].split('</script>')[0])
    (OUT/TITLE).write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
    lines=['# V17 水痕与守望施工','',f'完整模型{len(a):,}格；相对V16改{len(delta)}处，加{report["added"]}、拆{report["removed"]}、换{report["replaced"]}。',
        '', '所有坐标为设计坐标；世界坐标=设计坐标+服务器设计原点O，JSON offset只是索引，不再另加。',
        '', '## 施工顺序','',
        '1. 保留V16音乐、48条普通路线与三机关。先核对Y76烽塔旧板、Y55维修塔原板及旧灯，不扩大清空。',
        '2. 烽塔先立柱/梁/平台，再做两段木梯、梯边护挡和低铁栏；平台未围护前不要在生存里跑动。原Y76路线的Y77…79三格空气严禁填入。',
        '3. 维修塔从原(63,54,14)走到(64,54,13)，将(65,55,13)改东向下半楼梯接入塔内Y55楼板；Z14上方旧塔墙保留。',
        '4. 北阶塔唯一栏杆口(-22,49,-49)，先确认周围同高地板，再拆并按差异调整两邻收头。其余塔内家具/灯均在原楼板上。',
        '5. 地下只换指定西壁潮痕与16格木补板，再搭堵塞格栅/低石屑和检水角。炼药锅空置，不加水，不挖通背墙。',
        '', '## 逐组搭法','']
    for f in m['features']:lines += [f'### {ZONES[f["zone"]]} / {f["name"]}','',f['note'],'',f['build'],'',f'范围：X{f["region"][0]}…{f["region"][1]} / Y{f["region"][2]}…{f["region"][3]} / Z{f["region"][4]}…{f["region"][5]}。具体状态见HTML逐层格。','']
    lines+=['## 观景定位','', '站在设计地板(-57,84,-40)，脚底Y85、按普通站姿眼高约86.62计算。从这里到东门塔(-28,60,104)屋冠与唱诗堂(7,55,71)屋脊上方的保守占用格射线无阻挡。视线说明不是游戏截图，也不保证服务器额外树木/建筑不会挡住。铁栏是一格高，不换成1.5格高的墙/栅栏。','',
        '## 增量材料','',mat['note'],'','| 物品 | 放置数量 |','|---|---:|']
    for n,v in sorted(mat['placeItems'].items(),key=lambda kv:-kv[1]):lines.append(f'| {names.get(n,n)} `{n}` | {v} |')
    lines+=['','拆下、复用及仅调连接数量见材料增减JSON；未扣工具/玩法决定的回收物。这里不是全堡最终采购单。','',
        '## 待实机验证','', '核对阶梯实际半格步进/转弯/双向行走、梯边防平走跌落、墙和铁栏更新、砂轮与灯的支撑、旧机关开关与两稳态保存重进。旧路光照代理未变暗；五新路最低分别6/4/6/8/6，不代表真实防刷怪。',
        '塔楼/地下叙事场景已落块；全堡统一施工/采购/NBT包与独立创造档全曲试听、全路线/夜间照明/机关验收仍需继续。无新版NBT，无真实世界修改。']
    (OUT/'施工顺序与增量材料.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text(f'# V17 水痕与守望\n\n打开 `{TITLE}`。整个watch_v17目录和七张PNG一起发给朋友，无需Python/联网；历史链接需保留上级story_v16等目录。\n\n这是实际方块施工数据和离线配图，不是游戏实测或最终全堡材料/NBT包。\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
