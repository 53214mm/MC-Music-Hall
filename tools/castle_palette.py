"""V8 material-only expansion on the immutable, delivered V7 model."""
from collections import Counter
from functools import lru_cache
from castle_detail import ROOT, read_model
from castle_craft_integration import ProtectedEditor
from castle_finish import EMISSION
from castle_front import route_cells

GRAY_FULL={'stone','stone_bricks','andesite','polished_andesite','chiseled_stone_bricks','cracked_stone_bricks','mossy_stone_bricks','tuff','tuff_bricks','polished_tuff','chiseled_tuff_bricks'}
GRAY_SHAPES={'stone_brick_stairs','stone_brick_slab','stone_brick_wall','polished_andesite_slab','polished_andesite_stairs','andesite_stairs','andesite_slab','andesite_wall'}
GRAYS=GRAY_FULL|GRAY_SHAPES
HORIZONTAL=((1,0,0),(-1,0,0),(0,0,1),(0,0,-1))
TOWERS=[(-1,-18,13,46,104,'冠塔'),(-22,-47,10,-4,62,'北阶塔'),(-51,-43,10,-8,78,'烽塔'),(67,4,11,-5,59,'维修塔')]


def zone_for(p):
    x,y,z=p
    for cx,cz,r,base,top,name in TOWERS:
        if abs(x-cx)<=r+4 and abs(z-cz)<=r+4 and base<=y<=top+5:return name,max(base+6,4),top
    if (x<=-76 or x>=80 or z<=-64) and z<=84:
        return '外围长墙',0,18 if z<=-64 else 16 if z<0 else 9
    if -72<=x<=-9 and 88<=z<=135:return '南门楼',-2,48
    if -75<=x<=-48 and 7<=z<=76 and y<=32:return '生活翼',4,25
    if -22<=x<=40 and 47<=z<=90 and y>=16:return '唱诗堂',21,55
    if 59<=x<=78 and 18<=z<=76:return '东侧维修翼',2,35
    if -21<=x<=64 and -47<=z<=51:return '主堡',6,64
    if -74<=x<=-12 and -24<=z<=87:return '西翼藏谱馆',8,44
    if -74<=x<=80 and -62<=z<=102:return '回廊与院墙',5,28
    return '保留石构',999,999


def material_for(name,p):
    if name not in GRAYS:return name
    zone,base,top=zone_for(p);x,y,z=p
    if y<base:return name
    # Pale members share the existing V7 dressings, independent of body color.
    if name.endswith('_wall'):return 'sandstone_wall'
    if name.endswith('_stairs'):return 'smooth_sandstone_stairs'
    if name.endswith('_slab'):return 'smooth_sandstone_slab'
    if name in ('polished_andesite','chiseled_stone_bricks','chiseled_tuff_bricks'):
        return 'chiseled_sandstone' if 'chiseled' in name else 'cut_sandstone'
    if zone=='外围长墙':return 'cut_sandstone' if y in (top,top+3) else 'mud_bricks'
    if zone=='南门楼':return 'bricks' if y>=14 else 'mud_bricks'
    if zone=='生活翼':return 'calcite' if y<=20 else 'bricks'
    if zone=='唱诗堂':return 'bricks'
    if zone=='西翼藏谱馆':return 'bricks' if y>=16 else 'mud_bricks'
    if zone in ('冠塔','北阶塔','烽塔','维修塔'):return 'bricks' if y>=top-22 else 'mud_bricks'
    if zone=='主堡' and 35<=y<=44:return 'packed_mud'
    return 'mud_bricks'


@lru_cache(maxsize=1)
def recolor_castle():
    data,before=read_model(ROOT/'castle_v3/integration_v7/castle_v7.json')
    music={p for p,s in before.items() if s[2]=='control' or s[2].isdigit()}
    frozen={(x+dx,y+dy,z+dz) for x,y,z in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    air=set()
    for r in data['routes']:
        floor=route_cells(r['points'],r['width']);frozen.update(floor)
        air.update((x,y+k,z) for x,y,z in floor for k in(1,2,3))
    for f in data['fixtures']:
        frozen.update(map(tuple,f['parts']));frozen.update(map(tuple,f['supports']))
    for p,s in before.items():
        if s[0] in EMISSION:
            frozen.update((p,(p[0],p[1]+1,p[2]),(p[0],p[1]-1,p[2])))
    frozen.update(air);e=ProtectedEditor(before,frozen,air);edits={};zone_counts=Counter();surface_gray=[]
    for p,(name,props,group) in before.items():
        if group!='shell' or name not in GRAYS:continue
        if not any(tuple(p[i]+d[i] for i in range(3)) not in before for d in HORIZONTAL):continue
        surface_gray.append(p)
        if not e.allowed(p):continue
        new=material_for(name,p)
        if new!=name:edits[p]=(new,dict(props),group);zone_counts[zone_for(p)[0]]+=1
    e.apply('V8统一墙面配色',edits)
    return dict(data=data,before=before,after=e.blocks,changed=set(edits),frozen=frozen,zone_counts=zone_counts,surface_gray=surface_gray)
