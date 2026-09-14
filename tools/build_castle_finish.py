"""Publish the V6 material/light review without changing previous versions or saves."""
import json
import zipfile
from collections import Counter
from castle_finish import ROOT,finish_castle,COLORS,NAMES,EMISSION,spread_light,protected
from castle_front import route_cells
from castle_sample import validate_route

OUT=ROOT/'castle_v3/finish_v6'


def main():
    m=finish_castle();b=m['before'];a=m['after'];data=m['data'];OUT.mkdir(exist_ok=True)
    for r in data['routes']:
        ps=list(map(tuple,r['points']));assert not validate_route(a,ps),r['name']
        for p in route_cells(ps,r['width']):assert not validate_route(a,[p]),(r['name'],p)
    with zipfile.ZipFile(r'E:\PCL\PCL 正式版 2.8.12\.minecraft\versions\26.3-snapshot-9\26.3-snapshot-9.jar') as jar:
        for name in {s[0] for s in a.values()}:
            path=f'assets/minecraft/blockstates/{name}.json';assert path in jar.namelist(),name
            definitions=json.loads(jar.read(path))
            if 'variants' in definitions:
                allowed={}
                for variant in definitions['variants']:
                    for item in variant.split(','):
                        if '=' in item:
                            k,v=item.split('=');allowed.setdefault(k,set()).add(v)
                for n,props,g in set((s[0],tuple(sorted(s[1].items())),s[2]) for s in a.values() if s[0]==name):
                    for k,v in props:
                        if k in allowed:assert v in allowed[k],(name,k,v)
    low=[min(p[i] for p in a) for i in range(3)];high=[max(p[i] for p in a) for i in range(3)];offset=[-v for v in low]
    def encode(blocks):
        palette=[];lookup={};items=[]
        for p,(n,props,g) in sorted(blocks.items()):
            key=(n,tuple(sorted(props.items())),g)
            if key not in lookup:lookup[key]=len(palette);palette.append([n,props,g])
            items.append([*(p[i]+offset[i] for i in range(3)),lookup[key]])
        return dict(palette=palette,blocks=items)
    names={**data['names'],**NAMES};counts=Counter(s[0] for s in a.values());oldcounts=Counter(s[0] for s in b.values());lights=Counter({n:counts[n] for n in EMISSION if counts[n]})
    before_surface=Counter(b[p][0] for p in m['exposed']);after_surface=Counter(a[p][0] for p in m['exposed'])
    report=dict(totalBlocks=len(a),changedCoordinates=len(m['changed']),addedBlocks=len(a)-len(b),lightBlocks=dict(lights),oldLightBlocks=sum(oldcounts[n] for n in EMISSION),newLightBlocks=sum(lights.values()),fixtures=len(m['fixtures']),fixtureKinds=dict(Counter(f['kind'] for f in m['fixtures'])),beforeExposedMasonry=dict(before_surface),afterExposedMasonry=dict(after_surface),noteBlocks=counts['note_block'],routes=len(data['routes']),size=[high[i]-low[i]+1 for i in range(3)],designMin=low,designMax=high,gameTest=False,browserTest=False,newNBT=False)
    sources={p:EMISSION[s[0]] for p,s in a.items() if s[0] in EMISSION};field=spread_light(a,sources)
    coverage=[]
    for r in data['routes']:
        cells=sorted(route_cells(r['points'],r['width']));dark=[];minvalue=15
        for p in cells:
            v=field.get((p[0],p[1]+1,p[2]),0);minvalue=min(v,minvalue)
            if v==0:dark.append(p)
        coverage.append(dict(name=r['name'],cells=len(cells),proxyMin=minvalue,zeroCells=dark,zeroInProtected=sum(protected(p) for p in dark)))
    report['staticLightProxy']=dict(zeroCells=sum(len(r['zeroCells']) for r in coverage),zeroInProtected=sum(r['zeroInProtected'] for r in coverage),note='只检查已登记路线的脚部格。部分形状按整格遮光，无天空光；不是游戏亮度或防刷怪证明。')
    encoded=encode(a);payload=dict(**encoded,offset=offset,names=names,colors=COLORS,fixtures=m['fixtures'],report=report)
    complete={**payload,'routes':data['routes'],'connections':data['connections'],'size':report['size']}
    def write(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    write('castle_v6.json',complete);write('validation.json',report);write('灯具坐标.json',m['fixtures']);write('路线照明待验.json',coverage)
    write('finish_comparison.json',dict(before=encode(b),after=encoded,offset=offset,facadeExtras=[],report=report))
    write('v6_changes.json',[dict(pos=p,before=b.get(p),after=a.get(p)) for p in sorted(m['changed'])])
    template=(ROOT/'tools/castle_finish_viewer.html').read_text(encoding='utf-8')
    (OUT/'余响堡_V6材质与灯光.html').write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
    building=Counter(s[0] for s in a.values() if s[2]=='shell');terrain=Counter(s[0] for s in a.values() if s[2]=='terrain');music=counts-building-terrain
    lines=['# V6 材料与灯具','',f'当前共{len(a):,}个非空气方块。灯具是实际方块，不依赖红石开关、光影包或隐形光源。未生成新版NBT；这是审阅稿统计，不是已定稿采购承诺。','',f'原有发光方块{report["oldLightBlocks"]}个；现在{report["newLightBlocks"]}个。新增灯具组件{len(m["fixtures"])}组；一组吊灯含4盏灯笼，所以组件数不等于灯源数。','']
    lines+=['| 发光方块 | V5 | V6 | 净增 |','|---|---:|---:|---:|']+[f'| {names.get(n,n)} | {oldcounts[n]} | {counts[n]} | {counts[n]-oldcounts[n]} |' for n in lights]
    lines+=['','## 完整现状材料','', '| 材料 | 建筑 | 岩体 | 音乐与控制 | 合计 | 相比V5 |','|---|---:|---:|---:|---:|---:|']+[f'| {names.get(n,n)} | {building[n]} | {terrain[n]} | {music[n]} | {counts[n]} | {counts[n]-oldcounts[n]:+} |' for n in sorted(set(counts)|set(oldcounts),key=lambda n:-counts[n])]
    lines+=['','不含工具、脚手架、损耗。蛙明灯获取较费力，可把灯龛中的赭黄蛙明灯换成荧石作低成本备选，外观和本统计随之改变；音乐机任何底材、导线支撑与保护区不参与替换。','', '参考：[普通灯笼](https://www.minecraft.net/en-us/article/taking-inventory--lantern)、[蛙明灯](https://www.minecraft.net/de-de/article/block-month--froglight)。']
    (OUT/'材料与灯具.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    text=f'''# V6 材质与照明

入口：`余响堡_V6材质与灯光.html`。同目录三张PNG必须一起保留；不需要Python、联网或网页服务器。与朋友分享时发送整个finish_v6文件夹即可（回看V5的链接需要父目录一起发）。

## 改了什么

- 表面灰石采用成片安山岩、凝灰岩砖基座和切石窗框；生活翼以木架、方解石填墙，唱诗堂上部少量暖砂岩。屋面有深板岩砖修补片。隐藏实心结构不为了凑材料种类而替换。
- 入口、路边、桥侧挑灯、回廊悬灯、塔身灯龛、唱诗堂三组吊灯和少量路面嵌灯；保护区上方的水晶灯井补冷色灯。发光方块由{report['oldLightBlocks']}增至{report['newLightBlocks']}。
- 几何以V5为底；材质允许覆盖旧门楼/西翼的表皮，但所有原有实体坐标保留。音乐及周边一格、整片音乐保护区冻结；不会改变2307个音符盒的音色或写入原NBT。

## 怎么看、怎么搭

1. 先看日景材质对照，再看夜间灯位示意。图是方块数据渲染，没有套用游戏纹理或光影。
2. 页面“灯具定位”可选一组灯，自动定位它所在的设计高度。点格子查看完整方块ID和状态；上一/下一层查看支架与链条。坐标是设计坐标，不是服务器世界坐标。
3. 手建时先用同形状新材料替换外露表皮，再搭灯座/支架/铁链，最后放灯笼。悬挂灯笼标为hanging=true；链条用26.3-snapshot-9的iron_chain。
4. 材料总数见`材料与灯具.md`，灯具精确位置与组件见`灯具坐标.json`。完整模型`castle_v6.json`，相对V5的改动在`v6_changes.json`。

## 检查边界

路线支撑/三格净空与灯具附着经过静态检查。灯位图和夜景使用不含天空光的简化六方向光传播；楼梯等部分方块保守地当整格遮光。当前登记路幅中有{report['staticLightProxy']['zeroCells']}个格在这个模型中为0，其中{report['staticLightProxy']['zeroInProtected']}个位于冻结音乐保护区；坐标在`路线照明待验.json`。这不是游戏内防刷怪证明，也不覆盖未登记的房间角落。

没有新NBT，没有修改真实存档。浏览器只做文件级检查；此前本地页面自动访问受安全策略限制，不改道绕过。游戏光照、碰撞、火灾/刷怪规则及音乐试听需进入隔离创造档实测后再定稿。
'''
    (OUT/'先看这里.md').write_text(text,encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
