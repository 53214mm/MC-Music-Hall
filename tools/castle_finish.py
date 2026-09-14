"""V6: surface material zoning and supported light fixtures on the saved V5 model."""
import math
from collections import deque
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_front import route_cells

DIRS=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))
EMISSION={'lantern':15,'sea_lantern':15,'ochre_froglight':15,'shroomlight':15,'soul_lantern':10}
MASONRY={'stone_bricks','mossy_stone_bricks','cracked_stone_bricks','andesite','polished_andesite','chiseled_stone_bricks'}
COLORS={'stone_bricks':'#969792','andesite':'#868783','polished_andesite':'#babbb4','chiseled_stone_bricks':'#acaca4','cracked_stone_bricks':'#888a83','mossy_stone_bricks':'#747f61','tuff_bricks':'#686f62','polished_tuff':'#767b6b','tuff':'#717664','chiseled_tuff_bricks':'#70775f','deepslate_bricks':'#3f4148','deepslate_tiles':'#30343e','deepslate_brick_stairs':'#454750','deepslate_brick_slab':'#454750','deepslate_tile_stairs':'#363a44','deepslate_tile_slab':'#363a44','calcite':'#dedace','smooth_sandstone':'#c8ba96','stripped_spruce_log':'#756045','spruce_planks':'#816447','spruce_log':'#50422f','stone_brick_wall':'#9b9d93','stone_brick_slab':'#a6a89f','stone_brick_stairs':'#9d9f96','polished_andesite_slab':'#babbb4','stone':'#777c70','lantern':'#ffc66a','ochre_froglight':'#efd899','sea_lantern':'#c6e7e5','gray_stained_glass_pane':'#535e69','iron_chain':'#424a4b','iron_bars':'#4b5156','light_blue_stained_glass':'#80b3c1','amethyst_block':'#9787af'}
NAMES={'tuff_bricks':'凝灰岩砖','polished_tuff':'磨制凝灰岩','chiseled_tuff_bricks':'雕纹凝灰岩砖','deepslate_bricks':'深板岩砖','deepslate_brick_stairs':'深板岩砖楼梯','deepslate_brick_slab':'深板岩砖台阶','calcite':'方解石','smooth_sandstone':'平滑砂岩','stripped_spruce_log':'去皮云杉原木','iron_chain':'铁链','ochre_froglight':'赭黄蛙明灯'}


def protected(p):
    x,y,z=p
    return -8<=x<=50 and -35<=y<=45 and -37<=z<=38


def spread_light(blocks,sources):
    """Conservative six-neighbor proxy: partial opaque shapes block a whole cell.

    No skylight, bounce, shader glow or spawning rules are modeled.
    """
    transparent={'lantern','soul_lantern','iron_chain','iron_bars','ladder','water','glass','light_blue_stained_glass','gray_stained_glass_pane'}
    opaque={p for p,s in blocks.items() if s[0] not in transparent and not s[0].endswith('_glass_pane')}
    light=dict(sources);queue=deque(sources)
    while queue:
        p=queue.popleft();value=light[p]-1
        if value<=0:continue
        x,y,z=p
        for dx,dy,dz in DIRS:
            q=(x+dx,y+dy,z+dz)
            if q in opaque or light.get(q,0)>=value:continue
            light[q]=value;queue.append(q)
    return light


@lru_cache(maxsize=1)
def finish_castle():
    data,before=read_model(ROOT/'castle_v3/envelope_v5/castle_v5.json')
    after=dict(before);music={p for p,s in before.items() if s[2]=='control' or s[2].isdigit()}
    frozen={(x+dx,y+dy,z+dz) for x,y,z in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    floors=set();air=set()
    for r in data['routes']:
        cells=route_cells(r['points'],r['width']);floors.update(cells)
        air.update((x,y+d,z) for x,y,z in cells for d in(1,2,3))
    def safe(p):return p not in frozen and not protected(p)
    def solid(p):
        s=after.get(p)
        return bool(s and (s[0] in MASONRY or s[0] in {'tuff_bricks','polished_tuff','chiseled_tuff_bricks','calcite','smooth_sandstone','stone','tuff','spruce_planks','spruce_log','stripped_spruce_log','deepslate_tiles','deepslate_bricks','ochre_froglight'}))
    exposed=[]
    for p,(name,props,g) in before.items():
        if g!='shell' or not safe(p):continue
        x,y,z=p
        if not any((x+dx,y+dy,z+dz) not in before for dx,dy,dz in DIRS):continue
        if name in MASONRY:
            exposed.append(p);n=name
            # Two-to-six-block patches follow courses and drift vertically. No white speckle.
            field=math.sin((x+z)*.19)+.6*math.cos((x-z)*.13+y*.24)
            gate=z>87;domestic=-75<=x<=-49 and 5<=z<=76;choir=-14<=x<=32 and 47<=z<=89
            base=-12 if gate else 16 if choir else 0
            if name=='polished_andesite':
                n='polished_tuff' if y<base+4 else 'smooth_sandstone' if choir and y>=25 else name
            elif name=='chiseled_stone_bricks':n='chiseled_tuff_bricks' if y<base+8 else name
            elif name in {'stone_bricks','mossy_stone_bricks','cracked_stone_bricks','andesite'}:
                if y<base+6:n='polished_tuff' if y in(base+3,base+4) else 'tuff_bricks'
                elif domestic and 6<=y<=14:
                    n='stripped_spruce_log' if (z-8)%9==0 or y in(6,13) else 'calcite'
                elif choir and y>=27:n='stone_bricks' if field<-.9 else 'andesite'
                else:n='andesite' if field<-.25 else 'stone_bricks'
                # Damp patches only low and away from formal window dressings.
                if base<y<base+8 and math.sin(x*.27)+math.cos(z*.23)>1.3:n='mossy_stone_bricks'
                # Local repaired masonry on the west, not identical age everywhere.
                if -49<=x<=-38 and 17<=y<=27 and -15<=z<=17:n='cracked_stone_bricks' if field<.4 else 'tuff_bricks'
            if n!=name:after[p]=(n,dict(axis='z' if y in(6,13) else 'y') if n=='stripped_spruce_log' else {},g)
        elif name in {'deepslate_tiles','deepslate_tile_stairs','deepslate_tile_slab'}:
            # Broad slate patches and roof-end courses; no repeating checkerboard.
            f=math.sin(x*.16+z*.06)+math.cos(z*.12)
            if f>1.1:after[p]=(name.replace('tile','brick'),props,g)
    fixtures=[];light_positions=[p for p,s in after.items() if s[0] in EMISSION]
    def near(p,d=6):return any(sum(abs(p[i]-q[i]) for i in range(3))<d for q in light_positions)
    def free(p):return safe(p) and p not in after and p not in air and p not in floors
    def add_fixture(pos,kind,parts,supports,zone):
        # Atomic placements: no partially built floating fixture if one cell is blocked.
        if any(not free(p) for p in parts):return False
        if not all(solid(p) for p in supports):return False
        after.update({p:(n,props,'shell') for p,(n,props) in parts.items()})
        fixtures.append(dict(pos=pos,kind=kind,zone=zone,supports=supports,parts=list(parts)))
        light_positions.append(pos);return True
    def stand(x,y,z,zone):
        floor=(x,y,z);light=(x,y+2,z)
        if near(light,6):return False
        return add_fixture(light,'路边灯座',{(x,y+1,z):('chiseled_tuff_bricks',{}),light:('lantern',dict(hanging='false',waterlogged='false'))},[floor],zone)
    def hang(x,y,z,zone):
        light=(x,y+4,z)
        if near(light,6):return False
        for roof in range(y+5,y+15):
            if (x,roof,z) not in after:continue
            if not solid((x,roof,z)):return False
            parts={light:('lantern',dict(hanging='true',waterlogged='false'))}
            for yy in range(y+5,roof):parts[x,yy,z]=('iron_chain',dict(axis='y',waterlogged='false'))
            return add_fixture(light,'悬灯',parts,[(x,roof,z)],zone)
        return False
    def niche(p,zone):
        if not safe(p) or p in floors or p in air or not solid(p) or near(p,6):return False
        # Flush fixture replaces one full cube, so no doorway becomes narrower.
        s=after[p]
        if s[2]!='shell' or s[0] not in MASONRY|{'tuff_bricks','polished_tuff','calcite','smooth_sandstone'}:return False
        x,y,z=p
        if not any((x+dx,y+dy,z+dz) not in after for dx,dy,dz in DIRS):return False
        after[p]=('ochre_froglight',dict(axis='y'),'shell')
        frame=[]
        for dy in(-1,1):
            q=(x,y+dy,z)
            if safe(q) and q not in floors and after.get(q,('',{},''))[0] in MASONRY|{'tuff_bricks','polished_tuff'}:
                after[q]=('chiseled_stone_bricks',{},'shell');frame.append(q)
        fixtures.append(dict(pos=p,kind='立面灯龛',zone=zone,supports=[p],parts=[p]+frame));light_positions.append(p);return True
    # Navigable routes: alternate the route edges, then try an overhead chain or wall recess.
    for r in data['routes']:
        points=list(map(tuple,r['points']))
        for i in range(0,len(points),6):
            x,y,z=points[i];p=points[i];nextp=points[min(i+1,len(points)-1)]
            if protected(p) or near((x,y+2,z),7):continue
            done=hang(x,y,z,r['name'])
            for distance in range(r['width']//2+2,r['width']//2+6):
                if done:break
                # Use perpendicular sides first; fallback tolerates corners and stair landings.
                offsets=[(distance,0),(-distance,0),(0,distance),(0,-distance)]
                if nextp[0]!=x:offsets=offsets[2:]+offsets[:2]
                if (i//6)%2:offsets=list(reversed(offsets))
                for dx,dz in offsets:
                    if stand(x+dx,y,z+dz,r['name']) or niche((x+dx,y+2,z+dz),r['name']):done=True;break
    # Architectural exterior lights, with narrow pale surrounds already present in V5.
    for side,x in [('east',57),('west',-13)]:
        for z in(-30,-17,-5,8,21,32):
            for y in(8,28,44):niche((x,y,z),'主堡外墙')
    for x in(-8,4,16,28,40,52):
        for y in(9,25):niche((x,y,44),'南立面')
    for cx,cz,r,levels in [(-1,-18,13,(58,78,97)),(-22,-47,10,(12,29,45,58)),(-51,-43,10,(18,39,58,72)),(67,4,11,(10,28,46,54)),(-28,113,12,(-5,16,36)),(-56,110,10,(-4,15))]:
        for y in levels:
            for x,z in ((cx-r,cz-4),(cx+r,cz+4),(cx-4,cz-r),(cx+4,cz+r)):
                niche((x,y,z),'塔身灯龛')
    # Three actual four-arm chandeliers, kept well above the nave's walking clearance.
    for z in(54,63,72):
        x=7;y=28;roof=next((yy for yy in range(y+2,57) if solid((x,yy,z))),None)
        if roof is None:continue
        parts={(x,yy,z):('iron_chain',dict(axis='y',waterlogged='false')) for yy in range(y+1,roof)}
        parts[x,y,z]=('deepslate_bricks',{})
        lights=[]
        for dx,dz in((1,0),(-1,0),(0,1),(0,-1)):
            for k in(1,2):parts[x+dx*k,y,z+dz*k]=('deepslate_brick_slab',dict(type='top',waterlogged='false'))
            pos=(x+dx*2,y-1,z+dz*2);parts[pos]=('lantern',dict(hanging='true',waterlogged='false'));lights.append(pos)
        if add_fixture(lights[0],'吊灯',parts,[(x,roof,z)],'唱诗堂'):
            light_positions.extend(lights[1:])
    # Open stairs and bridges lack ceilings/walls: a short stone outrigger carries
    # a floor lantern beyond the reserved walking width. Do not leave those paths dark.
    def outrigger(p,width,zone):
        x,y,z=p
        for dx,dz in((1,0),(-1,0),(0,1),(0,-1)):
            distance=width//2+2;end=(x+dx*distance,y,z+dz*distance);lamp=(end[0],y+2,end[2])
            if near(lamp,5):continue
            parts={};anchor=None;valid=True
            for k in range(distance+1):
                q=(x+dx*k,y,z+dz*k)
                if q in after:
                    if solid(q):anchor=q
                    elif after[q][0].endswith('_stairs'):pass
                    else:valid=False;break
                else:parts[q]=('tuff_bricks',{})
            if not valid or not anchor or end in after:continue
            parts[end[0],y+1,end[2]]=('chiseled_tuff_bricks',{})
            parts[lamp]=('lantern',dict(hanging='false',waterlogged='false'))
            if add_fixture(lamp,'桥侧挑灯',parts,[anchor],zone):return True
        return False
    for _ in range(2):
        field=spread_light(after,{p:EMISSION[s[0]] for p,s in after.items() if s[0] in EMISSION})
        recent=[]
        for r in data['routes']:
            for point in r['points']:
                p=tuple(point);x,y,z=p
                if not safe(p) or field.get((x,y+1,z),0)>=5 or any(sum(abs(p[i]-q[i]) for i in range(3))<5 for q in recent):continue
                if outrigger(p,r['width'],r['name']):recent.append(p);continue
                # Small flush floor medallions only where a supported edge lamp cannot fit.
                if after.get(p,('',{},''))[0] in MASONRY|{'tuff_bricks','polished_tuff','calcite','deepslate_bricks','spruce_planks'}:
                    after[p]=('ochre_froglight',dict(axis='y'),'shell')
                    fixtures.append(dict(pos=p,kind='路面嵌灯',zone=r['name'],supports=[p],parts=[p]));light_positions.append(p);recent.append(p)
    # The crystal lantern ABOVE the reserved machine must read as the night landmark.
    # Only the upper light-well corner blocks change; no source is placed near notes.
    for x in(11,31):
        for z in(0,20):
            for y in(54,60,65):
                p=(x,y,z);old=after.get(p)
                if safe(p) and old and old[2]=='shell' and old[0] in {'light_blue_stained_glass','polished_andesite'}:
                    after[p]=('sea_lantern',{},'shell');fixtures.append(dict(pos=p,kind='水晶灯井',zone='音乐核心上方采光井',supports=[p],parts=[p]))
    changed={p for p in set(after)|set(before) if before.get(p)!=after.get(p)}
    return dict(data=data,before=before,after=after,frozen=frozen,fixtures=fixtures,changed=changed,exposed=exposed)
