"""Small east-side projections on V19; immutable previous releases."""
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_story_rooms import frozen_cells
from castle_craft_integration import ProtectedEditor
from castle_interior import state,stair,slab,DIRECTIONS
from castle_sculpt import FULL

SOURCE=ROOT/'castle_v3/facade_v19/castle_v19.json'
OUT=ROOT/'castle_v3/release_v20'
TITLE='余响堡_V20施工总册.html'
REGIONS={'curtain':(85,90,-30,19,-45,61),'gallery':(76,80,15,30,28,66)}

@lru_cache(maxsize=1)
def model_v20():
    d,b=read_model(SOURCE);frozen=frozen_cells(d,b);e=ProtectedEditor(b,frozen,set());features=[];fixtures=[]
    def commit(name,zone,edits,note,build):
        r=REGIONS[zone];assert all(all(r[2*i]<=p[i]<=r[2*i+1] for i in range(3)) for p in edits)
        e.apply(name,edits);features.append(dict(name=name,family='sidewall_v20',positions=set(edits),note=note,build=build))
    terrain={}
    for (x,y,z),s in b.items():
        if s[2]=='terrain':terrain[x,z]=max(y,terrain.get((x,z),-999))
    for cz in(-43,-29,-15,0,17,31,45,59):
        edits={};top=16 if cz<0 else 9
        for x in range(86,89):
            for z in range(cz-1,cz+2):
                bottom=max(-29,terrain.get((x,z),-16)+1)
                for y in range(bottom,4):
                    if (x,y,z) not in b:edits[x,y,z]=state('tuff_bricks' if y<1 else 'cut_sandstone')
        for y in range(4,top-1):
            depth=2 if y<top-5 else 1
            for x in range(86,86+depth):
                for z in range(cz-1,cz+2):edits[x,y,z]=state('mud_bricks' if z!=cz else 'cut_sandstone')
        for y,x in((4,88),(top-5,87),(top-1,86)):
            for z in range(cz-1,cz+2):edits[x,y,z]=stair('west','smooth_sandstone_stairs')
        for z in range(cz-1,cz+2):edits[86,top,z]=slab('smooth_sandstone_slab')
        if cz in(-29,31):
            edits[88,4,cz]=state('lantern',hanging='false',waterlogged='false')
            fixtures.append(dict(name=f'东城墙扶垛台灯 Z={cz}',pos=[88,4,cz],kind='扶垛台灯',parts=[[88,4,cz]],supports=[[88,3,cz]]))
        commit(f'东外城墙加深扶垛 Z={cz}','curtain',edits,
               '位于旧拱龛之间，脚部外挑三格、上身逐步退回，保留全部旧凹拱与灯。',
               '先按最低层搭凝灰岩砖脚，再搭泥砖/砂岩芯，最后装回向墙面的压顶楼梯和下半台阶；两处台灯放在完整砂岩顶面。')
    for cz in(32,47,62):
        edits={}
        for z in range(cz-3,cz+4):
            for x in(77,78):edits[x,18,z]=slab('smooth_sandstone_slab','top')
            for y in range(19,28):
                for x in range(77,79 if abs(z-cz)<3 else 78):edits[x,y,z]=state('bricks')
            # Top-light bay with a one-course reveal; original wall remains behind glass.
            if abs(z-cz)<=2:
                for y in range(20,27):
                    edits[78,y,z]=None
                    edits[77,y,z]=state('gray_stained_glass_pane',north='true',south='true',east='false',west='false',waterlogged='false')
            for x in range(77,80):edits[x,28,z]=stair('west','deepslate_tile_stairs')
            edits[77,29,z]=slab('deepslate_tile_slab')
        for dz in(-3,0,3):
            for y in range(19,28):edits[78,y,cz+dz]=state('sandstone_wall',up='true',north='none',south='none',east='none',west='none',waterlogged='false')
        for dz in(-2,2):
            edits[77,16,cz+dz]=state('cut_sandstone')
            edits[77,17,cz+dz]=state('cut_sandstone');edits[78,17,cz+dz]=stair('west','smooth_sandstone_stairs','top')
        # The polygon's occupied east skin is X=75, not the nominal bound 76.
        edits={(x-1,y,z):s for (x,y,z),s in edits.items()}
        commit(f'维修长廊外挑高窗 Z={cz}','gallery',edits,
               '上部凸窗向外挑两格，薄深色雨檐再挑一格。是带原墙背衬的封闭造景，不开进原工坊、不新增可走空间。',
               '先搭两只石托臂和上半台阶窗台，再搭砖侧颊、玻璃片和细石柱，最后搭深色楼梯雨檐；X=75原墙不拆。')
    provisional={p for p in set(b)|set(e.blocks) if b.get(p)!=e.blocks.get(p)}
    for x,y,z in provisional:
        s=e.blocks.get((x,y,z))
        if not s or not s[0].endswith(('_wall','_pane')):continue
        n,pr,g=s;pr=dict(pr)
        for side,dx,dz in [('east',1,0),('west',-1,0),('north',0,-1),('south',0,1)]:
            nn=e.blocks.get((x+dx,y,z+dz),('',))[0];linked=nn in FULL or nn.endswith(('_wall','_pane')) or nn=='iron_bars'
            if n.endswith('_pane'):pr[side]=str(linked).lower()
            else:pr[side]=('tall' if side=='west' or y==27 else 'low') if linked else 'none'
        e.blocks[x,y,z]=(n,pr,g)
    a=e.blocks;changed={p for p in set(b)|set(a) if b.get(p)!=a.get(p)}
    for f in features:
        ps=f.pop('positions');parts=ps&set(a);anchors={tuple(p[i]+dd[i] for i in range(3)) for p in parts for dd in DIRECTIONS if tuple(p[i]+dd[i] for i in range(3)) in a and tuple(p[i]+dd[i] for i in range(3)) not in parts}
        f.update(parts=sorted(parts),anchors=sorted(anchors),oldAnchors=sorted(p for p in anchors if b.get(p)==a[p]),region=[v for i in range(3) for v in(min(p[i] for p in ps),max(p[i] for p in ps))])
    return dict(data=d,before=b,after=a,changed=changed,frozen=frozen,features=features,fixtures=fixtures)
