"""Exterior-only refinement on the saved V3 block data, with protected music/routes."""
import json
import math
from pathlib import Path
from castle_front import route_cells
from castle_sample import validate_route

ROOT=Path(__file__).resolve().parents[1]


def read_model(path):
    d=json.loads(path.read_text(encoding='utf-8'))
    blocks={tuple(b[i]-d['offset'][i] for i in range(3)):tuple(d['palette'][b[3]]) for b in d['blocks']}
    return d,blocks


def refine():
    data,original=read_model(ROOT/'castle_v3'/'full_castle'/'castle.json');blocks=dict(original)
    _,old=read_model(ROOT/'castle_v3'/'gate_west_combined'/'combined.json')
    floors=set();air=set()
    for r in data['routes']:
        cells=route_cells(r['points'],r['width']);floors.update(cells)
        air.update((x,y+d,z) for x,y,z in cells for d in(1,2,3))
    frozen=set(old)|floors|{p for p,s in original.items() if s[2]=='control' or s[2].isdigit()}
    changes={};parts={};part='facade'
    def allowed(p):
        x,y,z=p
        return p not in frozen and p not in air and not(-8<=x<=50 and -35<=y<=45 and -37<=z<=38)
    def put(x,y,z,n='stone_bricks',props=None):
        p=(x,y,z)
        if allowed(p):blocks[p]=(n,props or {},'shell');changes[p]='place';parts[p]=part
    def remove(x,y,z):
        p=(x,y,z)
        if allowed(p) and p in blocks and blocks[p][2]=='shell':blocks.pop(p);changes[p]='remove'
    def box(x0,y0,z0,x1,y1,z1,n='stone_bricks',props=None):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):put(x,y,z,n,props)
    def stair(x,y,z,facing,half='bottom',n='stone_brick_stairs'):
        put(x,y,z,n,dict(facing=facing,half=half,shape='straight',waterlogged='false'))
    def slab(x,y,z,n='stone_brick_slab',kind='bottom'):put(x,y,z,n,dict(type=kind,waterlogged='false'))
    def wall(x,y,z,n='stone_brick_wall'):put(x,y,z,n,dict(up='true',east='none',west='none',north='none',south='none',waterlogged='false'))
    def pane(x,y,z,normal='south'):
        along=normal in('north','south')
        put(x,y,z,'gray_stained_glass_pane',dict(east=str(along).lower(),west=str(along).lower(),north=str(not along).lower(),south=str(not along).lower(),waterlogged='false'))
    def pinnacle(cx,y,cz,height=8):
        box(cx-1,y,cz-1,cx+1,y,cz+1,'polished_andesite')
        for k in range(1,height):
            if k<4:
                put(cx,y+k,cz,'chiseled_stone_bricks' if k==2 else 'stone_bricks')
                if k==3:
                    for dx,dz,face in((1,0,'west'),(-1,0,'east'),(0,1,'north'),(0,-1,'south')):stair(cx+dx,y+k,cz+dz,face)
            else:wall(cx,y+k,cz)
        slab(cx,y+height,cz)
    # A pointed archivolt is a thin shaped ring, not a filled triangular mass.
    def arch_height(u,r,spring):return spring+round(math.sqrt(max(0,4*r*r-(abs(u)+r)**2)))
    def front_window(cx,base,cz,r=4,spring=23):
        # Cut an opening all the way through the three-course wall first.
        for u in range(-r,r+1):
            top=arch_height(u,r,spring)
            for y in range(base,top):
                for z in range(cz-3,cz+1):remove(cx+u,y,z)
                pane(cx+u,y,cz-2)
        # Three progressively larger, outward-projecting carved surrounds.
        for d in range(3):
            rr=r+d+1;z=cz+d
            for x in(cx-rr,cx+rr):
                box(x,base-1,z,x,spring,z,'polished_andesite' if d!=1 else 'stone_bricks')
                for y in(base+3,spring-1):stair(x,y,z,'east' if x<cx else 'west',half='top')
            for u in range(-rr,rr+1):
                yy=arch_height(u,rr,spring)
                stair(cx+u,yy,z,'east' if u<0 else 'west',half='top',n='stone_brick_stairs')
                if d==2 and abs(u)%3==0:slab(cx+u,yy+1,z,'polished_andesite_slab')
            for x in range(cx-rr,cx+rr+1):slab(x,base-1,z,'polished_andesite_slab',kind='top')
        # Twin lancets and small high roundel behind the broad external arch.
        box(cx,base,cz-1,cx,spring+1,cz-1,'polished_andesite')
        for side in(-1,1):
            for u in range(-1,2):stair(cx+side*2+u,spring+1-abs(u),cz-1,'east' if u<0 else 'west',half='top')
        for u,v in((0,0),(1,1),(2,2),(1,3),(0,4),(-1,3),(-2,2),(-1,1)):
            slab(cx+u,spring+2+v,cz-1,'polished_andesite_slab',kind='top')
    # Remove the old shallow blind panels, leaving a structural backing outside core.
    for x in range(-6,50):
        for y in range(6,49):
            for z in range(42,48):remove(x,y,z)
    box(-8,6,41,51,47,42)
    # Close the inherited gap between wall head and hipped roof: attic masonry.
    for x in range(-8,52):
        for z in range(42,45):
            roof_y=48+max(0,(36-max(abs(x-21),int(abs(z-1)*.65)))//2)
            box(x,47,z,x,roof_y-1,z)
    for cx in(1,21,41):front_window(cx,9,44,r=4,spring=22)
    # Deep buttress piers are grouped at major bays, not attached to every wall voxel.
    for cx in(-8,11,31,51):
        for yy,half,depth in[(-2,2,7),(10,2,6),(23,1,5),(35,1,4)]:
            top={-2:9,10:22,23:34,35:44}[yy]
            box(cx-half,yy,44,cx+half,top,44+depth)
            for x in range(cx-half,cx+half+1):stair(x,top+1,44+depth,'north')
        pinnacle(cx,46,47,9 if cx in(11,31) else 7)
    # Two cornice courses with alternating corbels leave a distinct shadow line.
    for x in range(-9,53):
        slab(x,45,47,'polished_andesite_slab',kind='top')
        stair(x,47,48,'north',half='top')
        slab(x,48,48,'stone_brick_slab')
        if x%3==0:stair(x,44,47,'north',half='top')
    # High circular traceried window uses a stone ring, four spokes and quatrefoils.
    cx,cy,cz=21,39,48
    for x in range(cx-9,cx+10):
        for y in range(cy-9,cy+10):
            d=math.hypot(x-cx,y-cy)
            if d<=7.1:
                for z in range(41,49):remove(x,y,z)
                pane(x,y,43)
                if x==cx or y==cy or abs(x-cx)==abs(y-cy):put(x,y,45,'polished_andesite')
            elif d<=9.2:
                put(x,y,46 if d<8.2 else 47,'polished_andesite' if d<8.2 else 'stone_bricks')
    # A tall gable over the central bay breaks the otherwise continuous roof shoulder.
    for u in range(-11,12):
        yy=62-abs(u)
        box(cx+u,49,45,cx+u,yy,46,'stone_bricks')
        stair(cx+u,yy+1,47,'east' if u<0 else 'west',n='deepslate_tile_stairs')
        if abs(u)%4==0:wall(cx+u,yy+2,47)
    for y in range(51,58):
        for x in range(19,24):remove(x,y,45);remove(x,y,46)
        pane(20,y,45);pane(22,y,45)
    pinnacle(21,63,47,5)
    # Choir wall: steep paired lancets in deep two-course side reveals.
    part='choir'
    for z in range(50,79):
        for x in(-10,28):
            roof_y=40+max(0,14-abs(x-7)//2)
            box(x,39,z,x,roof_y-1,z)
    for zc in(58,68,77):
        for side,xwall in((-1,-10),(1,28)):
            for dz in range(-3,4):
                top=33+max(0,3-abs(dz))
                for y in range(23,top):
                    for dx in range(-1,2):remove(xwall+dx,y,zc+dz)
                    pane(xwall,y,zc+dz,'east')
            for zz in(zc-4,zc+4):
                box(xwall+side,21,zz,xwall+side,34,zz,'polished_andesite')
                for y in(24,30):slab(xwall+side*2,y,zz,'polished_andesite_slab',kind='top')
            for dz in range(-4,5):
                yy=37-abs(dz)
                stair(xwall+side,yy,zc+dz,'south' if dz<0 else 'north',half='top')
            box(xwall+side,23,zc,xwall+side,33,zc,'polished_andesite')
            for dz in range(-4,5):slab(xwall+side*2,22,zc+dz,'polished_andesite_slab',kind='top')
    # Flying buttress: stepped outer pier + a narrow rising curved arm + open void.
    for zc in(53,63,74):
        for side,xwall in((-1,-10),(1,28)):
            outer=xwall+side*9
            box(outer-1,0,zc-1,outer+1,25,zc+1)
            box(outer-1,26,zc,outer+1,30,zc,'polished_andesite')
            for k in range(10):
                x=outer-side*k;yy=29+round(9*(k/9)**.62)
                for z in(zc,zc+1):
                    stair(x,yy,z,'east' if side<0 else 'west',half='top')
                    put(x,yy+1,z,'polished_andesite')
                    slab(x,yy+2,z,'stone_brick_slab')
            pinnacle(outer,31,zc,9)
    # Choir eaves: dressed coping, projecting brackets and small roof-end pinnacles.
    for z in range(50,80):
        for x in(-11,28):
            stair(x,38,z,'east' if x<0 else 'west',half='top')
            slab(x,39,z,'polished_andesite_slab',kind='top')
            if z%4==0:stair(x+(-1 if x<0 else 1),37,z,'east' if x<0 else 'west',half='top')
    for z in range(50,83):
        slab(7,55,z,'deepslate_tile_slab',kind='top')
        if z%4==0:wall(7,56,z,'deepslate_brick_wall')
    for z in(50,80):pinnacle(7,56,z,5)
    # Dormers really cut a small opening in the old roof and have their own gables.
    for zc in(58,71):
        for side,cxx in((-1,-4),(1,19)):
            for x in range(cxx-2,cxx+3):
                for z in range(zc-2,zc+3):
                    for y in range(43,52):
                        if blocks.get((x,y,z),('',{},''))[0].startswith('deepslate_'):remove(x,y,z)
            for z in range(zc-2,zc+3):
                yroof=51-abs(z-zc)
                for x in range(cxx-2,cxx+3):
                    put(x,yroof,z,'deepslate_tiles')
                xx=cxx+side*2
                box(xx,44,z,xx,yroof-1,z,'polished_andesite')
                stair(xx,yroof,z,'south' if z<zc else 'north',n='deepslate_tile_stairs')
            for y in range(45,49):pane(cxx+side*2,y,zc,'east')
    # Repair patch is localized on one roof bay, not spread as visual static.
    for x in range(13,17):
        yy=40+max(0,14-abs(x-7)//2)
        for z in range(76,79):put(x,yy,z,'spruce_planks')
    # Weathering follows downpipes, sheltered bases and window drips.
    part='facade'
    for p,s in list(blocks.items()):
        x,y,z=p
        if s[0]!='stone_bricks' or s[2]!='shell' or p in frozen:continue
        if 40<=z<=52 and -9<=x<=53 and -2<=y<=11 and (y<=3 or abs(x-11)<=2 and y<9 or abs(x-31)<=2 and y<6):
            if (x*13+y*7+z*3)%23<4:put(x,y,z,'mossy_stone_bricks')
            elif (x*11+y+z)%29==0:put(x,y,z,'cracked_stone_bricks')
    # Explicit new rail connections. Existing stage states remain immutable.
    for p in changes:
        s=blocks.get(p)
        if not s or not s[0].endswith('_wall') or p in frozen:continue
        n,props,g=s;props=dict(props)
        for name,dx,dz in(('east',1,0),('west',-1,0),('north',0,-1),('south',0,1)):
            props[name]='low' if (p[0]+dx,p[1],p[2]+dz) in blocks else 'none'
        blocks[p]=(n,props,g)
    for p in frozen:assert blocks[p]==original[p],p
    for r in data['routes']:
        points=list(map(tuple,r['points']))
        assert not validate_route(blocks,points),r['name']
        for p in route_cells(points,r['width']):assert not validate_route(blocks,[p]),(r['name'],p)
    delta={p for p in set(original)|set(blocks) if original.get(p)!=blocks.get(p)}
    return data,original,blocks,delta,parts
