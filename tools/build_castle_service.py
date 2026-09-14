"""V15 persisted full castle, explicit excavation delta and off-line build guide."""
import hashlib
import json
from collections import Counter
from castle_detail import ROOT,read_model
from castle_service import service_castle,service_variant,service_isolation,stair_profile
from castle_front import route_cells
from castle_finish import EMISSION,spread_light
from build_craft_integration import encode
from vanilla_mesh import VanillaAssets,JAR

OUT=ROOT/'castle_v3/service_v15'
TITLE='余响堡_V15庭院下维修捷径.html'
REGIONS=[
 dict(name='庭院入口与下行楼梯',region=[52,59,0,23,38,59],layer=16,note='向北下降15格；三格宽。屋顶不是通路，图中剖切不能照着拆。'),
 dict(name='石闩、拉杆与独立线槽',region=[52,61,0,8,24,37],layer=5,note='拉杆在北侧Z26，石闩Z32；默认关闭。末线向西拐入中继器。'),
 dict(name='低层维修道与高桥接口',region=[52,59,0,7,4,24],layer=2,note='低层地板Y1；Z6只开有连续地板的三格口，两端栏杆保留。')]


def lighting(before,after,routes,floors):
    fields={k:spread_light(b,{p:EMISSION[s[0]] for p,s in b.items() if s[0] in EMISSION}) for k,b in [('before',before),('after',after)]}
    old={(x,y+1,z) for r in routes for x,y,z in route_cells(r['points'],r['width'])}
    samples={(x,y+1,z) for x,y,z in floors if (x,y+1,z) not in after}
    def stats(f,ps):
        vs=[f.get(p,0) for p in ps]
        return dict(samples=len(vs),minimum=min(vs),mean=round(sum(vs)/len(vs),2),zero=sum(v==0 for v in vs))
    return dict(oldBefore=stats(fields['before'],old),oldAfter=stats(fields['after'],old),newRoute=stats(fields['after'],samples),
                dimmerSamples=[dict(pos=p,before=fields['before'].get(p,0),after=fields['after'].get(p,0)) for p in sorted(old) if fields['after'].get(p,0)<fields['before'].get(p,0)],
                samples=[dict(pos=p,light=fields['after'].get(p,0)) for p in sorted(samples)],
                excludedJambFloorSamples=sorted({(x,y+1,z) for x,y,z in floors}-samples),
                method='只用建筑光源的保守六邻域代理，异形不透明块按整格遮挡；不计红石火把、天空光、反射和真实更新，不是游戏防刷怪验收。')


def material_counts(before,after,changed):
    place=Counter(after[p][0] for p in changed if p in after)
    remove=Counter(before[p][0] for p in changed if p in before)
    states=[p for p in sorted(changed) if p in before and p in after and before[p][0]==after[p][0]]
    items=Counter();recover=Counter()
    for p in changed:
        if p in states:continue
        if p in before:recover[before[p][0]]+=1
        if p not in after:continue
        n=after[p][0]
        if n=='piston_head':continue
        n={'redstone_wire':'redstone','redstone_wall_torch':'redstone_torch'}.get(n,n)
        items[n]+=1
    return dict(placeBlocks=place,removeBlocks=remove,placeItems=items,dismantleBlocks=recover,stateOnlyPositions=states,
                note='相对已有V14的增量，非全堡采购单。活塞头由活塞生成，不是可采购物品；7格线用7份红石粉，墙火把用红石火把物品。栏杆仅连接状态变化，不重复买。拆下数按块格，不保证工具/玩法下的掉落。')


def main():
    m=service_castle();d=m['data'];b=m['before'];a=m['after'];c=m['shortcut'];OUT.mkdir(exist_ok=True)
    assets=VanillaAssets();names={**d['names'],'sticky_piston':'黏性活塞','piston_head':'活塞头（自动生成）','redstone_wall_torch':'墙式红石火把','redstone_torch':'红石火把','redstone':'红石粉','redstone_wire':'红石线','repeater':'红石中继器','lever':'拉杆'};colors=dict(d['colors'])
    opened=service_variant(a,c,True)
    overlay=[dict(pos=p,before=a.get(p),after=opened.get(p)) for p in sorted(set(a)|set(opened)) if a.get(p)!=opened.get(p)]
    states={(s[0],tuple(sorted(s[1].items()))) for model in(a,opened) for s in model.values() if s[2] in ('shell','terrain')}
    for n,p in sorted(states):assets.elements(n,p);colors[n]=assets.swatch(n,p)
    sources=[ROOT/'castle_v3/shortcuts_v14/castle_v14.json',*sorted((ROOT/'nbt_save').glob('*.nbt'))]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    delta=[dict(pos=p,before=b.get(p),after=a.get(p)) for p in sorted(m['changed'])]
    materials=material_counts(b,a,m['changed']);light=lighting(b,a,d['routes'],m['floorCells'])
    assert not light['dimmerSamples'] and light['newRoute']['minimum']>=5
    report=dict(version='V15',date='2026-09-13',target='26.3-snapshot-9',dataVersion=5011,totalBlocks=len(a),
                changedCoordinates=len(delta),added=sum(v['before'] is None for v in delta),removed=sum(v['after'] is None for v in delta),replaced=sum(v['before'] is not None and v['after'] is not None for v in delta),
                ordinaryRoutes=len(d['routes']),gatedRoutes=3,noteBlocks=sum(s[0]=='note_block' for s in a.values()),musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in a.values()),
                lightBlocks=sum(s[0] in EMISSION for s in a.values()),modelStatesChecked=len(states),sourceHashes=hashes,targetJarSHA256=hashlib.sha256(__import__('pathlib').Path(JAR).read_bytes()).hexdigest(),
                size=d['size'],designMin=d['report']['designMin'],designMax=d['report']['designMax'],newNBT=False,inGameTest=False,browserTest=False,default='all three shortcuts closed')
    features=[dict(name=f['name'],region=f['region'],note=f['note'],kind='service_v15') for f in REGIONS]
    meta=dict(shortcut=c,regions=REGIONS,features=features,fixtures=m['fixtures'],floorCells=m['floorCells'],stairCells=m['stairCells'],railEnds=m['railEnds'],roofPreserved=m['roofPreserved'],
              replacedPositions=sorted(m['replaceable']),isolation=service_isolation(b,a),stairProfile=stair_profile(a),
              assumptions='默认玩家0.6×1.8，普通触及4.5。距离下界仅针对关闭闩南侧直走入口，不含爬行、飞行、搭拆方块或服务器属性。图和状态覆盖不是Minecraft运行。')
    full={**d,**encode(a,d['offset']), 'names':names,'colors':colors,'report':report,'features':d['features']+features,'fixtures':d['fixtures']+m['fixtures'],'serviceV15':meta,'featureProvenance':d['featureProvenance']+' V15 service underpass and inverted stone latch.'}
    def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    write('castle_v15.json',full);assert read_model(OUT/'castle_v15.json')[1]==a
    for n,v in [('v15_changes.json',delta),('机关与通路.json',meta),('开启状态覆盖.json',overlay),('材料增减.json',materials),('照明代理.json',light),('validation.json',report)]:write(n,v)
    # One complete local envelope, not sparse feature-only occupancy: air is meaningful.
    neighborhood={p:s for p,s in a.items() if 51<=p[0]<=62 and -1<=p[1]<=24 and 3<=p[2]<=60}
    payload=dict(**encode(neighborhood,d['offset']),offset=d['offset'],names=names,colors=colors,meta=meta,report=report,changes=delta,overlay=overlay,materials=materials,lighting=light)
    (OUT/TITLE).write_text((ROOT/'tools/castle_service_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
    lines=['# V15 庭院下维修捷径施工','',f'完整模型{len(a):,}格；本轮{len(delta)}坐标变化（加{report["added"]} / 拆{report["removed"]} / 换{report["replaced"]}）。不改音乐、地表、旧43普通路线或S1/S2。原模型与NBT保留，未修改游戏。','',
           '## 先定位与开挖','',
           '全部使用设计坐标；先选服务器世界中设计原点O，世界坐标=设计坐标+O。文件offset仅索引偏移，不要另加一次。以下按已有V14施工；从零建全堡的采购包仍待后续。',
           '1. 先核对高端(55,16,58)庭院路与低端(55,1,5)音乐门厅高桥。X54…56为三格路幅，南(+Z)高、北(-Z)低。不要移动音乐机器来迁就新道。',
           '2. 沿下表先搭连续地板/楼梯及图内承托，再清理其上三格空气。只拆差异JSON标明的旧块，不要执行宽泛fill清空。三格路幅以外旧墙、旧表皮、屋顶和灯全部保留。',
           '3. 同高地板确认后，分别拆X54…56/Y17/Z56的三格庭院栏杆、X54…56/Y2/Z6的三格高桥栏杆；X53/57端栏杆保留并连接新侧墙。',
           '4. 下降15格采用45个朝南、下半、straight的平滑砂岩楼梯；每级的具体坐标见表。上/下出口不是跳台。','',
           '| Z 范围 | 地板Y | 方块 |','|---|---:|---|','| 58…55 | 16 | 原同高地面/补凝灰岩砖 |']
    for z in range(54,39,-1):lines.append(f'| {z} | {z-38} | X54、55、56各1个朝南下半平滑砂岩楼梯 |')
    lines+=['| 39…5 | 1 | 原地板优先，缺口补凝灰岩砖 |','','## 墙、雨棚与照明','',
            '按逐层页保留原块，补X53/57暖泥砖侧墙与切制砂岩侧龛、半砖压顶。楼梯上方保持三格空气；局部原装饰保护区的屋顶保持旧状态。雨棚两根木柱(53/57,17…20,55)，Y20横梁，深板岩楼梯山形屋顶最高Y23。不拆渲染剖面省略的外墙。',
            '六个灯龛都在X53、Z=10/18/26/36/44/51，按当地地板h在Y=h+1放切制砂岩托座、Y=h+2放落地灯笼。灯具完整坐标见页面和机关与通路JSON。建筑光源总518（不把红石火把计入）。','',
            '## 石闩：先看施工顺序，再看默认关闭图','',
            '1. 按逐层图搭Z32两侧X54/56、Y2…4实心门柱和顶吊座。中心(55,2,32)始终留空，Y3/Y4是运动区，不塞装饰。先不放活塞和闩石。',
            '2. 拉杆座A=(58,3,26)，在其西面(57,3,26)装墙拉杆，facing=west。站支撑格(55,1,26)操作。A及导线下方都用所列实心导电满块，不能用半砖替代。',
            '3. 按下表铺7格线；爬坡低线头上(59,4,26)、(59,5,27)必须留空。末线W7向北和向西连，南/东不连。',
            '4. (58,5,32)放1档中继器，facing=east：输入东、输出西。(57,5,32)放切制砂岩，西面(56,5,32)放西向墙红石火把。不要把火把插到活塞上。',
            '5. 先拨拉杆到开启输入ON，确认火把熄灭并稳定，再在(55,5,32)放向下的黏性活塞（抬头放置并以F3核对down），在(55,4,32)放1块雕纹砂岩，Y3留空。',
            '6. 拨回OFF并等待完整伸出：Y4自动成为sticky/short=false/down活塞头，石移到Y3。活塞头不需要、也不能作为普通材料手放。这才是默认关闭图。',
            '7. 从音乐门厅侧拨ON：石回到Y4，Y3清空，闩口净宽1、净高2，可双向返回庭院。普通走廊仍三格宽；不要把门柱位置也算三宽通路。','',
            '| 顺序 | 红石线坐标 | ON时稳态强度 |','|---|---|---:|']
    for i,p in enumerate(c['wire']):lines.append(f'| {i+1} | {p} | {15-i} |')
    lines+=['','每次切换等火把、活塞和石块完全稳定（正常20TPS下建议人为隔约1秒）。快速短脉冲可能吐块、频繁操作可能烧火把。本机关不是快速时钟，也不是永久解锁。别站闩下关门。','',
            '## 本轮增量物品','',materials['note'],'','| 材料 | 需放置物品数量 |','|---|---:|']
    for n,count in items_sorted(materials['placeItems']):lines.append(f'| {names.get(n,n)} `{n}` | {count} |')
    lines+=['','回收数量和仅调整连接的栏杆坐标见材料增减JSON。物品数没有扣减可回收旧料，便于先备料；不是最终全堡数量。','',
            '## 静态检查与游戏内待验','',
            f'指定旧路77段→捷径53段，按登记图计边，非秒数。新路线照明代理最低{light["newRoute"]["minimum"]}、无零值，旧43普通路线无变暗；不等于游戏夜间或防刷怪验收。',
            '关闭时只留1格高，能挡普通站立/蹲伏，不能保证挡爬行、飞行或搭拆块。关闭南侧指定入口到整个拉杆格的轴向距离下界6.3，按4.5交互假设不可直接触及；不是全区域防绕过或权限设施。',
            '静态核查含：三格宽楼梯地板与三格净空、每半格表面最大0.5高差、石闩0.6×1.8人物连续扫掠、两稳态开关回环、上坡线与中继器方向、整条输入/输出/QC邻域隔离。没有完整楼梯动力学或Minecraft事件仿真。',
            '必须在独立创造测试区执行关闭→沿旧路到拉杆→开启→两方向上/下楼梯和穿闩→关闭→再开；开、关两个稳态各保存重进，复查状态后再循环。检查雨棚/栏杆防跌落、灯、区块加载和邻居更新；开启机关时完整试听原曲。',
            '原曲音符盒2,307、音乐/控制32,260格保持；无新版NBT，无真实存档修改，无浏览器交互/游戏验收。其余房间内饰、最终统一施工/采购包与NBT仍待继续。']
    (OUT/'施工与材料.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text(f'# V15\n\n打开 `{TITLE}`；先看上下层关系，再看石闩开关与接线，最后按逐层图施工。\n\n分享整个service_v15目录及4张PNG，无需Python或联网。上级历史/研究链接需保留对应文件。只有JSON设计，不能当NBT导入。\n\n实际游戏检查和最终全堡施工包仍待完成。\n',encoding='utf-8')
    for p in sources:assert hashes[str(p.relative_to(ROOT))]==hashlib.sha256(p.read_bytes()).hexdigest()
    print(json.dumps(report,ensure_ascii=False),flush=True)


def items_sorted(items):return sorted(items.items(),key=lambda kv:(-kv[1],kv[0]))


if __name__=='__main__':main()
