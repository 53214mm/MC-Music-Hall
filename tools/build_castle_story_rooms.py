"""V16 complete model + room-sized offline construction drawings."""
import hashlib
import json
from collections import Counter
from castle_detail import ROOT,read_model
from castle_story_rooms import story_rooms,story_lighting,ZONE_NAMES
from castle_finish import EMISSION
from build_craft_integration import encode
from vanilla_mesh import VanillaAssets

OUT=ROOT/'castle_v3/story_v16'
TITLE='余响堡_V16空席与守曲人工坊.html'
VIEWS=[dict(name='唱诗堂长席',region=[-7,21,16,20,58,79],layer=17),
       dict(name='后殿纪念龛与独席',region=[7,19,17,27,79,86],layer=18),
       dict(name='维修工作夹廊',region=[65,75,13,23,39,53],layer=17)]


def materials(before,after,changed):
    placed=Counter(after[p][0] for p in changed if p in after);removed=Counter(before[p][0] for p in changed if p in before)
    state_only=[p for p in sorted(changed) if p in before and p in after and before[p][0]==after[p][0]]
    items=Counter();dismantle=Counter()
    for p in changed:
        if p in state_only:continue
        if p in before:dismantle[before[p][0]]+=1
        if p not in after:continue
        n=after[p][0]
        if n=='potted_oxeye_daisy':items['flower_pot']+=1;items['oxeye_daisy']+=1
        else:items[n]+=1
    return dict(placeBlocks=placed,removeBlocks=removed,placeItems=items,dismantleBlocks=dismantle,stateOnlyPositions=state_only,
                note='按已有V15计算的增量，不是全堡采购单；同种方块仅调方向/连接不重复购买。雏菊盆栽由1花盆+1滨菊组成；旧料实际掉落取决于工具与玩法，数量未扣可回收材料。')


def main():
    m=story_rooms();d=m['data'];b=m['before'];a=m['after'];light=story_lighting();OUT.mkdir(exist_ok=True)
    assert not light['dimmerSamples'] and all(r['after']['zero']==0 for r in light['newRoutes'])
    assets=VanillaAssets();colors=dict(d['colors']);names={**d['names'],'lectern':'讲台（空谱架）','grindstone':'砂轮','smithing_table':'锻造台',
        'potted_oxeye_daisy':'滨菊盆栽','flower_pot':'花盆','oxeye_daisy':'滨菊','waxed_weathered_cut_copper':'涂蜡锈蚀切制铜块',
        'waxed_weathered_cut_copper_slab':'涂蜡锈蚀切制铜台阶','waxed_weathered_cut_copper_stairs':'涂蜡锈蚀切制铜楼梯','smooth_sandstone_slab':'平滑砂岩台阶'}
    states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in('shell','terrain')}
    for n,p in sorted(states):assets.elements(n,p);colors[n]=assets.swatch(n,p)
    source=[ROOT/'castle_v3/service_v15/castle_v15.json',*sorted((ROOT/'nbt_save').glob('*.nbt'))]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source}
    delta=[dict(pos=p,before=b.get(p),after=a.get(p)) for p in sorted(m['changed'])]
    mat=materials(b,a,m['changed'])
    report=dict(version='V16',date='2026-09-13',source='service_v15/castle_v15.json',target='26.3-snapshot-9',dataVersion=5011,
                totalBlocks=len(a),changedCoordinates=len(delta),added=sum(v['before'] is None for v in delta),removed=sum(v['after'] is None for v in delta),
                replaced=sum(v['before'] is not None and v['after'] is not None for v in delta),newFeatures=len(m['features']),newRoutes=len(m['routes']),oldRoutes=len(d['routes']),routes=len(d['routes'])+len(m['routes']),
                lightBlocks=sum(s[0] in EMISSION for s in a.values()),newLights=len(m['fixtures']),noteBlocks=sum(s[0]=='note_block' for s in a.values()),musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in a.values()),
                modelStatesChecked=len(states),sourceHashes=hashes,size=d['size'],designMin=d['report']['designMin'],designMax=d['report']['designMax'],newNBT=False,browserTest=False,inGameTest=False)
    meta=dict(zones=ZONE_NAMES,views=VIEWS,features=m['features'],fixtures=m['fixtures'],routes=m['routes'],openings=m['openings'],
              railUpdates=[dict(pos=p,state=s) for p,s in sorted(m['railUpdates'].items()) if s!=b.get(p)],
              replacedPositions=sorted(m['changed']&set(b)),oldChairs=sorted(m['chairs']),oldTable=sorted(m['oldTable']),
              content='讲台has_book=false；桶/砂轮/锻造台没有预装物品、乐谱或燃料。备用金属件是形制呼应，不会发声。')
    full={**d,**encode(a,d['offset']),'colors':colors,'names':names,'report':report,'routes':d['routes']+m['routes'],'features':d['features']+m['features'],
          'fixtures':d['fixtures']+m['fixtures'],'storyV16':meta,'featureProvenance':d['featureProvenance']+' V16 choir and service mezzanine.'}
    def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    write('castle_v16.json',full);assert read_model(OUT/'castle_v16.json')[1]==a
    for n,v in [('v16_changes.json',delta),('房间与通路.json',meta),('材料增减.json',mat),('照明代理.json',light),('validation.json',report)]:write(n,v)
    wanted=set()
    for f in VIEWS:
        r=f['region'];wanted.update((x,y,z) for x in range(r[0],r[1]+1) for y in range(r[2],r[3]+1) for z in range(r[4],r[5]+1))
    payload=dict(**encode({p:a[p] for p in wanted if p in a},d['offset']),offset=d['offset'],names=names,colors=colors,meta=meta,report=report,changes=delta,materials=mat,lighting=light)
    (OUT/TITLE).write_text((ROOT/'tools/castle_story_rooms_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
    lines=['# V16 空席与守曲人工坊施工','',f'实际全模型{len(a):,}格；相对V15改{len(delta)}处，加{report["added"]}、拆{report["removed"]}、换{report["replaced"]}。原音乐/旧路/三机关保持，旧模型和源NBT不改。','',
           '全部是设计坐标；在服务器选定设计(0,0,0)的世界位置O，再以设计坐标+O施工。JSON offset仅用于索引，不另加到服务器坐标。','',
           '## 推荐顺序','',
           '1. 核对V15地板、灯柱和栏杆，先搭维修平台横梁/托臂与Y16木板、端部护栏。保留所有旧灯座，不要把平台下方空间填实。',
           '2. 检查每个下列开口的脚下与四邻均有同高完整地板，再拆旧栏杆并调整端头。新增路线是正常行走支路/环线，不加入门锁。',
           '3. 只拆旧14把零散椅和原X71/72、Y17/18、Z45…48厚工台（16格）。准确复用/替换/删除以差异表为准，不扩大清空。',
           '4. 放长席、端灯、侧后殿纪念龛和独席，再建维修薄工台和零件架。讲台默认空，砂轮与锻造台不预填物品。',
           '5. 检查10盏灯各有实心或上半台阶顶面支撑；盆栽需先放花盆再右键放入1朵滨菊。','',
           '## 逐组搭法','']
    for f in m['features']:
        lines += [f'### {ZONE_NAMES[f["zone"]]} / {f["name"]}','',f['note'],'',f['build'],'',
                  f'范围：X{f["region"][0]}…{f["region"][1]} / Y{f["region"][2]}…{f["region"][3]} / Z{f["region"][4]}…{f["region"][5]}。具体每格及朝向看HTML。','']
    lines+=['## 八处同高开口','']+[f'- 拆旧栏杆 {p}；楼板先连续，端头状态按差异表。' for p in m['openings']]
    lines+=['','## 准确增量物品','',mat['note'],'','| 物品 | 放置数量 |','|---|---:|']
    for n,v in sorted(mat['placeItems'].items(),key=lambda kv:-kv[1]):lines.append(f'| {names.get(n,n)} `{n}` | {v} |')
    lines+=['','拆下方块格和仅调整连接/朝向的格子详见材料增减JSON。源NBT不是新版城堡；不要往服务器覆盖包含空气的大结构。','',
            '## 路线与光照代理','', '| 新路线 | 采样点 | 最低代理 |','|---|---:|---:|']
    for r in light['newRoutes']:lines.append(f'| {r["name"]} | {r["after"]["samples"]} | {r["after"]["minimum"]} |')
    lines+=['','旧43普通路线和三条捷径采样均没有变暗。总建筑光源528；代理不含天空光、反射、真实更新，不是游戏防刷怪结论。','',
            '## 游戏内待验','',
            '在独立创造档走入左右席间、后殿独席与维修夹廊；核对三格净高、栏杆开口与端头、平台下方空间、灯具和花盆支撑。部分墙连接与活板门姿态会随实际放置更新，要在目标版本核对，不能把离线渲染当实机截图。',
            '三处捷径继续分别检查关→开→双向通过→再关、两稳态保存重进；完整播放原曲检查误触/音区与照明。此轮没有跑Minecraft，也没有生成新版NBT。',
            '剩余：蓄水池与塔楼叙事场景、全堡统一手建/采购/NBT包及隔离创造档验收。空讲台、桶、图中的普通纹理都不代表已经有可读乐谱或道具。']
    (OUT/'内饰施工与材料.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text(f'# V16\n\n打开 `{TITLE}`。先看整厅对照，再看纪念龛/工台与夹廊剖面，最后按逐层图施工。\n\n发送整个story_v16目录及6张PNG，无需Python或联网。回看V15需保留上级service_v15目录。不是最终全堡采购单，没有新版NBT或游戏验收。\n',encoding='utf-8')
    for p in source:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))]
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
