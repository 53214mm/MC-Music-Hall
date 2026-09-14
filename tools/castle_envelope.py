"""V5 exterior extension, using the shipped V4 change set as an immutable baseline."""
import json
import math
from functools import lru_cache
from castle_detail import read_model,ROOT
from castle_front import route_cells


def octagon(cx,cz,r):
    return {(x,z) for x in range(cx-r,cx+r+1) for z in range(cz-r,cz+r+1) if abs(x-cx)+abs(z-cz)<=int(r*1.45)}


@lru_cache(maxsize=1)
def expand_envelope():
    data,original=read_model(ROOT/'castle_v3'/'full_castle'/'castle.json')
    baseline=dict(original);v4_changes=set()
    for edit in json.loads((ROOT/'castle_v3'/'detail_v4'/'exterior_changes.json').read_text(encoding='utf-8')):
        p=tuple(edit['pos']);old=tuple(edit['before']) if edit['before'] else None
        if original.get(p)!=old:raise ValueError(f'V4 no longer matches its source at {p}; do not silently rebase it')
        if edit['after']:baseline[p]=tuple(edit['after'])
        else:baseline.pop(p,None)
        v4_changes.add(p)
    _,previous=read_model(ROOT/'castle_v3'/'gate_west_combined'/'combined.json')
    floors=set();air=set()
    for r in data['routes']:
        cells=route_cells(r['points'],r['width']);floors.update(cells)
        air.update((x,y+d,z) for x,y,z in cells for d in(1,2,3))
    frozen=set(previous)|floors|v4_changes|{p for p,s in baseline.items() if s[2]=='control' or s[2].isdigit()}
    blocks=dict(baseline);touched=set();features=[]
    def allowed(p):
        x,y,z=p
        return p not in frozen and p not in air and not(-8<=x<=50 and -35<=y<=45 and -37<=z<=38)
    def put(p,n='stone_bricks',props=None):
        p=tuple(p)
        if allowed(p):blocks[p]=(n,props or {},'shell');touched.add(p)
    def clear(p):
        p=tuple(p)
        if allowed(p) and blocks.get(p,('',{},''))[2]=='shell':blocks.pop(p,None);touched.add(p)
    def box(x0,y0,z0,x1,y1,z1,n='stone_bricks',props=None):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):put((x,y,z),n,props)
    def stair(p,facing,half='bottom',n='stone_brick_stairs'):
        put(p,n,dict(facing=facing,half=half,shape='straight',waterlogged='false'))
    def slab(p,n='stone_brick_slab',kind='bottom'):put(p,n,dict(type=kind,waterlogged='false'))
    def wall(p,n='stone_brick_wall'):put(p,n,dict(up='true',east='none',west='none',north='none',south='none',waterlogged='false'))
    def face_mapper(cx,cz,side,distance):
        if side=='east':return lambda u,y,d:(cx+distance+d,y,cz+u)
        if side=='west':return lambda u,y,d:(cx-distance-d,y,cz+u)
        if side=='south':return lambda u,y,d:(cx+u,y,cz+distance+d)
        return lambda u,y,d:(cx+u,y,cz-distance-d)
    def pointed_window(at,base,spring,r=2,side='east',depth=3):
        # Narrower windows than the ceremonial front, with two stepped surrounds.
        for u in range(-r,r+1):
            yy=spring+round(math.sqrt(max(0,4*r*r-(abs(u)+r)**2)))
            for y in range(base,yy):
                for d in range(-depth+1,1):clear(at(u,y,d))
                horizontal=side in('north','south')
                put(at(u,y,-depth+1),'gray_stained_glass_pane',dict(east=str(horizontal).lower(),west=str(horizontal).lower(),north=str(not horizontal).lower(),south=str(not horizontal).lower(),waterlogged='false'))
        for d in(1,2):
            rr=r+d
            for u in(-rr,rr):
                for y in range(base-1,spring+1):put(at(u,y,d),'polished_andesite')
            for u in range(-rr,rr+1):
                y=spring+round(math.sqrt(max(0,4*rr*rr-(abs(u)+rr)**2)))
                facing=('south' if u<0 else 'north') if side in('east','west') else ('east' if u<0 else 'west')
                stair(at(u,y,d),facing,half='top')
                slab(at(u,base-1,d),'polished_andesite_slab',kind='top')
        for y in range(base,spring+1):put(at(0,y,0),'polished_andesite')
    # East/west side bays, staggered between the larger buttresses.
    for side in('east','west'):
        x=57 if side=='east' else -13
        for z in(-24,-4,19):
            at=face_mapper(x,z,side,0)
            pointed_window(at,7,20,2,side,3)
            # Upper single light and a shallow relief niche break the large wall.
            for y in range(34,41):
                for d in(0,-1,-2):clear(at(0,y,d))
                put(at(0,y,-2),'iron_bars',dict(east='false',west='false',north='true',south='true',waterlogged='false'))
            for u in(-2,2):
                for y in range(33,42):put(at(u,y,1),'polished_andesite')
            for u in range(-2,3):stair(at(u,43-abs(u),1),'south' if u<0 else 'north',half='top')
        for z in(-34,-15,8,31):
            at=face_mapper(x,z,side,0)
            for y in range(-8,44):
                depth=5 if y<6 else 4 if y<22 else 3 if y<35 else 2
                for u in(-1,0,1):
                    for d in range(1,depth+1):put(at(u,y,d),'stone_bricks' if u else 'polished_andesite')
                if y in(5,21,34):
                    for u in(-1,0,1):stair(at(u,y+1,depth), 'west' if side=='east' else 'east')
            slab(at(0,44,2),'polished_andesite_slab',kind='top');wall(at(0,45,2))
        # Two-course eaves plus discrete supporting corbels, rather than bright bands.
        for z in range(-32,35):
            at=face_mapper(x,z,side,0)
            for y in range(47,49):put(at(0,y,0))
            slab(at(0,46,1),'polished_andesite_slab',kind='top')
            stair(at(0,48,2),'west' if side=='east' else 'east',half='top',n='deepslate_tile_stairs')
            if z%4==0:stair(at(0,45,1),'west' if side=='east' else 'east',half='top')
    features.append(dict(name='主堡侧立面',pos=[59,22,19],note='错开的双联长窗、上部窄灯窗、四段收分扶垛；不复制南立面的圆窗。'))
    for x in(15,36):pointed_window(face_mapper(x,-42,'north',0),9,23,3,'north',3)
    # Close roof/wall junctions around the clipped keep, without entering tower cores.
    footprint={(x,z) for x in range(-13,58) for z in range(-42,45) if min(x+13,57-x)+min(z+42,44-z)>=7}
    edge={p for p in footprint if any((p[0]+dx,p[1]+dz) not in footprint for dx,dz in((1,0),(-1,0),(0,1),(0,-1)))}
    tower_specs=[(-1,-18,13,46,104,True),(-22,-47,10,-4,62,True),(-51,-43,10,-8,78,False),(67,4,11,-5,59,True)]
    def in_tower(x,y,z):return any(y>=base and (x,z) in octagon(cx,cz,r+1) for cx,cz,r,base,top,roof in tower_specs)
    for x,z in edge:
        roof_y=48+max(0,(36-max(abs(x-21),int(abs(z-1)*.65)))//2)
        for y in range(47,roof_y):
            if not in_tower(x,y,z):put((x,y,z))
        if not in_tower(x,roof_y,z):
            facing='east' if x<0 else 'west' if x>42 else 'south' if z<0 else 'north'
            stair((x,roof_y,z),facing,n='deepslate_tile_stairs')
    # Raised stone roof seams follow a slope; keep the crystal light well untouched.
    for z in(-32,31):
        for x in range(-11,56):
            y=48+max(0,(36-max(abs(x-21),int(abs(z-1)*.65)))//2)
            if not in_tower(x,y,z):slab((x,y+1,z),'deepslate_tile_slab')
    # Four different tower crowns retain their different uses and heights.
    for cx,cz,r,base,top,roof in tower_specs:
        outer=octagon(cx,cz,r);inner=octagon(cx,cz,r-1);crown=octagon(cx,cz,r+2)
        # Corner shafts run over the clipped corners, leaving broad clear wall bays.
        q=int(r*.45)
        corners={(cx+dx,cz+dz) for dx,dz in[(r,q),(r,-q),(-r,q),(-r,-q),(q,r),(-q,r),(q,-r),(-q,-r)]}
        for x,z in corners:
            for y in range(max(base,0),top-4):
                if (y-base)%18 in(0,1):put((x,y,z),'chiseled_stone_bricks')
                else:put((x,y,z),'polished_andesite')
        # Crown window gallery; lower lights vary between towers.
        levels=[(top-15,top-8)]
        if top>90:levels.append((66,75))
        elif cx==67:levels.append((23,31))
        for side in('north','south','east','west'):
            at=face_mapper(cx,cz,side,r)
            for b,s in levels:pointed_window(at,b,s,2,side,2)
        # A continuous projecting cornice, borne by separate corbels below.
        for x,z in crown:
            if (x,z) in inner:continue
            slab((x,top+1,z),'polished_andesite_slab',kind='top')
            if (x,z) not in outer and (x+z)%3==0:
                face='east' if x<cx else 'west' if x>cx else 'south' if z<cz else 'north'
                stair((x,top,z),face,half='top')
                put((x,top-1,z),'stone_bricks')
        if roof:
            # Roof skirt closes against the crown while preserving the original point.
            for x,z in crown:
                if any((x+dx,z+dz) not in crown for dx,dz in((1,0),(-1,0),(0,1),(0,-1))):
                    face='east' if x<cx else 'west' if x>cx else 'south' if z<cz else 'north'
                    stair((x,top+3,z),face,n='deepslate_tile_stairs')
            for x,z in ((cx-r-1,cz),(cx+r+1,cz),(cx,cz-r-1),(cx,cz+r+1)):
                slab((x,top+4,z),'polished_andesite_slab',kind='top')
                wall((x,top+5,z));slab((x,top+6,z),'stone_brick_slab')
        else:
            # Open beacon parapet: broad merlons with caps, no added conical roof.
            for x,z in crown:
                boundary=any((x+dx,z+dz) not in crown for dx,dz in((1,0),(-1,0),(0,1),(0,-1)))
                if boundary and (x+z)%4<2:
                    put((x,top+3,z));put((x,top+4,z));slab((x,top+5,z),'polished_andesite_slab')
        # Deliberate narrow stone relief at the quieter side, instead of more windows.
        at=face_mapper(cx,cz,'north',r)
        for u in(-4,4):
            for y in range(top-26,top-21):wall(at(u,y,1))
        features.append(dict(name='冠塔窗廊' if top>90 else '露天烽台' if not roof else '维修塔' if cx==67 else '北阶塔',pos=[cx,top,cz],note='托石与塔冠外挑；窗廊收口配合原有可达楼层。露台/窗台仍须实机检查防跌落。'))
    # Domestic roofs get closed eaves and a few structural end timbers, not gothic crowns.
    for p,s in list(baseline.items()):
        x,y,z=p
        if not(-74<=x<=-50 and 8<=z<=74 and 15<=y<=24 and s[0]=='deepslate_tile_stairs'):continue
        # Detect exposed roof ends from the existing geometry; never fill whole rooms.
        if any((x+dx,y,z+dz) not in baseline for dx,dz in((1,0),(-1,0))):
            for yy in range(15,y):
                if (x,yy,z) not in baseline:put((x,yy,z),'spruce_planks' if z%11==0 else 'stone_bricks')
            if z%11==0:stair((x,y-1,z),'east' if x<-61 else 'west',half='top',n='spruce_stairs')
    for p in touched:
        state=blocks.get(p)
        if not state or not state[0].endswith('_wall'):continue
        n,props,g=state;props=dict(props)
        for side,dx,dz in(('north',0,-1),('south',0,1),('east',1,0),('west',-1,0)):
            props[side]='low' if (p[0]+dx,p[1],p[2]+dz) in blocks else 'none'
        blocks[p]=(n,props,g)
    delta={p for p in set(baseline)|set(blocks) if baseline.get(p)!=blocks.get(p)}
    return dict(data=data,original=original,before=baseline,after=blocks,changes=delta,v4_changes=v4_changes,features=features)
