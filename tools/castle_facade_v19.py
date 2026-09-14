"""Bounded north/east facade sample on immutable V17; no game or NBT writes."""
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_story_rooms import frozen_cells
from castle_interior import state,stair,slab,DIRECTIONS
from castle_craft_integration import ProtectedEditor
from castle_sculpt import FULL

REGION={'north':(-1,52,-9,75,-49,-38),'east':(53,65,-9,54,-37,-10),'roof':(1,51,48,75,-47,-18)}
ROOF={'deepslate_tiles','deepslate_bricks','deepslate_tile_stairs','deepslate_brick_stairs','deepslate_tile_slab','deepslate_brick_slab'}
SOURCE=ROOT/'castle_v3/watch_v17/castle_v17.json'
OUT=ROOT/'castle_v3/facade_v19'
TITLE='余响堡_V19北墙与转角精修.html'


def roof_height(blocks,x,z):
    return max((y for y in range(48,76) if blocks.get((x,y,z),('',))[0] in ROOF),default=None)


def wall():return state('sandstone_wall',up='true',east='none',west='none',north='none',south='none',waterlogged='false')


@lru_cache(maxsize=1)
def facade_v19():
    data,b=read_model(SOURCE);frozen=frozen_cells(data,b)
    # Freeze every existing crystal block and its six immediate neighbors as well.
    for p,s in b.items():
        if s[0] in ('amethyst_block','light_blue_stained_glass','purple_stained_glass','sea_lantern'):
            frozen.add(p);frozen.update(tuple(p[i]+v[i] for i in range(3)) for v in DIRECTIONS)
    e=ProtectedEditor(b,frozen,set());features=[];backs=[];joins=set()
    def commit(name,zone,edits,note,build):
        r=REGION[zone]
        assert all(all(r[2*i]<=p[i]<=r[2*i+1] for i in range(3)) for p in edits),(name,'outside scope')
        e.apply(name,edits)
        features.append(dict(name=name,zone=zone,note=note,build=build,positions=set(edits)))
    def foundation(edits,xzs):
        for x,z in xzs:
            ground=max((y for y in range(-9,5) if (x,y,z) in b),default=None)
            if ground is None:raise ValueError(('No foundation within scoped base',x,z))
            for y in range(ground+1,5):
                if (x,y,z) not in b:edits[x,y,z]=state('tuff_bricks')
    # Broad outside piers and narrow central shafts produce three unequal wall bays.
    for cx in (3,48,21,30):
        broad=cx in (3,48);edits={};width=1 if broad else 0;maxd=5 if broad else 3
        foundation(edits,[(x,-42-d) for x in range(cx-width,cx+width+1) for d in range(1,maxd+1)])
        for y in range(5,49 if broad else 48):
            depth=(5 if y<12 else 4 if y<26 else 3 if y<39 else 2) if broad else (3 if y<34 else 2)
            for x in range(cx-width,cx+width+1):
                for d in range(1,depth+1):
                    n='cut_sandstone' if x==cx and d==depth else 'mud_bricks'
                    edits[x,y,-42-d]=state(n)
            if y in (11,25,38) and broad:
                for x in range(cx-1,cx+2):edits[x,y+1,-42-depth]=stair('south','smooth_sandstone_stairs')
        if broad:
            for y in range(8,46):
                if y in (12,26,39):continue
                depth=5 if y<12 else 4 if y<26 else 3 if y<39 else 2
                edits[cx,y,-43-depth]=wall()
            for x in range(cx-1,cx+2):edits[x,49,-44]=slab('smooth_sandstone_slab')
            for y in range(50,54):edits[cx,y,-44]=wall()
            edits[cx,54,-44]=slab('smooth_sandstone_slab')
        else:edits[cx,48,-44]=state('chiseled_sandstone')
        commit(f'北墙{"厚扶壁" if broad else "中央细壁柱"} X={cx}','north',edits,
               '外侧厚扶壁逐级退让，中间细壁柱夹出较窄的凸跨；原两扇长窗不挪动。',
               '基脚从原地表上方接起，岩体不换；先搭实体芯，再装退台楼梯、墙状细柱与顶帽。')
    # Central bay projects two blocks but the two existing flanking windows stay intact.
    edits={}
    for x in range(22,30):
        for y in range(6,48):
            for z in (-43,-44):edits[x,y,z]=state('bricks' if y>=34 else 'mud_bricks')
    for u in range(-2,3):
        top=28-abs(u)
        for y in range(13,top):
            edits[26+u,y,-44]=None;edits[26+u,y,-43]=state('polished_tuff');backs.append((26+u,y,-43))
    for x in(23,29):
        for y in range(12,26):edits[x,y,-45]=wall()
        edits[x,12,-45]=state('chiseled_sandstone')
    for u in range(-3,4):
        y=28-abs(u);edits[26+u,y,-45]=stair('east' if u<0 else 'west','smooth_sandstone_stairs','top')
        edits[26+u,y+1,-45]=slab('smooth_sandstone_slab')
        edits[26+u,12,-45]=slab('smooth_sandstone_slab','top')
    # A small masonry shield in the blind niche; no false doorway to the music chamber.
    for y,half in ((17,1),(18,2),(19,2),(20,2),(21,1)):
        for u in range(-half,half+1):edits[26+u,y,-44]=state('cut_sandstone')
    for u in(-1,0,1):edits[26+u,16+abs(u),-44]=stair('east' if u<0 else 'west','smooth_sandstone_stairs','top')
    for u in range(-1,2):
        for y in range(37,45-abs(u)):
            edits[26+u,y,-44]=None;edits[26+u,y,-43]=state('polished_tuff');backs.append((26+u,y,-43))
    for u in(-2,2):
        for y in range(36,44):edits[26+u,y,-45]=wall()
    for u in range(-2,3):
        edits[26+u,45-abs(u),-45]=stair('east' if u<0 else 'west','smooth_sandstone_stairs','top')
        edits[26+u,36,-45]=slab('smooth_sandstone_slab','top')
    commit('中央凸跨与封闭徽龛','north',edits,'中央窄凸跨连接山墙，两侧保留原长窗。徽龛有实背衬，不是可进入的新门洞。','凸跨先接原墙，凹龛留一格退深；小盾形浮雕用石块和倒楼梯收尖，不加入旗帜实体。')
    # Actual one-course recesses in the outer skin retain the inner wall at Z=-40.
    for cx in (8,15,36,43):
        edits={}
        for u in range(-2,3):
            for y in range(36,46-abs(u)):
                edits[cx+u,y,-42]=None;edits[cx+u,y,-41]=state('bricks');backs.append((cx+u,y,-41))
        for u in(-3,3):
            for y in range(35,44):edits[cx+u,y,-43]=wall()
            edits[cx+u,35,-43]=state('chiseled_sandstone')
            edits[cx+u,43,-43]=state('cut_sandstone')
        for u in range(-3,4):
            y=46-abs(u);edits[cx+u,y,-42]=state('cut_sandstone')
            edits[cx+u,y,-43]=stair('east' if u<0 else 'west','smooth_sandstone_stairs','top')
            edits[cx+u,y+1,-43]=slab('smooth_sandstone_slab')
            edits[cx+u,35,-43]=slab('smooth_sandstone_slab','top')
        commit(f'北墙上层浅凹盲拱 X={cx}','north',edits,'只退掉外皮一层，砖红背衬在Z=-41，Z=-40内墙不动；不是一排新窗洞。','两根细柱支起倒楼梯尖拱；薄窗台和拱上台阶构成阴影，凹处保持为空气。')
    edits={}
    for x in range(1,51):
        if not 21<=x<=30:
            edits[x,34,-43]=slab('smooth_sandstone_slab','top')
            if x%4==0:edits[x,33,-43]=stair('south','smooth_sandstone_stairs','top')
        if not 15<=x<=37:
            edits[x,49,-43]=stair('south','deepslate_tile_stairs','top')
            edits[x,50,-43]=slab('deepslate_tile_slab')
    commit('北墙分层薄腰线与断开的檐线','north',edits,'腰线分开长窗与上层盲拱，屋檐在中央山墙处中断，避免再包成整圈矩形。','先贴墙放上半台阶，再在间隔位置放倒楼梯托石；不要把托石间空气填满。')
    # Cross-gable/dormer roofs decline backwards until they meet actual old roof tiles.
    def gable(cx,front,radius,peak,base,label):
        edits={};front_z=front;step=2 if radius>5 else 1
        # Front masonry is tied through to the existing wall/roof instead of a paper plane.
        for u in range(-radius,radius+1):
            top=peak-abs(u)
            for z in range(front_z,-41):
                for y in range(base,top):edits[cx+u,y,z]=state('bricks')
            for y in range(base,top):edits[cx+u,y,front_z]=state('cut_sandstone' if abs(u)==radius else 'bricks')
            edits[cx+u,top,front_z-1]=stair('east' if u<0 else 'west','smooth_sandstone_stairs')
            edits[cx+u,top-1,front_z-1]=stair('east' if u<0 else 'west','smooth_sandstone_stairs','top')
            if u%4==0:edits[cx+u,top+1,front_z-1]=wall()
        for z in range(front_z,-17):
            ridge=peak-max(0,(z-front_z-2)//step)
            for u in range(-radius,radius+1):
                oldtop=roof_height(b,cx+u,z);yy=ridge-abs(u)
                if oldtop is not None and yy<=oldtop:
                    joins.add((cx+u,oldtop,z));continue
                if yy<base:continue
                edits[cx+u,yy,z]=stair('east' if u<0 else 'west','deepslate_tile_stairs') if u else slab('deepslate_tile_slab','top')
                # One course below joins stair risers into a continuous roof skin.
                if yy-1>=base and (oldtop is None or yy-1>oldtop):edits[cx+u,yy-1,z]=state('deepslate_tiles')
                # Closed side cheek down to the old roof, but keep the original roof underneath.
                if abs(u)==radius:
                    for y in range(oldtop+1 if oldtop is not None else base,yy):edits[cx+u,y,z]=state('bricks')
        for x in (cx-3,cx,cx+3) if radius>5 else (cx,):
            r=1;spring=base+6 if radius>5 else base+3
            for u in range(-r,r+1):
                for y in range(base+1,spring+2-abs(u)):
                    edits[x+u,y,front_z]=None
                    edits[x+u,y,front_z+1]=state('polished_tuff');backs.append((x+u,y,front_z+1))
            for u in(-2,2):
                for y in range(base,spring+1):edits[x+u,y,front_z-1]=wall()
            for u in range(-2,3):
                edits[x+u,spring+2-abs(u),front_z-1]=stair('east' if u<0 else 'west','smooth_sandstone_stairs','top')
                edits[x+u,base,front_z-1]=slab('smooth_sandstone_slab','top')
            for y in range(base+1,spring+1):edits[x,y,front_z]=state('spruce_fence',east='false',west='false',north='false',south='true',waterlogged='false')
        if radius>5:
            # Small round stone tracery above the three tall lights, with solid backing.
            cy=peak-6
            for u in range(-3,4):
                for v in range(-3,4):
                    rr=u*u+v*v
                    if rr<=4:
                        edits[cx+u,cy+v,front_z]=None
                        edits[cx+u,cy+v,front_z+1]=state('polished_tuff');backs.append((cx+u,cy+v,front_z+1))
                    elif 5<=rr<=10:
                        edits[cx+u,cy+v,front_z-1]=slab('smooth_sandstone_slab','bottom' if v>0 else 'top') if abs(v)>=2 else wall()
            for u,v in[(0,0),(1,0),(-1,0),(0,1),(0,-1)]:edits[cx+u,cy+v,front_z]=wall()
            for y in range(peak+1,peak+4):edits[cx,y,front_z-1]=wall()
            edits[cx,peak+4,front_z-1]=slab('smooth_sandstone_slab')
        # Do not overwrite original geometry when the outer gable joins an old roof tile.
        commit(label,'roof',edits,'砖红山墙配薄浅色斜边，深色交接屋面向后降低并接回原坡。旧屋面保留在下方，不声称新增可走阁楼。','先搭贴墙/接坡的山墙背板，再封侧颊、搭向后收低的屋面，最后装倒楼梯窗头、薄檐和尖顶。')
    gable(26,-45,10,68,49,'中央高山墙与后收交接屋面')
    gable(6,-43,4,60,51,'北面左侧小老虎窗')
    gable(45,-43,4,60,51,'北面右侧小老虎窗')
    for cz in (-34,-15):
        edits={};foundation(edits,[(x,z) for x in range(58,65) for z in range(cz-2,cz+3)])
        for y in range(5,48):
            half=2 if y<13 else 1;depth=7 if y<13 else 5 if y<27 else 3 if y<39 else 2
            for z in range(cz-half,cz+half+1):
                for x in range(58,58+depth):edits[x,y,z]=state('cut_sandstone' if z==cz and x==57+depth else 'mud_bricks')
            if y in (12,26,38):
                for z in range(cz-half,cz+half+1):edits[57+depth,y+1,z]=stair('west','smooth_sandstone_stairs')
        for y in range(7,45):
            depth=7 if y<13 else 5 if y<27 else 3 if y<39 else 2
            if y not in (13,27,39):edits[58+depth,y,cz]=wall()
        for z in range(cz-1,cz+2):edits[59,48,z]=slab('smooth_sandstone_slab')
        commit(f'东侧收分扶壁 Z={cz}','east',edits,'加深原有扶垛的底部与退台，稀疏布置，原长窗和维修塔保留。','先接原基脚，按5格/3格宽和逐段退深搭芯；阶梯压顶朝西回接墙面。')
    edits={}
    for z in range(-32,-11):
        edits[58,46,z]=slab('smooth_sandstone_slab','top')
        if z%4==0:
            edits[58,45,z]=stair('west','smooth_sandstone_stairs','top')
            edits[59,46,z]=slab('smooth_sandstone_slab','top')
            edits[59,47,z]=stair('west','deepslate_tile_stairs')
    commit('东侧疏托檐与薄挑口','east',edits,'东面保持窄上窗，不复制北面整排盲拱；檐下只在间隔托架处再挑出一层。','原上部铁栏窄窗不动，托石在窗上方；薄檐按逐层图与原黑瓦边相接。')
    edits={};fixtures=[]
    for x in(21,30):
        edits[x,32,-46]=state('cut_sandstone')
        edits[x,31,-46]=state('iron_chain',axis='y',waterlogged='false')
        edits[x,30,-46]=state('lantern',hanging='true',waterlogged='false')
        edits[x,31,-45]=stair('south','smooth_sandstone_stairs','top')
        fixtures.append(dict(name=f'北墙中央壁柱挂灯 X={x}',pos=[x,30,-46],kind='石挑臂链挂灯',parts=[[x,30,-46],[x,31,-46]],supports=[[x,32,-46],[x,32,-45]]))
    commit('两盏中央壁柱挂灯','north',edits,'新灯落在两根中央壁柱上，原539个灯位保持；不是照亮全堡外墙的泛光保证。','先在壁柱前放实心石挑臂，下面接竖铁链与悬挂灯笼；不得换成红石光源。')
    # Reconcile only new/replaced narrow member states, against final neighbors.
    provisional={p for p in set(b)|set(e.blocks) if b.get(p)!=e.blocks.get(p)}
    for x,y,z in provisional:
        s=e.blocks.get((x,y,z))
        if not s or not s[0].endswith(('_wall','_fence')):continue
        n,pr,g=s;pr=dict(pr)
        for side,dx,dz in [('east',1,0),('west',-1,0),('north',0,-1),('south',0,1)]:
            nn=e.blocks.get((x+dx,y,z+dz),('',))[0]
            linked=nn in FULL or nn.endswith('_wall') if n.endswith('_wall') else nn in FULL or nn==n
            pr[side]=('low' if linked else 'none') if n.endswith('_wall') else str(linked).lower()
        e.blocks[x,y,z]=(n,pr,g)
    a=e.blocks;changed={p for p in set(b)|set(a) if b.get(p)!=a.get(p)}
    for f in features:
        positions=f.pop('positions');ps=positions&set(a);anchors={tuple(p[i]+dd[i] for i in range(3)) for p in ps for dd in DIRECTIONS if tuple(p[i]+dd[i] for i in range(3)) in a and tuple(p[i]+dd[i] for i in range(3)) not in ps}
        f.update(parts=sorted(ps),anchors=sorted(anchors),oldAnchors=sorted(p for p in anchors if b.get(p)==a[p]),
                 region=[v for i in range(3) for v in(min(p[i] for p in positions),max(p[i] for p in positions))],family='facade_v19')
    return dict(data=data,before=b,after=a,changed=changed,frozen=frozen,features=features,fixtures=fixtures,blindBacks=sorted(set(backs)),roofJoins=sorted(joins))
