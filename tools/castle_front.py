"""South gate unit in castle design coordinates; immutable west-wing integration."""
import math
from castle_sample import build_sample,validate_route

DIRECTIONS={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}


def grid_route(vertices):
    points=[]
    for a,b in zip(vertices,vertices[1:]):
        delta=[b[i]-a[i] for i in range(3)];n=max(map(abs,delta))
        if not n:continue
        step=[d//n for d in delta]
        if any(d!=s*n for d,s in zip(delta,step)) or abs(step[0])+abs(step[2])!=1 or abs(step[1])>1:
            raise ValueError(f'Non-grid route {a} → {b}')
        part=[tuple(a[i]+step[i]*j for i in range(3)) for j in range(n+1)]
        points.extend(part if not points else part[1:])
    return points


def route_cells(points,width):
    if width<1 or width%2!=1:raise ValueError('Width must be positive odd')
    cells=set();half=width//2
    for a,b in zip(points,points[1:]):
        along_x=a[0]!=b[0]
        for x,y,z in(a,b):
            cells.update((x if along_x else x+j,y,z+j if along_x else z) for j in range(-half,half+1))
    return cells


def build_front():
    blocks={};routes=[]
    def put(x,y,z,name='stone_bricks',props=None,group='shell'):
        blocks[x,y,z]=(name,props or {},group)
    def box(x0,y0,z0,x1,y1,z1,name='stone_bricks',props=None,group='shell'):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):put(x,y,z,name,props,group)
    def clear(x0,y0,z0,x1,y1,z1):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):blocks.pop((x,y,z),None)
    def stair(x,y,z,facing,half='bottom',name='stone_brick_stairs'):
        put(x,y,z,name,dict(facing=facing,half=half,shape='straight',waterlogged='false'))
    def rail(x,y,z):put(x,y,z,'stone_brick_wall',dict(up='true',east='none',west='none',north='none',south='none',waterlogged='false'))
    def lantern(x,y,z,hanging=False):put(x,y,z,'lantern',dict(hanging=str(hanging).lower(),waterlogged='false'))
    def route(name,vertices,width=3,kind='explore'):
        r=dict(name=name,points=grid_route(vertices),width=width,kind=kind);routes.append(r);return r
    # Irregular shell-only cliff. The deliberately empty interior is not a room.
    heights={}
    for z in range(80,182):
        center=-45+round(5*math.sin(z*.087));half=round(43-max(0,z-112)*.28)
        for x in range(center-half,center+half+1):
            edge=abs(x-center)/half
            top=round(-12-max(0,z-150)*.65+3*math.sin(x*.18+z*.09))
            if z<96:top=round((96-z)*.75-12)
            top+=round(max(0,1-abs(x+18)/12)*max(0,1-abs(z-143)/20)*22)
            top-=round(max(0,edge-.7)*20)
            if 119<=z<=146 and -50<=x<=-36:top=-45
            heights[x,z]=max(-45,top)
    for (x,z),top in heights.items():
        # Three blocks of skin; exposed sides meet differing adjacent terrain.
        neighbors=[heights.get((x+dx,z+dz),-49) for dx,dz in((3,0),(-3,0),(0,3),(0,-3))]
        base=min(top-2,min(neighbors))
        for y in range(max(-48,base),top+1):
            material='tuff' if (y+round(3*math.sin(x*.08)))%17 in(0,1,2) else 'andesite' if y%11 in(0,1) else 'stone'
            put(x,y,z,material,group='terrain')
        # A bottom cap prevents the shell opening directly into the void.
        put(x,-48,z,'stone',group='terrain')
    # Bridge: masonry spandrels taper towards the high middle of the arch.
    for z in range(116,152):
        soffit=-15-abs(z-133)
        box(-46,soffit,z,-40,-12,z,'stone_bricks')
        for x in(-46,-40):rail(x,-11,z)
    for z in(116,151):box(-47,-35,z,-39,-13,z+1,'mossy_stone_bricks')
    # Gate hall and deliberately thick facade; the vaulted opening is cut next.
    box(-49,-13,93,-37,-12,113)
    box(-49,-11,93,-48,7,113);box(-38,-11,93,-37,7,113)
    box(-49,-11,93,-37,7,94);box(-49,-11,111,-37,7,113)
    box(-49,5,93,-37,8,113)
    clear(-47,-11,95,-39,4,110)
    for x in range(-47,-38):
        opening=1-abs(x+43)
        clear(x,-11,111,x,opening,113)
        for z in(114,115):
            stair(x,opening+1,z,'north',half='top')
            if abs(x+43)>=4:box(x,-11,z,x,opening,z,'polished_andesite')
    # Recessed raised portcullis. No trigger or redstone is implied.
    for x in range(-46,-39):
        for y in range(2,6):put(x,y,111,'iron_bars',dict(north='false',south='false',east='true',west='true',waterlogged='false'))
    for x in(-48,-38):box(x,-11,114,x,6,115,'deepslate_tiles')
    for x in(-49,-37):
        box(x,-13,113,x,9,116,'polished_andesite')
        lantern(x,10,114)
    for x in range(-49,-36):
        if x%3:box(x,9,113,x,11,114)
    # Multisided towers with genuine hollow interiors and inhabited levels.
    def footprint(cx,cz,r):
        return {(x,z) for x in range(cx-r,cx+r+1) for z in range(cz-r,cz+r+1) if abs(x-cx)+abs(z-cz)<=int(r*1.45)}
    def tower(cx,cz,r,top,floors,roof=False):
        outer=footprint(cx,cz,r);inner=footprint(cx,cz,r-2)
        for x,z in outer:
            for y in range(-28,-11):put(x,y,z,'mossy_stone_bricks' if y<-18 else 'stone_bricks')
            if (x,z) not in inner:
                for y in range(-11,top+1):put(x,y,z,'polished_andesite' if (abs(x-cx)==r or abs(z-cz)==r) and y%19==0 else 'stone_bricks')
            else:clear(x,-11,z,x,top,z)
            for y in floors:put(x,y,z,'spruce_planks' if y>0 else 'stone_bricks')
        # Projecting crown with corbels, not a flat rim at every floor.
        crown=footprint(cx,cz,r+1)
        for x,z in crown:
            if (x,z) not in inner:
                box(x,top+1,z,x,top+2,z,'polished_andesite')
                if (x+z)%3==0:stair(x,top,z,'east' if x<cx else 'west',half='top')
        if roof:
            for x,z in crown:
                d=max(abs(x-cx),abs(z-cz),int((abs(x-cx)+abs(z-cz))/1.45))
                ry=top+5+max(0,r+1-d)
                put(x,ry,z,'deepslate_tiles')
            # Offset stone chimney and a timber repair patch on the north slope.
            box(cx+3,top+5,cz-4,cx+4,top+16,cz-3,'stone_bricks')
            for x in range(cx-5,cx-1):
                for z in range(cz-10,cz-7):
                    ry=top+5+max(0,r+1-max(abs(x-cx),abs(z-cz)))
                    put(x,ry,z,'spruce_planks')
        else:
            for x,z in crown:
                edge=any((x+dx,z+dz) not in crown for dx,dz in((1,0),(-1,0),(0,1),(0,-1)))
                if edge:
                    put(x,top+3,z)
                    if (x+z)%4 in(0,1):box(x,top+4,z,x,top+5,z)
        # Lancets: cut both wall courses; arrow slits do not fill the interior.
        for y0 in(-6,14,33):
            if y0+5>=top:continue
            for dx,dz in((r,0),(-r,0),(0,r),(0,-r)):
                x,z=cx+dx,cz+dz
                if dx:
                    clear(min(x,x-(1 if dx>0 else -1)),y0,z,max(x,x-(1 if dx>0 else -1)),y0+5,z)
                else:
                    clear(x,y0,min(z,z-(1 if dz>0 else -1)),x,y0+5,max(z,z-(1 if dz>0 else -1)))
                for y in range(y0,y0+5):put(x,y,z,'iron_bars',dict(north='true' if dx else 'false',south='true' if dx else 'false',east='false' if dx else 'true',west='false' if dx else 'true',waterlogged='false'))
        # Broad buttress feet with setbacks along the lower half.
        for dx,dz in((r+1,0),(-r-1,0),(0,r+1),(0,-r-1)):
            x,z=cx+dx,cz+dz
            box(x,-26,z,x,1,z,'polished_andesite')
            stair(x,2,z,'east' if dx<0 else 'west' if dx>0 else 'south' if dz<0 else 'north')
    tower(-56,100,10,23,[-12,8,23])
    tower(-28,104,11,43,[-12,8,28,42],roof=True)
    # Roof walk above the gate, with supporting masonry already below it.
    box(-57,8,100,-28,8,104)
    for x in range(-48,-37):
        rail(x,9,100);rail(x,9,104)
    # Returning stair follows the western retaining wall, not a floating ladder.
    box(-62,-26,79,-60,8,100,'stone_bricks')
    # Small story objects kept outside walking lanes.
    box(-61,-11,104,-59,-11,105,'spruce_planks')
    box(-61,-10,104,-59,-10,105,'spruce_slab',dict(type='top',waterlogged='false'))
    stair(-60,-11,107,'north',name='spruce_stairs');lantern(-60,-9,104)
    for x,z in((-53,106),(-52,106),(-53,107),(-32,99),(-24,99)):
        put(x,-11,z,'barrel',dict(facing='up',open='false'))
    for y in(-4,16,36):
        box(-20,y,106,-20,y,108,'spruce_planks');lantern(-20,y+1,107)
    # Fallen waystone: small, ground-supported fragments beside the approach.
    box(-28,-29,171,-26,-27,172,'chiseled_stone_bricks');box(-25,-29,171,-22,-29,171,'polished_andesite')
    # The main road is five wide; tower flights are three wide with landings.
    route('断碑坡道—拱桥—门厅',[(-18,-28,178),(-43,-28,178),(-43,-28,174),(-43,-12,158),(-43,-12,102)],5,'main')
    route('门厅折入—前庭—西翼',[(-43,-12,102),(-43,-12,97),(-49,-12,97),(-49,-12,92),(-49,0,80),(-49,0,76),(-38,0,76),(-38,0,74)],3,'main')
    for base,span in((-12,10),(8,10),(28,7)):
        mid=base+span;end=base+2*span;start_z=110;turn_z=start_z-span
        route(f'东门塔 {base}→{end} 层', [(-28,base,113),(-25,base,113),(-25,base,110),(-25,mid,turn_z),(-25,mid,turn_z-3),(-31,mid,turn_z-3),(-31,mid,turn_z),(-31,end,110),(-31,end,113),(-28,end,113)])
    route('门厅—东门塔入口',[(-43,-12,102),(-30,-12,102),(-30,-12,113),(-28,-12,113)])
    route('东塔巡廊—西塔—前庭环路',[(-28,8,113),(-28,8,102),(-56,8,102),(-58,8,102),(-58,8,96),(-58,0,88),(-58,0,76),(-49,0,76),(-38,0,76),(-38,0,74)])
    route('守门人小室',[(-43,-12,102),(-55,-12,102)],3,'deadend')
    route('西门塔露台',[(-56,8,102),(-56,8,109),(-61,8,109),(-61,8,106),(-61,16,98),(-61,16,95),(-55,16,95),(-55,16,98),(-55,23,105),(-55,23,108)])
    # Open a route only where its 3-high clearance is explicitly reserved.
    floors={};clearances=set()
    for r in routes:
        pts=r['points'];cells=route_cells(pts,r['width'])
        for p in cells:floors.setdefault(p,None)
        for a,b in zip(pts,pts[1:]):
            if a[1]==b[1]:continue
            low,high=(a,b) if a[1]<b[1] else (b,a)
            facing=DIRECTIONS[high[0]-low[0],high[2]-low[2]]
            for p in route_cells([a,b],r['width']):
                if p[1]==high[1]:floors[p]=facing
        for x,y,z in cells:clearances.update((x,y+d,z) for d in(1,2,3))
    for p,facing in floors.items():
        if facing:stair(*p,facing)
        else:put(*p)
    for p in clearances:blocks.pop(p,None)
    # Guard the long access stair and cliff return with a parapet beside the lanes.
    for r in routes:
        for a,b in zip(r['points'],r['points'][1:]):
            if a[1]==b[1] and r['kind']!='main':continue
            along_x=a[0]!=b[0];half=r['width']//2+1
            for x,y,z in(a,b):
                for j in(-half,half):
                    p=(x if along_x else x+j,y,z+j if along_x else z)
                    if (p[0],p[1]+1,p[2]) not in clearances and (p[0],p[1]+1,p[2]) not in floors and p not in floors and p not in clearances:
                        put(*p);rail(p[0],p[1]+1,p[2])
    for (x,y,z),(name,props,g) in list(blocks.items()):
        if name!='stone_brick_wall':continue
        props=dict(props)
        for side,dx,dz in(('east',1,0),('west',-1,0),('north',0,-1),('south',0,1)):
            props[side]='low' if (x+dx,y,z+dz) in blocks else 'none'
        blocks[x,y,z]=(name,props,g)
    return dict(blocks=blocks,routes=routes,markers=[dict(name='断碑抵达点',pos=[-18,-28,178]),dict(name='拱桥中点',pos=[-43,-12,133]),dict(name='折入门厅',pos=[-43,-12,102]),dict(name='与西翼衔接',pos=[-38,0,74]),dict(name='东门塔顶层',pos=[-28,42,113]),dict(name='西塔露台',pos=[-55,23,108])])


def combined_model():
    front=build_front();west=build_sample();blocks=dict(front['blocks'])
    overlap=set(blocks)&set(west['blocks'])
    conflicts=sum(blocks[p][:2]!=west['blocks'][p][:2] for p in overlap)
    # Preserve the previously shipped west-wing block/state contract exactly.
    blocks.update(west['blocks'])
    cleared=set()
    for route in west['routes']:
        for x,y,z in route_cells(route['points'],route['width']):
            for d in(1,2,3):
                p=(x,y+d,z)
                if p in blocks and p not in west['blocks']:
                    blocks.pop(p);cleared.add(p)
    return dict(blocks=blocks,routes=front['routes']+west['routes'],markers=front['markers']+west['markers'],shortcuts=west['shortcuts'],
                integration=dict(sharedPositions=len(overlap),westPreferredDifferences=conflicts,westBlocks=len(west['blocks']),newUniqueBlocks=len(blocks)-len(west['blocks']),removedNewBlocksForExistingClearance=len(cleared)))
