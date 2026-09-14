"""V10 bounded exterior geometry on delivered V9. Atomic, protected features."""
import json
import math
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_finish import protected,EMISSION
from castle_front import route_cells
from castle_craft_samples import Sample
from castle_craft_integration import ProtectedEditor,mapped_edits,mapped_position

FULL={'stone','stone_bricks','andesite','polished_andesite','mossy_stone_bricks','cracked_stone_bricks','chiseled_stone_bricks','tuff','tuff_bricks','polished_tuff','chiseled_tuff_bricks','mud_bricks','packed_mud','bricks','smooth_sandstone','sandstone','cut_sandstone','chiseled_sandstone','calcite','deepslate_tiles','deepslate_bricks','spruce_planks','spruce_log','stripped_spruce_log'}


@lru_cache(maxsize=1)
def sculpt_castle():
    data,before=read_model(ROOT/'castle_v3/ground_v9/castle_v9.json')
    music={p for p,s in before.items() if s[2]=='control' or s[2].isdigit()}
    frozen={(x+dx,y+dy,z+dz) for x,y,z in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    frozen.update(p for p,s in before.items() if s[2]=='terrain')
    frozen.update(tuple(d['pos']) for d in json.loads((ROOT/'castle_v3/ground_v9/v9_changes.json').read_text(encoding='utf-8')))
    air=set()
    for r in data['routes']:
        floor=route_cells(r['points'],r['width']);frozen.update(floor)
        air.update((x,y+k,z) for x,y,z in floor for k in(1,2,3))
    for f in data['fixtures']:
        frozen.update(map(tuple,f['parts']));frozen.update(map(tuple,f['supports']))
    for p,s in before.items():
        if s[0] in EMISSION:frozen.update((p,(p[0],p[1]-1,p[2]),(p[0],p[1]+1,p[2])))
    for f in data['features']:
        r=f['region']
        frozen.update((x,y,z) for x in range(r[0],r[1]+1) for y in range(r[2],r[3]+1) for z in range(r[4],r[5]+1))
    frozen.update(air);e=ProtectedEditor(before,frozen,air);features=[];deferred=[]
    fixture_supports={tuple(p) for f in data['fixtures'] for p in f['supports']}
    terrain_top={}
    for (x,y,z),s in before.items():
        if s[2]=='terrain':terrain_top[x,z]=max(y,terrain_top.get((x,z),-999))

    def commit(title,family,edits,anchors,note,**meta):
        if not all(e.blocks.get(p,('',{},''))[0] in FULL for p in anchors):raise ValueError(f'{title}: missing full wall/roof anchors {anchors}')
        # Resolve new narrow members against the complete prospective neighborhood.
        def state(p):return edits[p] if p in edits else e.blocks.get(p)
        for (x,y,z),s in list(edits.items()):
            if not s or not s[0].endswith(('_wall','_fence')):continue
            n,props,g=s;props=dict(props)
            for side,dx,dz in [('east',1,0),('west',-1,0),('south',0,1),('north',0,-1)]:
                neighbor=state((x+dx,y,z+dz));nn=neighbor[0] if neighbor else ''
                join=nn in FULL or nn.endswith('_wall') if n.endswith('_wall') else nn in FULL or nn=='spruce_fence'
                props[side]=('low' if join else 'none') if n.endswith('_wall') else str(join).lower()
            edits[x,y,z]=(n,props,g)
        changed=e.apply(title,edits)
        positions=list(edits)
        features.append(dict(name=title,family=family,changed=changed,anchors=anchors,note=note,
                             region=[v for i in range(3) for v in (min(p[i] for p in positions),max(p[i] for p in positions))],**meta))

    def curtain(title,origin,turn,top):
        s=Sample(title,title,());edits={};at=lambda u,y,d:mapped_position((u,y,d),origin,turn)
        spring=top-6;base=2;profile=lambda u:spring+[4,3,2,0][abs(u)]
        recess=[]
        for u in range(-2,3):
            for y in range(base,profile(u)):
                if not all(before.get(at(u,y,d),('',{},''))[0] in FULL for d in(0,-1,-2)):
                    raise ValueError(f'{title}: missing three-course wall {at(u,y,0)}')
                edits[u,y,0]=None;recess.append([at(u,y,0),at(u,y,-1),at(u,y,-2)])
        for u in(-3,3):
            for y in range(base,spring+1):s.wall(u,y,1)
            s.put(u,base-1,1,'chiseled_sandstone');s.put(u,spring,1,'chiseled_sandstone')
        for u in range(-3,4):
            y=profile(u);s.stair(u,y,1,'smooth_sandstone_stairs','east' if u<0 else 'west','top')
            s.slab(u,base-1,1,'smooth_sandstone_slab','top')
            if u:
                inner=u-1 if u>0 else u+1
                for yy in range(y+1,profile(inner)):s.put(u,yy,1,'smooth_sandstone')
        # Tapered engaged piers sit on unchanged terrain or return to the old wall.
        for u in(-5,5):
            for d in(1,2):
                xx,_,zz=at(u,0,d);bottom=max(-13,terrain_top.get((xx,zz),-14)+1)
                last=3 if d==2 else top-3
                for y in range(bottom,last+1):
                    if y>=4:s.wall(u,y,d)
                    else:s.put(u,y,d,'tuff_bricks' if y<1 else 'cut_sandstone')
            s.stair(u,4,2,'smooth_sandstone_stairs','north')
            s.put(u,top-2,1,'chiseled_sandstone')
            s.stair(u,top-1,1,'smooth_sandstone_stairs','north','top')
            s.slab(u,top,1,'smooth_sandstone_slab')
        for u in range(-4,5):
            s.slab(u,top-1,1,'smooth_sandstone_slab','top')
            if u%4==0:s.stair(u,top-2,1,'smooth_sandstone_stairs','north','top')
        edits.update(s.blocks)
        commit(title,'curtain',mapped_edits(s,origin,turn,edits),[at(-5,1,0),at(5,1,0)],
               '只退去墙面最外一格，保留后方两层墙；薄拱框、收分扶垛与留空托石均为真实方块。',recess=recess)

    for side,x,turn in [('西',-79,1),('东',85,3)]:
        for z in(-50,-36,-22,-8,10,24,38,52,66):curtain(f'{side}长墙拱龛 Z={z}',(x,0,z),turn,16 if z<0 else 9)
    for x in(-48,-34,-20,-6,8,22,36,50):curtain(f'北长墙拱龛 X={x}',(x,0,-68),2,18)

    def window(title,origin,turn,base,spring,r):
        s=Sample(title,title,());edits={};at=lambda u,y,d:mapped_position((u,y,d),origin,turn);shared=[]
        fr=r+1
        arch=lambda u,rr:spring+round(math.sqrt(max(0,4*rr*rr-(abs(u)+rr)**2)))
        # Remove the two exact old surround rings; don't clear an entire rectangle.
        ring=set()
        for d in(1,2):
            rr=r+d
            ring.update((u,y,d) for u in(-rr,rr) for y in range(base-1,spring+1))
            ring.update((u,arch(u,rr),d) for u in range(-rr,rr+1))
            ring.update((u,base-1,d) for u in range(-rr,rr+1))
        for p in ring:
            old=e.blocks.get(at(*p))
            if old and (old[0] in FULL or old[0].endswith(('_stairs','_slab','_wall'))):
                if not e.allowed(at(*p)):shared.append(at(*p))
                else:edits[p]=None
        # Retained lamp anchors must still return to the wall, not hang from a
        # deleted outer arch. Add an inward stone neck, outside frozen routes.
        for u,y,d in ring:
            if at(u,y,d) not in fixture_supports:continue
            for dd in range(d-1,-1,-1):
                q=at(u,y,dd)
                if before.get(q,('',{},''))[0] in FULL and (u,y,dd) not in edits:break
                s.put(u,y,dd,'cut_sandstone')
        for u in(-fr,fr):
            for y in range(base,spring+1):s.wall(u,y,1)
            s.put(u,base-1,1,'chiseled_sandstone');s.put(u,spring,1,'chiseled_sandstone')
        for u in range(-fr,fr+1):
            y=arch(u,fr)
            s.stair(u,y,1,'smooth_sandstone_stairs','east' if u<0 else 'west','top')
            s.slab(u,y+1,1,'smooth_sandstone_slab')
            s.slab(u,base-1,1,'smooth_sandstone_slab','top')
            if u:
                inner=u-1 if u>0 else u+1
                for yy in range(y+1,arch(inner,fr)):s.put(u,yy,1,'smooth_sandstone')
        opening=[]
        for u in range(-r,r+1):
            for y in range(base,arch(u,r)):
                for d in(-1,0):
                    p=at(u,y,d);old=before.get(p)
                    if old is None or old[0].endswith(('_glass_pane','_bars')):opening.append(p)
        for y in range(base,spring+1):
            p=at(0,y,0);old=e.blocks.get(p)
            if old and old[0] in FULL and e.allowed(p):s.fence(0,y,0)
        for u in(-fr,fr):s.stair(u,base-2,1,'smooth_sandstone_stairs','north','top')
        edits.update(s.blocks)
        commit(title,'window',mapped_edits(s,origin,turn,edits),[at(-r-1,base+1,0),at(r+1,base+1,0)],
               '沿原窗位减薄双层外窗套；保留原空气、玻璃，以及兼作通路或灯座的旧外框成员。',opening=opening,retainedShared=shared)

    for title,cx,cz,r,top in [('冠塔',-1,-18,13,104),('北阶塔',-22,-47,10,62),('烽塔',-51,-43,10,78),('维修塔',67,4,11,59)]:
        for side,dx,dz,turn in [('南',0,r,0),('西',-r,0,1),('北',0,-r,2),('东',r,0,3)]:
            if title in ('烽塔','维修塔') and side=='南':
                region=[-56,-46,61,78,-34,-30] if title=='烽塔' else [62,72,42,60,14,18]
                deferred.append(dict(name=title+'南向上层窗廊',family='window',reason='外框与登塔平台、灯具支撑及三格通行净空重叠；窄框也无法完整绕开，整组保留原窗，留待与登塔空间联合精修。',region=region))
                continue
            window(title+side+'向上层窗廊',(cx+dx,0,cz+dz),turn,top-15,top-8,2)
    for x in(15,36):window(f'主堡北窗 X={x}',(x,0,-42),2,9,23,3)

    for side,x,turn in [('东',75,3),('西',59,1)]:
        origin=(x,0,45);s=Sample(side,side,());at=lambda u,y,d:mapped_position((u,y,d),origin,turn)
        # The north end of the west eave meets a frozen V7 window neighborhood.
        for u in range(-20 if side=='西' else -24,25):
            for y in range(30,34):
                if at(u,y,0) not in before:s.put(u,y,0,'mud_bricks')
            s.slab(u,33,1,'smooth_sandstone_slab','top')
            if u%6==0:
                s.stair(u,32,1,'smooth_sandstone_stairs','north','top')
                s.put(u,31,1,'spruce_fence',north=True,south=False,east=False,west=False,waterlogged=False)
            if abs(u) in(7,8,9,19,20,21):
                for y in range(30,33):
                    if at(u,y,0) not in before:s.trap(u,y,0,'spruce_trapdoor')
        commit('维修长廊'+side+'檐接缝与百叶','eave',mapped_edits(s,origin,turn),[at(-20,29,0),at(20,29,0)],
               '在列出的范围内补齐墙头到屋坡的四格外皮接缝；保留既有屋面，加入薄檐、间隔倒楼梯和木百叶。西檐北端避开V7窗跨保护范围。')

    for side,z,turn in [('南',18,0),('北',-18,2)]:
        origin=(-31,0,z);s=Sample(side,side,());at=lambda u,y,d:mapped_position((u,y,d),origin,turn)
        for u in range(-18,19):
            ry=42+(19-abs(u))//2
            s.slab(u,ry-1,-1,'smooth_sandstone_slab','top')
            s.stair(u,ry-1,0,'smooth_sandstone_stairs','north','top')
            if abs(u) in(5,12,17):
                s.stair(u,ry-2,-1,'spruce_stairs','north','top')
                s.stair(u,ry-2,0,'smooth_sandstone_stairs','north','top')
        commit('西翼藏谱馆'+side+'山墙薄收边','verge',mapped_edits(s,origin,turn),[at(-12,40,-3),at(12,40,-3)],
               '沿现有屋坡下缘增加薄收边，间隔木托与倒楼梯回接原屋檐；不复制屋顶或堆厚山墙。')

    after=e.blocks;changed={p for p in set(before)|set(after) if before.get(p)!=after.get(p)}
    return dict(data=data,before=before,after=after,changed=changed,frozen=frozen,features=features,deferred=deferred)
