"""A bounded, real-block circulation sample, not the full castle."""
import math


def validate_route(blocks, route):
    """Conservative centerline check; route Y is support block, not player feet."""
    errors=[]
    full_supports={'stone','stone_bricks','mossy_stone_bricks','cracked_stone_bricks','andesite','polished_andesite','chiseled_stone_bricks','spruce_planks','spruce_log','deepslate_tiles','bookshelf','barrel','tuff_bricks','mud_bricks','polished_tuff','chiseled_tuff_bricks','calcite','smooth_sandstone','stripped_spruce_log','deepslate_bricks','ochre_froglight'}
    for x,y,z in route:
        support=blocks.get((x,y,z))
        if not support or not (support[0] in full_supports or support[0].endswith('_stairs') or support[0].endswith('_slab') and support[1].get('type') in('top','double')):
            errors.append(f'无支撑 {(x,y,z)}')
        for dy in (1,2,3):
            if (x,y+dy,z) in blocks:errors.append(f'净空不足 {(x,y+dy,z)}')
    for a,b in zip(route,route[1:]):
        dx,dy,dz=(b[i]-a[i] for i in range(3))
        if abs(dx)+abs(dz)!=1 or abs(dy)>1:
            errors.append(f'路线跳格 {a} → {b}');continue
        if dy:
            low,high=(a,b) if dy>0 else (b,a)
            facing={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}[(high[0]-low[0],high[2]-low[2])]
            stair=blocks.get(tuple(high))
            if not stair or not stair[0].endswith('_stairs') or stair[1].get('facing')!=facing or stair[1].get('half')!='bottom':
                errors.append(f'缺少正确方向的台阶 {high} / {facing}')
    return errors


def build_sample():
    blocks={};routes=[]
    def put(x,y,z,name='stone_bricks',props=None):
        blocks[x,y,z]=(name,props or {},'sample')
    def box(x0,y0,z0,x1,y1,z1,name='stone_bricks',props=None):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):put(x,y,z,name,props)
    def clear(x0,y0,z0,x1,y1,z1):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):blocks.pop((x,y,z),None)
    def stone(x,y,z):
        # Spatially localized weathering, not equal random noise on every wall.
        return 'mossy_stone_bricks' if y<1 and (x*17+z*13)%19<3 else 'andesite' if y<8 and (x*11+y+z*7)%31==0 else 'stone_bricks'
    def wallbox(x0,y0,z0,x1,y1,z1):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):put(x,y,z,stone(x,y,z))
    def rail(x,y,z):put(x,y,z,'stone_brick_wall',{'up':'true','north':'none','south':'none','east':'none','west':'none','waterlogged':'false'})
    def stair(x,y,z,facing,name='stone_brick_stairs',half='bottom'):
        put(x,y,z,name,{'facing':facing,'half':half,'shape':'straight','waterlogged':'false'})
    def lamp(x,y,z):put(x,y,z,'lantern',{'hanging':'false','waterlogged':'false'})
    # Cistern: a genuine underground void with a continuous water-mark course.
    box(-42,-13,29,-14,-12,77,'stone_bricks')
    for y in range(-11,0):
        for x in range(-42,-13):
            for z in range(29,78):
                if x in(-42,-14) or z in(29,77):
                    put(x,y,z,'mossy_stone_bricks' if y in(-8,-7) else 'stone_bricks')
    # Memorial recess at the end of the small side passage; no connection behind it.
    box(-18,-12,50,-14,-12,56,'polished_andesite')
    box(-15,-11,51,-15,-10,55,'chiseled_stone_bricks')
    box(-16,-11,52,-16,-11,54,'polished_andesite');lamp(-16,-10,53)
    # Ground courtyard and paved forecourt. The well is cut through the floor.
    box(-49,-1,25,-14,0,79,'stone_bricks')
    for x in range(-44,-14):
        for z in range(26,79):
            put(x,0,z,'andesite' if (x+z)%9 in(0,1) else 'stone_bricks')
    clear(-31,-11,38,-25,1,46)
    for x in range(-32,-23):
        for z in range(37,48):
            if x in(-32,-24) or z in(37,47):rail(x,1,z)
    # Cloister outer enclosure, inward-facing stepped arches and roof galleries.
    wallbox(-45,1,25,-44,8,60);wallbox(-15,1,25,-14,8,60)
    wallbox(-45,1,25,-14,8,26);wallbox(-45,1,59,-14,8,60)
    for z in(30,36,48,54):
        for x in(-39,-20):
            wallbox(x,1,z,x+1,5,z+1)
            box(x-1,6,z-1,x+2,6,z+2,'polished_andesite')
    for x in(-39,-20):
        for z0,z1 in((31,35),(37,47),(49,53)):
            for z in range(z0,z1+1):
                # Tall central well bay differs from the smaller repetitive bays.
                rise=min(z-z0,z1-z,3);y=4+rise
                box(x,y,z,x+1,8,z,'stone_bricks')
    for x in range(-46,-12):
        for z in range(24,62):
            if x<=-38 or x>=-20 or z<=31 or z>=55:
                put(x,9,z,'deepslate_brick_slab',{'type':'bottom','waterlogged':'false'})
    # Southern portico: buttressed entry and manual S1 gate opening.
    for x in(-36,-26):
        wallbox(x,1,61,x+1,9,63)
        stair(x,10,62,'north',half='top')
    # Raised archive with an inhabited undercroft, stepped buttresses and gable.
    box(-48,15,-15,-14,16,15,'stone_bricks')
    wallbox(-48,17,-15,-47,40,15);wallbox(-15,17,-15,-14,40,15)
    wallbox(-48,17,-15,-14,40,-14);wallbox(-48,17,14,-14,40,15)
    for x in range(-47,-14):
        for z in range(-14,15):
            if x<=-41 or x>=-21 or z<=-9 or z>=9:
                put(x,32,z,'spruce_planks')
    for x in(-46,-40,-22,-16):
        for z in(-13,13):
            box(x,0,z,x+1,15,z+1,'stone_bricks')
    for z in(-11,0,11):
        for x,side in((-50,'east'),(-12,'west')):
            wallbox(x,0,z,x+1,28,z+2)
            for j in range(3):stair(x,29+j,z+1,side)
    # West/east lancets recessed two blocks, filled with bars rather than crystal.
    for x0 in(-48,-15):
        for z0 in(-9,-2,5):
            clear(x0,22,z0,x0+1,29,z0+2)
            for z in range(z0,z0+3):
                for y in range(22,30-abs(z-(z0+1))):
                    put(x0, y,z,'iron_bars',{'north':'true','south':'true','east':'false','west':'false','waterlogged':'false'})
    # Southern window niches, visibly set back from stone mouldings.
    for cx in(-40,-23):
        clear(cx-1,23,14,cx+1,29,15)
        for x in range(cx-1,cx+2):
            for y in range(23,30-abs(x-cx)):
                put(x,y,14,'iron_bars',{'east':'true','west':'true','north':'false','south':'false','waterlogged':'false'})
        for x in(cx-2,cx+2):box(x,21,16,x,30,16,'polished_andesite')
        for x in range(cx-2,cx+3):stair(x,31-abs(x-cx),16,'north',half='top')
    # Gabled roof with real stair pitch, closed gable ends and ridge cap.
    for x in range(-50,-11):
        roof_y=42+(19-abs(x+31))//2
        for z in range(-17,18):
            stair(x,roof_y,z,'east' if x<-31 else 'west','deepslate_tile_stairs')
        for z in(-15,15):box(x,40,z,x,roof_y-1,z,'stone_bricks')
    box(-31,52,-18,-31,52,18,'deepslate_tiles')
    for z in(-12,0,12):
        box(-46,39,z,-16,39,z,'spruce_log',{'axis':'x'})
        for x in(-46,-16):box(x,33,z,x,38,z,'spruce_log',{'axis':'y'})
    # Open arched undercroft, so the raised archive does not read as thin stilts.
    for z in(-14,13):
        for left,right in((-46,-40),(-40,-22),(-22,-16)):
            for x in range(left,right+1):
                spring=5+min(x-left,right-x,7)
                box(x,spring,z,x,15,z+1,'stone_bricks')
                if left<x<right:stair(x,spring-1,z+1,'east' if x<(left+right)/2 else 'west',half='top')
    # Deep central portal, upper oculus, eaves corbels and a dressed gable edge.
    for x in range(-35,-26):
        opening=24-abs(x+31)//2
        clear(x,17,14,x,opening,15)
        for z in(16,17):
            if abs(x+31)>=3:box(x,17,z,x,opening,z,'polished_andesite')
            stair(x,opening+1,z,'north',half='top')
    for x in range(-36,-25):
        for y in range(29,40):
            radius=math.hypot(x+31,y-34)
            if radius<3.2:
                clear(x,y,14,x,y,15)
                if x==-31 or y==34:put(x,y,14,'iron_bars',{'north':'false','south':'false','east':'true','west':'true','waterlogged':'false'})
            elif radius<=4.4:put(x,y,16,'polished_andesite')
    for x in range(-49,-12):
        gy=42+(19-abs(x+31))//2
        put(x,gy,18,'polished_andesite')
        if x%3==0:stair(x,39,16,'north',half='top')
    # Lower, polygonal copyist's apse breaks the library's rectangular silhouette.
    def apse_inside(x,z):
        return -62<=x<=-47 and -12<=z<=8 and abs(x+52)+abs(z+2)<=20
    apse={(x,z) for x in range(-62,-46) for z in range(-12,9) if apse_inside(x,z)}
    for x,z in apse:
        put(x,16,z,'stone_bricks')
        boundary=any((x+dx,z+dz) not in apse for dx,dz in((1,0),(-1,0),(0,1),(0,-1)))
        if boundary and x<-48:
            box(x,17,z,x,33,z,'stone_bricks')
            put(x,34,z,'polished_andesite')
        ry=35+max(0,8-max(abs(x+54),abs(z+2)))
        put(x,ry,z,'deepslate_tiles')
    for x,z in((-61,-6),(-61,2),(-56,-11),(-56,7)):
        box(x,0,z,x,16,z,'stone_bricks')
        box(x,17,z,x,31,z,'polished_andesite')
    for z0 in(-5,1):
        clear(-62,22,z0,-62,28,z0+2)
        for z in range(z0,z0+3):
            for y in range(22,29-abs(z-z0-1)):
                put(-62,y,z,'iron_bars',{'north':'true','south':'true','east':'false','west':'false','waterlogged':'false'})
    # One reading desk, not a second hall full of unrelated furniture.
    box(-59,17,-5,-58,17,-3,'spruce_planks')
    box(-59,18,-5,-58,18,-3,'spruce_slab',{'type':'top','waterlogged':'false'})
    lamp(-59,19,-4)
    # Story props: preserved score shelves, contrasting rough repairs, desks.
    for z in range(-10,11):
        for y in range(17,23):put(-45,y,z,'bookshelf' if z%7 else 'spruce_planks')
    for x in range(-39,-31):
        for z in(-6,-5):put(x,18,z,'spruce_slab',{'type':'top','waterlogged':'false'})
    for x in(-39,-33):box(x,17,-6,x,17,-5,'spruce_planks')
    for x in(-38,-34):stair(x,17,-3,'north','spruce_stairs')
    lamp(-36,19,-6)
    for x in(-44,-40,-24):
        put(x,33,-11,'barrel',{'facing':'south','open':'false'})
    # Upper gallery railing follows the void, not a filled intermediate floor.
    for z in range(-8,9):
        for x in(-41,-21):rail(x,33,z)
    for x in range(-40,-21):
        for z in(-9,9):rail(x,33,z)
    # Suspended crossing above the open well. Supports remain outside the shaft.
    for x in(-36,-21):
        for z in(40,44):wallbox(x,1,z,x,15,z)
    box(-43,16,40,-17,16,44,'stone_bricks')
    for x in range(-43,-16):
        for z in(40,44):rail(x,17,z)
    # The long gallery has piers; leave the well itself open below the crossing.
    box(-33,16,14,-29,16,43,'stone_bricks')
    for z in(20,28,34):
        for x in(-33,-29):box(x,0,z,x,15,z,'stone_bricks')
    for z in range(16,40):
        for x in(-33,-29):rail(x,17,z)
    # A route is a build contract: 3-wide support, 3-high clear volume, actual stairs.
    def route(name,vertices,kind='main'):
        points=[]
        for a,b in zip(vertices,vertices[1:]):
            delta=[b[i]-a[i] for i in range(3)];n=max(map(abs,delta))
            if not n:continue
            step=[d//n for d in delta]
            if any(d!=s*n for d,s in zip(delta,step)) or abs(step[0])+abs(step[2])!=1:
                raise ValueError(f'Non-grid route {a} → {b}')
            segment=[tuple(a[i]+step[i]*j for i in range(3)) for j in range(n+1)]
            points.extend(segment if not points else segment[1:])
        routes.append(dict(name=name,kind=kind,points=points,width=3))
        return points
    route('前庭—西阶—藏谱下厅',[(-38,0,74),(-41,0,74),(-41,0,57),(-47,0,57),(-47,0,40),(-47,16,24),(-47,16,19),(-31,16,19),(-31,16,0)])
    route('空井地面环廊',[(-41,0,57),(-41,0,30),(-17,0,30),(-17,0,56),(-41,0,56),(-41,0,57)])
    route('藏谱下厅—回望悬桥',[(-31,16,0),(-31,16,42),(-19,16,42)])
    route('藏谱下厅—东阶—藏谱上廊',[(-31,16,0),(-25,16,0),(-25,16,14),(-19,16,14),(-19,16,12),(-19,32,-4),(-19,32,-11),(-31,32,-11)])
    route('藏谱上廊环路',[(-31,32,-11),(-43,32,-11),(-43,32,11),(-23,32,11),(-23,32,-11),(-31,32,-11)])
    route('偏置抄谱间',[(-31,16,0),(-40,16,0),(-40,16,-4),(-54,16,-4)],'deadend')
    route('空井—蓄水池—前庭',[(-35,0,30),(-35,0,32),(-35,-12,44),(-35,-12,54),(-19,-12,54),(-19,-12,59),(-19,0,71),(-19,0,74),(-38,0,74)],'explore')
    route('蓄水池纪念龛',[(-19,-12,54),(-17,-12,54)],'deadend')
    # Expand routes before reserving the union of all clearances, so turns are safe.
    clearances=set();floors={}
    for r in routes:
        pts=r['points']
        for i,p in enumerate(pts):
            x,y,z=p
            adjacent=([pts[i-1]] if i else [])+([pts[i+1]] if i+1<len(pts) else [])
            axes={(q[0]!=x,q[2]!=z) for q in adjacent}
            cells={(x,z)}
            for along_x,along_z in axes:
                cells.update((x+(j if along_z else 0),z+(j if along_x else 0)) for j in(-1,0,1))
            lower=next((q for q in adjacent if q[1]<y),None)
            facing=None
            if lower:facing={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}[(x-lower[0],z-lower[2])]
            for xx,zz in cells:
                floors[xx,y,zz]=facing
                clearances.update((xx,y+d,zz) for d in(1,2,3))
    for p,facing in floors.items():
        if facing:stair(*p,facing)
        elif p not in blocks or blocks[p][0].endswith(('_wall','_slab','_stairs')):put(*p)
    for p in clearances:blocks.pop(p,None)
    # Stair safety edging; handrails never occupy the walking lanes.
    for x,z0,z1,y0,dy in((-47,40,24,0,1),(-19,12,-4,16,1),(-35,32,44,0,-1),(-19,59,71,-12,1)):
        dz=1 if z1>z0 else -1
        for j,z in enumerate(range(z0,z1+dz,dz)):
            y=y0+dy*j
            for xx in(x-2,x+2):
                if (xx,y+1,z) not in clearances:
                    put(xx,y,z);rail(xx,y+1,z)
    # S1 is a removable 3x3 screen for creative testing, not an automatic door.
    shortcut=[(-31,0,z) for z in range(74,55,-1)]
    for x in range(-32,-29):
        for z in range(56,75):
            put(x,0,z)
            for y in(1,2,3):blocks.pop((x,y,z),None)
    seal=[]
    for x in range(-32,-29):
        for y in(1,2,3):
            put(x,y,60,'iron_bars',{'east':'true','west':'true','north':'false','south':'false','waterlogged':'false'});seal.append((x,y,60))
    # S2's ladder is deliberately incomplete. Six lower pieces are added manually.
    for y in range(17,34):
        put(-47,y,2,'spruce_planks')
        blocks.pop((-46,y,2),None)
        if y>=23:put(-46,y,2,'ladder',{'facing':'east','waterlogged':'false'})
    clear(-45,17,1,-45,22,3)
    # Low-key lamps and repairs, placed only off the inspected circulation lanes.
    for x,y,z in[(-43,1,68),(-16,1,75),(-37,-11,57),(-22,-11,33),(-46,17,17)]:
        if (x,y,z) not in clearances:
            put(x,y-1,z,'polished_andesite');lamp(x,y,z)
    # Serialize connected rails explicitly rather than relying on later updates.
    for (x,y,z),(name,props,group) in list(blocks.items()):
        if name!='stone_brick_wall':continue
        props=dict(props)
        for side,dx,dz in(('east',1,0),('west',-1,0),('north',0,-1),('south',0,1)):
            props[side]='low' if (x+dx,y,z+dz) in blocks else 'none'
        blocks[x,y,z]=(name,props,group)
    return dict(blocks=blocks,routes=routes,shortcuts=[dict(name='S1 前庭便门',remove=seal,points=shortcut),dict(name='S2 藏谱折返梯',add=[[-46,y,2] for y in range(17,23)],note='人工补6架梯子；未实现单向放梯机关，不计入步行净空验收')],
                markers=[dict(name='余烬前庭',pos=[-38,0,74]),dict(name='地面空井',pos=[-28,0,42]),dict(name='干蓄水池',pos=[-28,-12,42]),dict(name='回望悬桥',pos=[-28,16,42]),dict(name='藏谱下厅',pos=[-31,16,0]),dict(name='藏谱上廊',pos=[-31,32,-11])])
