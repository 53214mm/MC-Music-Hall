"""V9 ground-skin recoloring. No excavation, extra layers, or cliff repainting."""
import math
from collections import Counter
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_finish import protected,EMISSION
from castle_front import route_cells
from castle_palette import GRAY_FULL

CARDINAL=((1,0),(-1,0),(0,1),(0,-1))
PAVING_FULL=GRAY_FULL|{'smooth_sandstone','cut_sandstone'}


def surface_columns(blocks):
    top={}
    for x,y,z in blocks:top[x,z]=max(y,top.get((x,z),-999))
    return top


def paving_material(name,p):
    x,y,z=p
    if name=='stone_brick_stairs':return 'smooth_sandstone_stairs'
    if name=='stone_brick_slab':return 'smooth_sandstone_slab'
    # Keep a narrow old-stone joint at intervals on the long approach.
    if z>=116 and z%9==0:return name
    if name in PAVING_FULL:return 'smooth_sandstone'
    return name


@lru_cache(maxsize=1)
def recolor_ground():
    data,before=read_model(ROOT/'castle_v3/palette_v8/castle_v8.json')
    top=surface_columns(before);after=dict(before)
    music={p for p,s in before.items() if s[2]=='control' or s[2].isdigit()}
    frozen={(x+dx,y+dy,z+dz) for x,y,z in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    for f in data['fixtures']:
        frozen.update(map(tuple,f['parts']));frozen.update(map(tuple,f['supports']))
    for p,s in before.items():
        if s[0] in EMISSION:frozen.update((p,(p[0],p[1]-1,p[2]),(p[0],p[1]+1,p[2])))
    route_floor=set()
    for r in data['routes']:route_floor.update(route_cells(r['points'],r['width']))
    paving={p for p in route_floor if -40<p[1]<=0 and top.get((p[0],p[2]))==p[1]}
    paving.update((x,y,z) for (x,y,z),s in before.items() if s[2]=='shell' and y==0 and -49<=x<=-14 and 25<=z<=79 and top[x,z]==y)
    masonry=PAVING_FULL|{'mud_bricks','bricks','packed_mud','calcite'}
    # A low wall must have a second masonry block above, so a pavement isn't a wall.
    wallfeet={p for p,s in before.items() if s[2]=='shell' and -35<=p[1]<=8 and s[0] in masonry and before.get((p[0],p[1]+1,p[2]),('',{},''))[0] in masonry}
    road_columns={(x,z):y for x,y,z in sorted(paving)}
    zones=Counter();changed=set();labels={}
    for (x,y,z),(name,props,group) in before.items():
        p=x,y,z
        if y!=top[x,z] or y<=-40 or p in frozen or protected(p):continue
        if p in paving and group=='shell':
            new=paving_material(name,p);zone='露天铺地'
        elif group=='terrain' and name in ('stone','andesite','tuff'):
            drop=max(y-top.get((x+dx,z+dz),y-6) for dx,dz in CARDINAL)
            # The steep rim and deep cracks remain rock; do not camouflage drops.
            if drop>=5:continue
            field=math.sin(x*.14+math.sin(z*.09))+.6*math.cos(z*.18-x*.04)
            nearwall=any((x+dx,y+dy,z+dz) in wallfeet for dx in range(-2,3) for dz in range(-2,3) if abs(dx)+abs(dz)<=2 for dy in range(0,5))
            nearroad=any(abs(road_columns.get((x+dx,z+dz),-999)-y)<=3 for dx in range(-4,5) for dz in range(-4,5) if abs(dx)+abs(dz)<=4)
            if nearwall:
                new='cut_sandstone' if field>.1 else 'smooth_sandstone';zone='墙根暖石'
            elif nearroad:
                new='packed_mud' if field>-.6 else 'coarse_dirt';zone='道路土肩'
            else:
                new='moss_block' if field>1.1 else 'mossy_cobblestone' if field>.75 else 'tuff' if field>.2 else 'coarse_dirt' if field<-.8 else 'packed_mud'
                zone='自然地表'
        else:continue
        if new!=name:
            after[p]=(new,dict(props),group);changed.add(p);zones[zone]+=1;labels[p]=zone
    return dict(data=data,before=before,after=after,changed=changed,frozen=frozen,top=top,paving=paving,zones=zones,labels=labels)
