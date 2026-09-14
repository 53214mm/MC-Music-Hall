"""V13 furnished domestic sequence, with supported interior access routes."""
from functools import lru_cache
from collections import deque
from castle_detail import ROOT,read_model
from castle_finish import protected,EMISSION
from castle_front import route_cells,grid_route
from castle_sample import validate_route

REGIONS={'shelter':(-67,-62,1,4,40,67),'kitchen':(-69,-53,1,5,10,26),
         'archive':(-44,-34,17,23,4,12),'upper':(-46,-45,33,37,-8,8)}
BRANCHES=[
 ('长屋北床位支路',[(-59,0,40),(-64,0,40)],'interior_deadend'),
 ('长屋中床位支路',[(-59,0,52),(-64,0,52)],'interior_deadend'),
 ('长屋南床位支路',[(-59,0,65),(-64,0,65)],'interior_deadend'),
 ('厨房备餐常开环线',[(-60,0,21),(-63,0,21),(-63,0,13),(-56,0,13),(-56,0,17),(-60,0,17),(-60,0,21)],'interior_loop'),
 ('藏谱下厅整理桌支路',[(-31,16,6),(-39,16,6)],'interior_deadend')]
DIRECTIONS=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))


def in_region(p,r):return all(r[2*i]<=p[i]<=r[2*i+1] for i in range(3))


class RoomEditor:
    def __init__(self,before,frozen,replaceable):
        self.before=before;self.blocks=dict(before);self.frozen=frozen;self.replaceable=replaceable

    def apply(self,name,edits,region):
        conflicts=[(p,self.blocks.get(p)) for p,s in edits.items() if not in_region(p,region) or protected(p) or p in self.frozen or
                   (p in self.blocks and p not in self.replaceable and self.blocks[p]!=s) or
                   (s and s[2]!='shell')]
        if conflicts:raise ValueError(f'{name}: atomic interior edit rejected: {conflicts[:10]}')
        for p,s in edits.items():
            if s is None:self.blocks.pop(p,None)
            else:self.blocks[p]=s


def state(n,**props):return(n,props,'shell')
def slab(n='spruce_slab',half='top'):return state(n,type=half,waterlogged='false')
def stair(facing='north',n='spruce_stairs',half='bottom'):
    return state(n,facing=facing,half=half,shape='straight',waterlogged='false')
def trap(facing='west'):return state('spruce_trapdoor',facing=facing,half='bottom',open='true',powered='false',waterlogged='false')
def barrel(facing='south'):return state('barrel',facing=facing,open='false')


def support_errors(blocks,features):
    """Grid connection to a verified original support; not a collision engine."""
    errors=[]
    for f in features:
        parts={tuple(p) for p in f['parts']};anchors={tuple(p) for p in f['anchors']}
        seen=set(anchors);queue=deque(anchors)
        while queue:
            p=queue.popleft()
            for d in DIRECTIONS:
                q=tuple(p[i]+d[i] for i in range(3))
                if q in parts and q in blocks and q not in seen:seen.add(q);queue.append(q)
        errors.extend((f['name'],p) for p in sorted(parts-seen))
    return errors


@lru_cache(maxsize=1)
def interior_castle():
    data,b=read_model(ROOT/'castle_v3/light_v12/castle_v12.json')
    music={p for p,s in b.items() if s[2]=='control' or s[2].isdigit()}
    frozen={(x+dx,y+dy,z+dz) for x,y,z in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    frozen.update(p for p,s in b.items() if s[2]=='terrain')
    for r in data['routes']:
        frozen.update((x,y+k,z) for x,y,z in route_cells(r['points'],r['width']) for k in range(4))
    for f in data['fixtures']:
        frozen.update(map(tuple,f['supports']));frozen.update(map(tuple,f['parts']))
    for p,s in b.items():
        if s[0] in EMISSION:frozen.update((p,(p[0],p[1]-1,p[2]),(p[0],p[1]+1,p[2])))
    for f in data['features']:
        r=f['region'];frozen.update((x,y,z) for x in range(r[0],r[1]+1) for y in range(r[2],r[3]+1) for z in range(r[4],r[5]+1))
    routes=[dict(name=n,points=grid_route(v),width=1,kind=k) for n,v,k in BRANCHES]
    openings=[]
    for r in routes:
        for x,y,z in r['points']:
            if (x,y,z) not in b:raise ValueError(f'No original floor for {r["name"]}: {(x,y,z)}')
            for k in(1,2,3):
                p=(x,y+k,z)
                if p not in b:continue
                if k!=1 or not b[p][0].endswith('_wall'):raise ValueError(f'Access blocked by non-rail: {p,b[p]}')
                if not all((x+dx,y,z+dz) in b for dx,dz in((0,0),(1,0),(-1,0),(0,1),(0,-1))):
                    raise ValueError(f'Rail has a drop beside it: {p}')
                openings.append(p)
    cot={(x,y,z+j) for z in(42,49,56,63) for x in range(-66,-62) for y in(1,2) for j in(0,1)}
    stove={(x,y,z) for x in range(-68,-65) for y in range(1,5) for z in range(17,23)}
    replaceable=cot|stove|set(openings)
    editor=RoomEditor(b,frozen,replaceable);features=[]
    for p in openings:editor.apply('室内同高栏杆口',{p:None},(p[0],p[0],p[1],p[1],p[2],p[2]))
    # Adjacent old rails must not keep an explicit arm toward the removed panel.
    rail_updates={}
    for x,y,z in openings:
        for side,dx,dz,back in [('east',1,0,'west'),('west',-1,0,'east'),('south',0,1,'north'),('north',0,-1,'south')]:
            q=x+dx,y,z+dz;s=editor.blocks.get(q)
            if s and s[0].endswith('_wall') and s[1].get(back)!='none':
                props=dict(rail_updates.get(q,s)[1]);props[back]='none';rail_updates[q]=(s[0],props,s[2])
    replaceable.update(rail_updates)
    for p,s in rail_updates.items():editor.apply('开口两侧栏杆收头',{p:s},(p[0],p[0],p[1],p[1],p[2],p[2]))
    for r in routes:frozen.update((x,y+k,z) for x,y,z in r['points'] for k in range(4))
    # Openings themselves are changes allowed before reserving the new route.
    def commit(name,zone,parts,story,build):
        editor.apply(name,parts,REGIONS[zone])
        anchors=set()
        for p in parts:
            for dd in DIRECTIONS:
                q=tuple(p[i]+dd[i] for i in range(3))
                if q in b and q not in parts and editor.blocks.get(q)==b[q]:anchors.add(q)
        positions=list(parts)
        features.append(dict(name=name,zone=zone,family='interior',parts=list(parts),anchors=sorted(anchors),
            region=[v for i in range(3) for v in(min(p[i] for p in positions),max(p[i] for p in positions))],
            note=story,build=build))
    for z,color,label in [(42,'white','叠好的白毯'),(49,'red','仍留着红毯的床'),(56,'green','补过的绿毯'),(63,'brown','未整理的褐毯')]:
        parts={}
        for x in range(-66,-62):
            for j in(0,1):
                parts[x,1,z+j]=state('stripped_spruce_log',axis='z') if x==-66 else slab()
                parts[x,2,z+j]=trap() if x==-66 else state(('white' if x==-65 else color)+'_carpet')
        commit(label,'shelter',parts,'低木框与两色织物区别床位；空床表达撤离留下的位置。木床造景，不可睡眠/设重生点。',
               '仅拆本床旧两层木块；Y1装床头原木与上半台阶，Y2放竖活板门和地毯，不能把地毯放在下半台阶上。')
    # Different bedside arrangements; no uniform grid of repeated storage.
    for name,x,z,n in [('北床旁的空衣箱',-65,40,'barrel'),('中床间修补台',-66,53,'crafting_table'),('南床旁的备用箱',-66,66,'barrel')]:
        parts={(x,1,z):barrel('east') if n=='barrel' else state(n)}
        commit(name,'shelter',parts,'储物并未写入物品；位置区别取衣、修补与离开前收拾的用途。','在原地板上放置，朝向室内支路；桶内物品留待手建后自行配置。')
    parts={}
    for x,y,z in sorted(stove):
        parts[x,y,z]=slab('brick_slab') if y==4 else state('tuff_bricks' if y==1 else 'bricks')
    for z in(18,20,22):parts[-66,2,z]=state('furnace',facing='east',lit='false')
    for z in range(17,23):parts[-66,3,z]=stair('east','brick_stairs','top')
    commit('三口熄火炉与薄石罩','kitchen',parts,'三个炉口没有火；旧大木顶换成石质薄罩，保留偏置烟囱和灶台位置。','只拆旧灶台标出的体积，凝灰岩下座、砖罩、东向熔炉逐层重建。熔炉不预装燃料。')
    parts={}
    for x in range(-67,-63):
        for z in(11,12):parts[x,1,z]=barrel('south') if x in(-67,-64) else slab('oak_slab')
    parts[-66,1,14]=state('crafting_table')
    for z in(11,12):parts[-68,1,z]=trap('west')
    parts[-64,2,12]=state('lantern',hanging='false',waterlogged='false')
    commit('备餐台与擦净的浅木台面','kitchen',parts,'浅橡木台面夹在深色桶柜之间，侧挡板薄而不封房；工作台与炉火分开。','先摆端头桶柜，再连上半橡木台阶；西侧活板门竖起。新增环线不放桌椅。')
    parts={}
    for x in range(-58,-53):
        for y in(1,2):parts[x,y,10]=barrel('south') if x in(-58,-56,-54) else state('spruce_planks')
        parts[x,3,10]=slab(half='bottom')
    parts[-56,3,10]=slab(half='top');parts[-56,4,10]=state('lantern',hanging='false',waterlogged='false')
    commit('空的储粮壁柜','kitchen',parts,'同一面墙有桶与封板的疏密变化；桶为空，不声称已装食物或道具。','两层桶/木柜原地落地，上铺下半台阶帽；正面朝南，从新备餐环线访问。')
    parts={}
    for x in range(-39,-34):
        for z in(7,8):parts[x,17,z]=barrel('north') if x in(-39,-35) else slab('oak_slab')
    for z in(7,8):parts[-40,17,z]=stair('east')
    parts[-34,17,8]=trap('east')
    commit('下厅的两人整理谱桌','archive',parts,'两张椅子靠近一张完整桌，另一端没有椅子；桌面置于挑空内，可从支路看整理台，再上楼俯看。未放书本实体或自定义文字。','桶柜作桌端，上半台阶作薄桌面；西侧两张楼梯椅。不要把桌面扩进X=-32…-30的主路。')
    parts={}
    for x in range(-43,-39):
        for y in range(17,21):parts[x,y,11]=state('stripped_spruce_log',axis='y') if x in(-43,-40) else state('bookshelf')
        parts[x,21,11]=stair('south','spruce_stairs','top')
        parts[x,22,11]=slab(half='bottom')
    for x in(-42,-41):parts[x,17,10]=trap('south')
    commit('下厅待归档的谱柜','archive',parts,'窄柜靠墙，原木侧柱与上下薄边包住普通书架；与上层成组档案柜区分。书架是原版装饰纹理，不含可读曲谱。','原地板上立木柱与书架，倒楼梯收檐、下半台阶封顶；底部竖活板门作柜裙。')
    for z0,label in [(-8,'上廊完整归档柜'),(4,'上廊补过的旧档柜')]:
        parts={}
        for z in range(z0,z0+3):
            for y in range(33,36):
                parts[-46,y,z]=state('bookshelf' if z==z0+1 else 'stripped_spruce_log',**({} if z==z0+1 else {'axis':'y'}))
            parts[-46,36,z]=stair('east','spruce_stairs','top');parts[-46,37,z]=slab(half='bottom')
        parts[-45,33,z0+1]=trap('east')
        if z0==4:parts[-46,34,5]=state('oak_planks')
        commit(label,'upper',parts,'归档柜贴实心楼板外侧，中央挑空与内侧栏杆保持；沿原上廊环路看到下厅的新整理桌。','柜脚落在Y32原楼板，向上立到Y35，Y36倒楼梯、Y37台阶帽。避开Z=2的旧折返梯井。')
    a=editor.blocks;changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
    for r in routes:
        errors=validate_route(a,r['points'])
        if errors:raise ValueError((r['name'],errors[:10]))
    errors=support_errors(a,features)
    if errors:raise ValueError(('Furniture unanchored',errors[:10]))
    for f in features:f['changed']=sum(p in changed for p in map(tuple,f['parts']))
    # Original frozen contract is returned; newly opened branch air was permitted above.
    frozen.difference_update(openings)
    return dict(data=data,before=b,after=a,changed=changed,frozen=frozen,replaceable=replaceable,
                routes=routes,openings=openings,railUpdates=rail_updates,features=features,supportErrors=errors)


@lru_cache(maxsize=1)
def interior_lighting():
    from castle_finish import spread_light
    m=interior_castle();fields={k:spread_light(m[k],{p:EMISSION[s[0]] for p,s in m[k].items() if s[0] in EMISSION}) for k in('before','after')}
    def stats(field,points):
        vs=[field.get(p,0) for p in points]
        return dict(samples=len(vs),minimum=min(vs),mean=round(sum(vs)/len(vs),2),zero=sum(v==0 for v in vs),below5=sum(v<5 for v in vs))
    points={(x,y+1,z) for r in m['data']['routes'] for x,y,z in route_cells(r['points'],r['width'])}
    worse=[dict(pos=p,before=fields['before'].get(p,0),after=fields['after'].get(p,0)) for p in sorted(points) if fields['after'].get(p,0)<fields['before'].get(p,0)]
    rows=[]
    for r in m['routes']:
        ps={(x,y+1,z) for x,y,z in r['points']}
        rows.append(dict(name=r['name'],kind=r['kind'],after=stats(fields['after'],ps),samples=[dict(pos=p,value=fields['after'].get(p,0)) for p in sorted(ps)]))
    return dict(method='同V12六邻域空气格保守代理，不透明异形方块整格遮挡；不含天空光/反射/游戏更新/刷怪判定。',
                before=stats(fields['before'],points),after=stats(fields['after'],points),dimmerSamples=worse,newRoutes=rows,inGameTest=False)
