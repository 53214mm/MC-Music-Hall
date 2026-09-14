"""Publish a V19 review sample; do not update the V18 purchase or NBT bundle."""
import hashlib
import json
from collections import Counter
from castle_facade_v19 import facade_v19,OUT,TITLE,SOURCE
from castle_detail import ROOT
from build_craft_integration import encode
from castle_release import item_cost
from vanilla_mesh import VanillaAssets

def dump(name,obj):
    path=OUT/name;text=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
    if not path.exists() or path.read_text(encoding='utf-8')!=text:path.write_text(text,encoding='utf-8')


def viewer_neighborhood(blocks,views,features):
    regions=[v['region'] for v in views]+[f['region'] for f in features]
    return {p:s for p,s in blocks.items() if any(all(r[2*i]-1<=p[i]<=r[2*i+1]+1 for i in range(3)) for r in regions)}

def main():
    m=facade_v19();b=m['before'];a=m['after'];d=m['data'];OUT.mkdir(exist_ok=True)
    changes=[dict(pos=p,before=b.get(p),after=a.get(p)) for p in sorted(m['changed'])]
    placed=Counter();removed=Counter();states=[]
    for v in changes:
        if v['before'] and v['after'] and v['before'][0]==v['after'][0]:states.append(v['pos']);continue
        if v['after']:placed.update(item_cost(v['after'][0],v['after'][1]))
        if v['before']:removed.update(item_cost(v['before'][0],v['before'][1]))
    materials=dict(placeItems=placed,dismantleItems=removed,stateOnlyPositions=states,note='相对已有V17/V18的增量成品物品，不是全堡采购表。同种材料仅调朝向/连接不重复购买，未扣旧料回收和损耗。')
    assets=VanillaAssets();colors=dict(d['colors']);newstates={(a[p][0],tuple(sorted(a[p][1].items()))) for p in m['changed'] if p in a}
    for n,pr in newstates:assets.elements(n,pr);colors[n]=assets.swatch(n,pr)
    report=dict(version='V19',source='V17 (V18 exact model)',sourceHash=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        target='26.3-snapshot-9',dataVersion=5011,totalBlocks=len(a),changedCoordinates=len(changes),
        added=sum(v['before'] is None for v in changes),removed=sum(v['after'] is None for v in changes),replaced=sum(v['before'] is not None and v['after'] is not None for v in changes),
        features=len(m['features']),routes=53,shortcuts=3,musicBlocks=32260,noteBlocks=2307,oldLightBlocks=539,newLights=2,lightBlocks=541,
        checkedChangedStates=len(newstates),designMin=d['report']['designMin'],designMax=d['report']['designMax'],
        newNBT=False,browserTest=False,inGameTest=False)
    meta=dict(features=m['features'],fixtures=m['fixtures'],blindBacks=m['blindBacks'],roofJoins=m['roofJoins'])
    full={**d,**encode(a,d['offset']),'colors':colors,'facadeV19':meta,'report':report,
          'features':d['features']+m['features'],'fixtures':d['fixtures']+m['fixtures'],'featureProvenance':d['featureProvenance']+' V19 bounded north/east facade sample, not a new NBT release.'}
    dump('castle_v19.json',full);dump('v19_changes.json',changes);dump('增量材料.json',materials);dump('validation.json',report);dump('构件与接坡.json',meta)
    views=[dict(name='北墙全立面（X横向/Z厚度）',region=[0,51,-9,74,-49,-38],layer=38),
           dict(name='中央山墙与交接屋面',region=[14,38,48,74,-47,-18],layer=59),
           dict(name='东侧扶壁与檐口',region=[53,65,-9,54,-37,-10],layer=26)]
    needed=viewer_neighborhood(a,views,m['features'])
    payload=dict(**encode(needed,d['offset']),offset=d['offset'],names=d['names'],colors=colors,views=views,features=m['features'],report=report,changes=changes,materials=materials)
    template=(ROOT/'tools/castle_facade_v19_viewer.html').read_text(encoding='utf-8')
    (OUT/TITLE).write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
    guide=['# V19 北墙与转角样板','', '只是一轮样板审阅，V18整包不改，不要把旧采购表当成新版，也没有V19 NBT。世界坐标=设计坐标+同一个O；不另加offset。','',
           f'相对V17/V18改{len(changes):,}处，新增{report["added"]:,}、拆除{report["removed"]:,}、替换{report["replaced"]:,}。完整候选模型{len(a):,}格。音乐、两扇北窗、全部旧构件/通路/机关/灯和地表保持。','',
           '先基脚与扶壁，再做凸跨/盲拱/腰线；再从原坡屋面往外接新山墙和老虎窗，最后装细柱与斜边。新装饰不是可行走的屋面，尚未验证防跌落。盲龛不穿透内墙；阁楼窗是封闭造景，不新增可进入房间。','']
    for f in m['features']:guide.extend([f'## {f["name"]}','',f['note'],'',f['build'],'',f'范围：{f["region"]}（X最小/最大、Y最小/最大、Z最小/最大）。',''])
    guide+=['## 增量备料','',materials['note'],'','| 成品物品 | 放置数量 | 拆下理论数量 |','|---|---:|---:|']
    for n in sorted(set(placed)|set(removed),key=lambda n:-placed[n]):guide.append(f'| {d["names"].get(n,n)} `{n}` | {placed[n]} | {removed[n]} |')
    guide+=['','实际回收取决于工具/附魔，未扣复用。仅更新连接的坐标另列增量材料JSON。','',
            '图为实际方块模型与纹理离线绘制，非游戏截图。未做浏览器交互/方块自动更新/真实照明/全曲试听。本轮原539个灯位不变，另加2盏壁柱灯（共541个光源），几何改变仍需核对光照。确认外观后，再将认可的部分同步到全堡采购与NBT。']
    (OUT/'样板施工说明.md').write_text('\n'.join(guide)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
