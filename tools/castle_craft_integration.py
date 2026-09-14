"""First integrated V7 exterior pass. Source V6, music, lights and routes stay frozen."""
import json
import math
from collections import Counter
from functools import lru_cache
from castle_detail import ROOT, read_model
from castle_finish import protected, EMISSION, DIRS
from castle_front import route_cells
from castle_craft_samples import Sample, samples

FACINGS=('east','south','west','north')
MASONRY={'stone_bricks','andesite','polished_andesite','chiseled_stone_bricks','cracked_stone_bricks','mossy_stone_bricks','tuff_bricks','polished_tuff','chiseled_tuff_bricks','smooth_sandstone'}
ROOFS={'deepslate_tiles','deepslate_bricks','deepslate_tile_stairs','deepslate_brick_stairs','deepslate_tile_slab','deepslate_brick_slab'}


def rotate_position(p,turns):
    x,y,z=p
    for _ in range(turns%4):x,z=-z,x
    return x,y,z


def rotate_state(state,turns):
    n,props,g=state;props=dict(props);turns%=4
    direction=lambda d:FACINGS[(FACINGS.index(d)+turns)%4]
    if props.get('facing') in FACINGS:props['facing']=direction(props['facing'])
    if turns%2 and props.get('axis') in ('x','z'):props['axis']='z' if props['axis']=='x' else 'x'
    arms={k:props.pop(k) for k in FACINGS if k in props}
    props.update({direction(k):v for k,v in arms.items()})
    return n,props,g


class ProtectedEditor:
    def __init__(self,before,frozen,air):self.before=before;self.blocks=dict(before);self.frozen=frozen;self.air=air

    def allowed(self,p):
        old=self.before.get(p)
        return not protected(p) and p not in self.frozen and p not in self.air and (old is None or old[2]=='shell')

    def apply(self,label,edits):
        edits={p:s for p,s in edits.items() if self.blocks.get(p)!=s}
        conflicts=[p for p in edits if not self.allowed(p)]
        if conflicts:raise ValueError(f'{label}: protected conflicts, no edits applied: {conflicts[:20]} ({len(conflicts)} total)')
        for p,s in edits.items():
            if s is None:self.blocks.pop(p,None)
            else:self.blocks[p]=s
        return len(edits)


def zone_at(p):
    x,y,z=p
    # Bounds follow external skins, not every exposed interior face of each building.
    if -75<=x<=-48 and 7<=z<=75 and 2<=y<=30:return '生活翼'
    if -21<=x<=40 and 48<=z<=90 and 20<=y<=60:return '唱诗堂'
    if -70<=x<=-10 and 88<=z<=133 and -3<=y<=52:return '南门楼'
    for cx,cz,r,base,top in [(-1,-18,13,46,110),(-22,-47,10,6,66),(-51,-43,10,6,85),(67,4,11,6,62)]:
        if base<=y<=top and r-2<=max(abs(x-cx),abs(z-cz))<=r+4:return '塔楼'
    if -20<=x<=64 and -48<=z<=51 and 6<=y<=68 and (x<=-10 or x>=54 or z<=-39 or z>=41):return '主堡'
    return None


def material(n,p,zone):
    x,y,z=p
    dress={'polished_andesite':'cut_sandstone','chiseled_stone_bricks':'chiseled_sandstone','polished_andesite_slab':'smooth_sandstone_slab','stone_brick_wall':'sandstone_wall'}
    if n in dress:return dress[n]
    if n in ('stone_brick_stairs','stone_brick_slab') and (zone in ('主堡','唱诗堂','塔楼') or y>=10):return n.replace('stone_brick','smooth_sandstone')
    if zone=='唱诗堂' and n in MASONRY-{'mossy_stone_bricks','tuff_bricks','polished_tuff','chiseled_tuff_bricks'}:
        # Keep flying buttresses and corner piers pale; reserve red brick for wall planes.
        if x in range(-11,-8) or x in range(27,30) or z in (48,49,79,80,81,82,83,84,85,86,87,88):return 'bricks'
        return 'smooth_sandstone' if n in ('smooth_sandstone','polished_andesite') else n
    if zone=='生活翼':
        if n in MASONRY and 5<=y<=14:return 'calcite'
        if n in MASONRY and y>14 and (z<=9 or z>=69):return 'bricks'
    if zone=='主堡' and n in ('stone_bricks','andesite') and y>=48:return 'bricks' if z>=44 and 10<=x<=32 else n
    return n


def mapped_edits(sample,origin,turns,edits=None):
    result={}
    for p,state in (sample.blocks if edits is None else edits).items():
        q=rotate_position(p,turns);q=tuple(q[i]+origin[i] for i in range(3))
        result[q]=rotate_state((state[0],state[1],'shell'),turns) if state else None
    return result


@lru_cache(maxsize=1)
def integrate_castle():
    data,before=read_model(ROOT/'castle_v3/finish_v6/castle_v6.json')
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
            frozen.add(p);frozen.add((p[0],p[1]+1,p[2]));frozen.add((p[0],p[1]-1,p[2]))
    frozen.update(air);e=ProtectedEditor(before,frozen,air);zone_counts=Counter();edits={}
    for p,(n,props,g) in before.items():
        if g!='shell' or not e.allowed(p):continue
        zone=zone_at(p)
        if not zone or not any(tuple(p[i]+d[i] for i in range(3)) not in before for d in DIRS):continue
        new=material(n,p,zone)
        if new!=n:edits[p]=(new,dict(props),g);zone_counts[zone]+=1
    e.apply('分区表皮',edits);features=[]

    def commit(title,family,edits,anchors,note):
        if not all(p in e.blocks for p in anchors):raise ValueError(f'{title}: missing wall/roof anchors {anchors}')
        changed=e.apply(title,edits)
        positions=list(edits)
        features.append(dict(name=title,family=family,changed=changed,anchors=anchors,note=note,
                             region=[v for i in range(3) for v in (min(p[i] for p in positions),max(p[i] for p in positions))]))

    def window(title,cx,cz,turn,base,spring,r):
        # Local +Z faces outdoors. Adapt A's fine members to the actual bay width.
        s=Sample(title,title,());edits={};at=lambda u,y,d:mapped_position((u,y,d),(cx,0,cz),turn)
        arch=lambda u,rr:spring+round(math.sqrt(max(0,4*rr*rr-(abs(u)+rr)**2)))
        for u in range(-r-3,r+4):
            for y in range(base-1,arch(0,r+3)+2):
                for d in (0,1,2):
                    p=at(u,y,d);old=e.blocks.get(p)
                    if old and (old[0] in MASONRY|{'cut_sandstone','chiseled_sandstone'} or old[0].endswith(('_stairs','_slab','_wall'))):edits[u,y,d]=None
        for u in range(-r,r+1):
            for y in range(base,arch(u,r)):
                for d in(-3,-2,-1,0):edits[u,y,d]=None
                s.put(u,y,-2,'gray_stained_glass_pane',east=True,west=True,north=False,south=False,waterlogged=False)
        for u in (-(r+1),r+1):
            for y in range(base-1,spring+1):
                s.put(u,y,-1,'cut_sandstone');s.put(u,y,0,'smooth_sandstone');s.wall(u,y,1)
            s.put(u,base-1,1,'chiseled_sandstone');s.put(u,spring,1,'chiseled_sandstone')
        for u in range(-r-1,r+2):
            y=arch(u,r+1)
            s.put(u,y,-1,'cut_sandstone')
            s.stair(u,y,0,'smooth_sandstone_stairs','east' if u<0 else 'west','top')
            s.slab(u,y+1,0,'smooth_sandstone_slab')
            s.slab(u,base-1,1,'smooth_sandstone_slab','top')
        # The two-circle outline rises several blocks near its spring. Join those
        # risers instead of leaving an isolated stair at each sampled height.
        for u in range(-r-1,r+2):
            if u==0:continue
            inner=u-1 if u>0 else u+1
            for y in range(arch(u,r+1)+1,arch(inner,r+1)):
                s.put(u,y,0,'smooth_sandstone');s.put(u,y,-1,'cut_sandstone')
        for u in (-r-1,r+1):
            s.put(u,base-1,1,'chiseled_sandstone');s.put(u,base-2,1,'grindstone',face='ceiling',facing='south')
        for u in (-r+1,0,r-1):
            for y in range(base,spring+1):s.fence(u,y,-1)
        for u in (-r-2,r+2):
            for y in range(base+3,base+7):s.trap(u,y,1,'dark_oak_trapdoor')
        for u in(-1,1):s.stair(u,spring+1,-1,'smooth_sandstone_stairs','east' if u<0 else 'west','top')
        s.slab(0,spring+2,-1,'smooth_sandstone_slab','top')
        s.connect();edits.update(s.blocks)
        world=mapped_edits(s,(cx,0,cz),turn,edits)
        # Anchor checks use untouched backing jamb blocks, not a floating front member.
        anchors=[at(-(r+1),base+1,-2),at(r+1,base+1,-2)]
        commit(title,'window',world,anchors,'沿用原窗洞位置；减薄外窗套，栅栏细窗棂后退，砂轮托住薄窗台。未改中央圆窗。')

    for cx in(1,41):window(f'南立面长窗 X={cx}',cx,44,0,9,22,4)
    for side,x,turn in [('西',-13,1),('东',57,3)]:
        for z in(-24,-4,19):window(f'{side}侧长窗 Z={z}',x,z,turn,7,20,2)

    def dormer(title,cx,cz,turn):
        # A roof-mounted adaptation of B; no sample plinth or solid attic block.
        s=Sample(title,title,());edits={};rise={0:6,1:5,2:3,3:1,4:0}
        at=lambda u,y,d:mapped_position((u,y,d),(cx,0,cz),turn)
        for u in range(-4,5):
            ry=49+rise[abs(u)]
            for d in range(-5,2):
                for y in range(43,ry):
                    old=e.blocks.get(at(u,y,d))
                    if old and old[0] in ROOFS:edits[u,y,d]=None
                s.stair(u,ry,d,'deepslate_tile_stairs','east' if u<0 else 'west')
                if d in(-5,1):s.stair(u,ry-1,d,'smooth_sandstone_stairs','east' if u<0 else 'west','top')
            for y in range(46,ry):s.put(u,y,0,'bricks')
            s.slab(u,ry,2,'smooth_sandstone_slab')
        for d in range(-5,3):s.slab(0,56,d,'deepslate_tile_slab')
        for u in range(-1,2):
            for y in range(48,53):
                for d in(-2,-1,0):edits[u,y,d]=None;s.remove(u,y,d)
                s.put(u,y,-2,'gray_stained_glass_pane',east=True,west=True,north=False,south=False,waterlogged=False)
                if u==0:s.fence(u,y,-1)
        for u in(-2,2):
            for y in range(47,53):s.wall(u,y,1)
            for y in range(49,52):s.trap(u*2,y,1)
            s.stair(u,53,0,'smooth_sandstone_stairs','east' if u<0 else 'west','top')
        for u in range(-3,4):s.slab(u,47,1,'smooth_sandstone_slab','top')
        # Side returns and the stepped slate riser join the existing main roof.
        for d in range(-5,0):
            for u in(-3,3):
                roof_levels=[y for y in range(40,55) if before.get(at(u,y,d),('',{},''))[0] in ROOFS]
                bottom=min(roof_levels) if roof_levels else 47
                for y in range(bottom,50):s.put(u,y,d,'bricks')
            for u in(-2,-1,1,2):
                low=49+rise[abs(u)+1]
                for y in range(low+1,49+rise[abs(u)]):s.put(u,y,d,'deepslate_tiles')
        s.connect();edits.update(s.blocks)
        anchors=[]
        for u in(-4,4):
            levels=[y for y in range(43,53) if before.get(at(u,y,0),('',{},''))[0] in ROOFS]
            if not levels:raise ValueError(f'{title}: no existing roof at side seam {u}')
            anchors.append(at(u,min(levels),0))
        commit(title,'dormer',mapped_edits(s,(cx,0,cz),turn,edits),anchors,'适配唱诗堂屋坡，九格宽、分段增坡；保留空心窗室，屋侧回接既有瓦面。')

    dormer('唱诗堂西坡老虎窗',-8,58,1)
    dormer('唱诗堂东坡老虎窗',24,71,3)

    c=samples()[2]
    def timber(title,origin,turn):
        edits={p:s for p,s in c.blocks.items() if p[1]>=5 and s[0]!='lantern'}
        # Retain existing lighting for this pass; omit unused sample suspension stems.
        for p in ((3,7,5),(9,7,5)):edits.pop(p,None)
        for x in range(3,10):
            for y in range(9,13):
                for z in(1,2,3,4):edits[x,y,z]=None
        anchors=[mapped_position((x,4,2),origin,turn) for x in(2,10)]
        commit(title,'timber',mapped_edits(c,origin,turn,edits),anchors,'只接入上部窗体和三格托架，不复制试样基座；横梁方向随立面旋转，铜绿仅用于小窗帽。')
    timber('旧厨房北向外挑窗',(-55,0,11),2)
    timber('收容长屋东向外挑窗',(-53,0,67),3)
    after=e.blocks;changed={p for p in set(before)|set(after) if before.get(p)!=after.get(p)}
    return dict(data=data,before=before,after=after,frozen=frozen,features=features,changed=changed,zone_counts=zone_counts)


def mapped_position(p,origin,turns):
    q=rotate_position(p,turns)
    return tuple(q[i]+origin[i] for i in range(3))
