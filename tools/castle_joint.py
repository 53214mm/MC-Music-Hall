"""V11: route-aware split/low window arches and supported warm niche lights."""
import json
import math
from functools import lru_cache
from castle_detail import ROOT, read_model
from castle_finish import EMISSION
from castle_front import route_cells
from castle_sculpt import FULL
from castle_craft_samples import Sample
from castle_craft_integration import ProtectedEditor, mapped_edits


@lru_cache(maxsize=1)
def joint_castle():
    data,before=read_model(ROOT/'castle_v3/detail_v10/castle_v10.json')
    music={p for p,s in before.items() if s[2]=='control' or s[2].isdigit()}
    frozen={(x+dx,y+dy,z+dz) for x,y,z in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    frozen.update(p for p,s in before.items() if s[2]=='terrain')
    frozen.update(tuple(d['pos']) for d in json.loads((ROOT/'castle_v3/ground_v9/v9_changes.json').read_text(encoding='utf-8')))
    air=set()
    for r in data['routes']:
        floors=route_cells(r['points'],r['width']);frozen.update(floors)
        air.update((x,y+k,z) for x,y,z in floors for k in(1,2,3))
    for f in data['fixtures']:
        frozen.update(map(tuple,f['parts']));frozen.update(map(tuple,f['supports']))
    for p,s in before.items():
        if s[0] in EMISSION:frozen.update((p,(p[0],p[1]-1,p[2]),(p[0],p[1]+1,p[2])))
    for f in data['features'][:12]:
        r=f['region'];frozen.update((x,y,z) for x in range(r[0],r[1]+1) for y in range(r[2],r[3]+1) for z in range(r[4],r[5]+1))
    bay_regions=[[-56,-46,61,80,-34,-30],[62,72,42,61,14,18]]
    platform_preserved=set()
    for r,ys in zip(bay_regions,[(64,65,76,77),(54,55,58,59,60,61)]):
        platform_preserved.update(p for p in before if r[0]<=p[0]<=r[1] and p[1] in ys and r[4]<=p[2]<=r[5])
    frozen.update(platform_preserved);frozen.update(air)
    editor=ProtectedEditor(before,frozen,air);features=[];fixtures=[]

    def commit(name,family,edits,anchors,note,**extra):
        if not all(editor.blocks.get(tuple(p),('',{},''))[0] in FULL for p in anchors):
            raise ValueError(f'{name}: missing masonry anchors {anchors}')
        def state(p):return edits[p] if p in edits else editor.blocks.get(p)
        for (x,y,z),s in list(edits.items()):
            if not s or not s[0].endswith(('_wall','_fence')):continue
            n,props,g=s;props=dict(props)
            for side,dx,dz in [('east',1,0),('west',-1,0),('south',0,1),('north',0,-1)]:
                other=state((x+dx,y,z+dz));nn=other[0] if other else ''
                join=(nn in FULL or nn.endswith('_wall')) if n.endswith('_wall') else (nn in FULL or nn=='spruce_fence')
                props[side]=('low' if join else 'none') if n.endswith('_wall') else str(join).lower()
            edits[x,y,z]=n,props,g
        count=editor.apply(name,edits)
        ps=list(edits);features.append(dict(name=name,family=family,changed=count,anchors=anchors,note=note,
            region=[v for i in range(3) for v in(min(p[i] for p in ps),max(p[i] for p in ps))],**extra))

    def bay(name,cx,z,base,spring,fire):
        sample=Sample(name,name,());edits={};at=lambda u,y,d:(cx+u,y,z+d)
        oldarch=lambda u,r:spring+round(math.sqrt(max(0,4*r*r-(abs(u)+r)**2)))
        ring=set()
        for d in(1,2):
            r=2+d
            ring.update((u,y,d) for u in(-r,r) for y in range(base-1,spring+1))
            ring.update((u,oldarch(u,r),d) for u in range(-r,r+1))
            ring.update((u,base-1,d) for u in range(-r,r+1))
        retained=[]
        for p in ring:
            q=at(*p);old=before.get(q)
            if not old:continue
            if not editor.allowed(q):retained.append(q)
            elif old[0] in FULL or old[0].endswith(('_stairs','_slab','_wall')):edits[p]=None
        opening=[]
        for u in range(-2,3):
            for y in range(base,oldarch(u,2)):
                for d in(-1,0):
                    q=at(u,y,d);s=before.get(q)
                    if not s or 'glass' in s[0]:opening.append(q)
        for u in range(-3,4):sample.slab(u,base-1,1,'smooth_sandstone_slab','top')
        for u in(-3,3):
            sample.stair(u,base-2,1,'smooth_sandstone_stairs','north','top')
        if fire:
            # Lower sill sits below the preserved Y64 landing. The new upper
            # arch stays beneath Y76 and stands outside the Y64 route width.
            for u in(-3,3):sample.wall(u,63,1)
            for u,ys in [(-4,range(68,71)),(4,range(66,71))]:
                for y in ys:sample.wall(u,y,2)
            for u in(-4,4):
                for y in range(68,71):sample.put(u,y,1,'cut_sandstone')
            profile=lambda u:[75,74,73,72,70][abs(u)]
            us=range(-4,5);depth=2
            mid_ys=[63]
            # The landing clearance severs the old upper mullion from its sill.
            # Remove the three dangling members, preserving the glass behind.
            for y in (68,69,70):edits[0,y,0]=None
        else:
            # Flat-crowned low arch terminates immediately below Y54. It
            # does not climb through the gallery or add a railing to its path.
            for u in(-3,3):
                for y in range(base,spring+1):sample.wall(u,y,1)
            profile=lambda u:[53,53,52,51][abs(u)]
            us=range(-3,4);depth=1;mid_ys=range(base,spring+1)
        arch=[]
        for u in us:
            y=profile(u);sample.stair(u,y,depth,'smooth_sandstone_stairs','east' if u<0 else 'west','top');arch.append(at(u,y,depth))
            if u:
                inner=u-1 if u>0 else u+1
                for yy in range(y+1,profile(inner)):sample.put(u,yy,depth,'smooth_sandstone');arch.append(at(u,yy,depth))
        for y in mid_ys:
            if before.get(at(0,y,0),('',{},''))[0] in FULL:sample.fence(0,y,0)
        # Two small side brackets return to a retained full masonry cell;
        # lamps are outside both the clear window and the walking envelope.
        bracket_y=71 if fire else 51
        for side in(-1,1):
            parts=[];anchor=at(side*4,bracket_y,0)
            for d in(1,2):sample.put(side*4,bracket_y,d,'cut_sandstone');parts.append(at(side*4,bracket_y,d))
            sample.stair(side*5,bracket_y,2,'smooth_sandstone_stairs','east' if side<0 else 'west','top');parts.append(at(side*5,bracket_y,2))
            sample.put(side*5,bracket_y-1,2,'iron_chain',axis='y',waterlogged=False);parts.append(at(side*5,bracket_y-1,2))
            sample.put(side*5,bracket_y-2,2,'lantern',hanging=True,waterlogged=False);parts.append(at(side*5,bracket_y-2,2))
            fixtures.append(dict(name=name+('左' if side<0 else '右')+'侧挂灯',pos=parts[-1],kind='窗廊侧挂灯',zone=name,supports=[anchor],parts=parts))
        edits.update(sample.blocks)
        commit(name,'platform_window',mapped_edits(sample,(cx,0,z),0,edits),[at(-4,bracket_y,0),at(4,bracket_y,0)],
               '保留平台、栏杆与旧灯座；'+('以两平台分隔上下窗廊，上拱最高Y75。' if fire else '低拱最高Y53，原Y54登塔平台与屋檐不拆。')+'两侧灯架回接原实墙。',
               opening=opening,newArch=arch,retainedShared=retained)

    bay('烽塔南向平台分隔窗廊',-51,-33,63,70,True)
    bay('维修塔南向平台下低拱窗',67,15,44,51,False)
    for f in data['features']:
        if f['family']!='curtain':continue
        cavity=[tuple(row[0]) for row in f['recess']];top=max(cavity,key=lambda p:p[1]);x,y,z=top
        lamp=(x,y-1,z);anchor=(x,y+1,z)
        if top in before or lamp in before:raise ValueError(f'{f["name"]}: niche must be air')
        parts={top:('iron_chain',dict(axis='y',waterlogged='false'),'shell'),
               lamp:('lantern',dict(hanging='true',waterlogged='false'),'shell')}
        name=f['name']+'顶挂暖灯'
        commit(name,'niche_light',parts,[anchor],'一格铁链接原拱龛顶，灯笼置于浅凹龛内；背墙与原砂岩拱框不拆。')
        fixtures.append(dict(name=name,pos=lamp,kind='拱龛顶挂灯',zone=f['name'],supports=[anchor],parts=list(parts)))
    after=editor.blocks;changed={p for p in set(before)|set(after) if before.get(p)!=after.get(p)}
    return dict(data=data,before=before,after=after,frozen=frozen,changed=changed,features=features,fixtures=fixtures,
                platformPreserved=platform_preserved,bayRegions=bay_regions,resolved=data['deferredFeatures'])
