"""V17: dry supply traces and four distinct, accessible tower rooms."""
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_interior import RoomEditor,state,slab,stair,trap,barrel,support_errors
from castle_story_rooms import frozen_cells,DIRS,HORIZONTAL,OPPOSITE
from castle_front import grid_route,route_cells
from castle_sample import validate_route
from castle_shortcuts import add,solid
from castle_finish import EMISSION,spread_light

ZONES={'cistern':'退水后的旧蓄水池','beacon':'烽塔守望台','crown':'冠塔未带走的抄谱桌','north':'北阶塔换岗角','maintenance':'维修塔巡检阁'}
REGIONS={'cistern':(-42,-23,-12,-3,33,52),'beacon':(-59,-43,76,87,-51,-35),
         'crown':(-11,1,64,69,-26,-12),'north':(-29,-18,49,54,-54,-49),'maintenance':(62,74,54,61,-1,14)}
BRANCHES=[
 ('井底检水环线',[(-35,-12,48),(-39,-12,48),(-39,-12,36),(-27,-12,36),(-27,-12,54)],'interior_loop_link','cistern'),
 ('烽塔登高观景梯',[(-51,76,-43),(-51,76,-46),(-47,76,-46),(-47,80,-42),(-51,80,-42),(-55,84,-42),(-57,84,-42),(-57,84,-40),(-56,84,-40)],'interior_viewpoint','beacon'),
 ('冠塔抄谱桌支路',[(-1,64,-18),(-1,64,-20),(-6,64,-20),(-6,64,-22)],'interior_deadend','crown'),
 ('北阶塔换岗支路',[(-22,48,-47),(-22,48,-51),(-26,48,-51)],'interior_deadend','north'),
 ('维修塔一阶接入与巡检位',[(63,54,14),(64,54,14),(64,54,13),(65,55,13),(65,55,4),(70,55,4),(70,55,0)],'interior_deadend','maintenance')]


def sight_trace(blocks,start,end):
    """Conservative occupied-voxel sight segment, not a first-person renderer.

    Bars/glass/stairs count as full obstructing voxels; walls/fences extend to
    1.5 blocks. Exact segment/AABB intervals cannot skip a tiny corner contact.
    """
    delta=[end[i]-start[i] for i in range(3)];bounds=[(min(start[i],end[i]),max(start[i],end[i])) for i in range(3)]
    nearest=None;nearest_t=float('inf')
    for p,s in blocks.items():
        # Walls/fences extend above their containing voxel. Other irregular
        # blocks are deliberately over-approximated as a whole solid cube.
        height=1.5 if s[0].endswith(('_wall','_fence')) else 1.0
        sizes=(1,height,1)
        if any(p[i]>bounds[i][1] or p[i]+sizes[i]<bounds[i][0] for i in range(3)):continue
        lo,hi=0.0,1.0
        for i in range(3):
            if abs(delta[i])<1e-12:
                if not p[i]<=start[i]<=p[i]+sizes[i]:lo,hi=1,0;break
            else:
                t0=(p[i]-start[i])/delta[i];t1=(p[i]+sizes[i]-start[i])/delta[i]
                lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
                if lo>hi:break
        if lo<=hi and lo<nearest_t:nearest,nearest_t=p,lo
    return nearest


def bars(**sides):return state('iron_bars',waterlogged='false',**{k:str(sides.get(k,False)).lower() for k in HORIZONTAL})
def wall():return state('sandstone_wall',up='true',waterlogged='false',north='none',south='none',east='none',west='none')
def lamp():return state('lantern',hanging='false',waterlogged='false')


@lru_cache(maxsize=1)
def watchrooms():
    d,b=read_model(ROOT/'castle_v3/story_v16/castle_v16.json');frozen=frozen_cells(d,b);original_frozen=set(frozen)
    replaceable=set();ed=RoomEditor(b,frozen,replaceable);features=[];fixtures=[]
    def commit(name,zone,parts,note,build):
        edits={p:s for p,s in parts.items() if ed.blocks.get(p)!=s}
        ed.apply(name,edits,REGIONS[zone]);ps={p for p,s in parts.items() if s is not None}
        if not ps:return
        anchors={add(p,v) for p in ps for v in DIRS if add(p,v) not in ps and add(p,v) in ed.blocks}
        features.append(dict(name=name,zone=zone,family='watchroom',parts=sorted(ps),anchors=sorted(anchors),
            oldAnchors=sorted(q for q in anchors if q in b and b[q]==ed.blocks[q]),region=[v for i in range(3) for v in(min(p[i] for p in ps),max(p[i] for p in ps))],note=note,build=build))
        for p in sorted(ps):
            if ed.blocks[p][0]=='lantern' and b.get(p,('',))[0]!='lantern':fixtures.append(dict(name=name+'灯',zone=zone,kind='落地家具灯',pos=p,parts=[p],supports=[add(p,(0,-1,0))]))
    # Precisely restore the buried interior water line; not the external terrain.
    watermarks={( -42,y,z) for y in(-8,-7) for z in range(34,53)}
    assert all(b[p][0]=='tuff_bricks' and add(p,(1,0,0)) not in b for p in watermarks)
    replaceable.update(watermarks)
    commit('西壁退水留下的两道潮痕','cistern',{p:state('mossy_stone_bricks') for p in watermarks},
           '苔色只留在旧水位和进水口附近，池子仍是干的；不是把全地下室随机刷绿。','只换X-42内壁、Y-8/-7、Z34…52两行，墙厚和外侧岩体不改。')
    parts={}
    for z in(37,43):
        for y in range(-11,-6):parts[-41,y,z]=wall()
        parts[-41,-6,z]=stair('south' if z==37 else 'north','smooth_sandstone_stairs','top')
    for z,y in[(38,-6),(39,-5),(40,-4),(41,-5),(42,-6)]:
        parts[-41,y,z]=state('chiseled_sandstone') if z==40 else stair('south' if z<40 else 'north','smooth_sandstone_stairs','top')
        parts[-41,y-1,z]=state('smooth_sandstone')
    for z in range(39,42):
        parts[-41,-11,z]=state('tuff_bricks')
        for y in range(-10,-6):parts[-41,y,z]=bars(north=True,south=True)
        parts[-40,-11,z]=slab('tuff_brick_slab','bottom')
    parts[-40,-11,38]=stair('east','tuff_brick_stairs');parts[-40,-11,42]=state('chiseled_tuff_bricks');parts[-40,-10,42]=lamp()
    commit('被石屑封住的旧进水口','cistern',parts,'拱框内是堵住的格栅，下面是退水后留下的石屑；原墙背板保留，没有在地基开漏水洞。',
           'X-41贴原西墙立细柱与倒楼梯拱框，中间铁栏落在Y-11凝灰岩座上；X-40半砖/楼梯形成低石屑堆，灯放实心雕纹座。')
    # A repaired patch sits on the existing basin floor, not over a new pit.
    patch={(x,-12,z) for x in range(-32,-28) for z in range(47,51)}
    assert all(b[p][0]=='tuff_bricks' for p in patch);replaceable.update(patch)
    commit('井底检水角的后补木板','cistern',{p:state('spruce_planks') for p in patch},'小块木板落在旧池底上，是后来的检水工作角；没有填井筒，也不铺满整座水池。','只替换X-32…-29 / Y-12 / Z47…50共16格原池底，原下层支撑保持。')
    parts={(-31,-11,48):barrel('south'),(-30,-11,48):state('cauldron'),(-29,-11,48):barrel('south'),(-29,-10,48):lamp(),
           (-32,-11,49):slab('waxed_weathered_cut_copper_slab','bottom'),(-32,-11,50):stair('north','waxed_weathered_cut_copper_stairs')}
    commit('空检水盆与留下的铜件','cistern',parts,'空炼药锅和铜件说明这里曾检修供水；桶未填物品，盆里没有水。','Y-11摆桶与空炼药锅，短铜件直接落在木补板上；灯放桶顶。')
    # Supported observation staircase. Keep all Y76 visitor clearance intact.
    lookout=grid_route(BRANCHES[1][1]);new_floors={p for p in lookout if p[1]>76};floor_states={p:state('spruce_planks') for p in new_floors};parts={}
    for u,v in zip(lookout,lookout[1:]):
        if u[1]==v[1]:continue
        lo,hi=(u,v) if u[1]<v[1] else (v,u)
        facing={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}[hi[0]-lo[0],hi[2]-lo[2]]
        floor_states[hi]=stair(facing)
        q=hi[0],hi[1]-1,hi[2]
        if q not in b:parts[q]=state('stripped_spruce_log',axis='z' if hi[2]!=lo[2] else 'x')
    deck={(x,84,z) for x in range(-58,-54) for z in range(-45,-38)}
    for p in deck:floor_states.setdefault(p,state('spruce_planks'))
    for z in(-44,-40):
        for y in range(77,84):parts[-57,y,z]=state('stripped_spruce_log',axis='y')
    for x in range(-58,-54):
        for z in(-44,-40):parts[x,83,z]=state('stripped_spruce_log',axis='x')
    parts.update(floor_states)
    commit('跨过旧登塔线的双折木观景台','beacon',parts,'两段四级楼梯升到Y84，横跨处的桥面在原路线三格净空上方；木台有立柱、横梁和楼梯下斜撑，不靠悬浮方块。',
           '先从Y76原楼板立X-57、Z-44/-40两柱至Y83，架Y83横梁和Y84平台；随后建两段楼梯及下方斜向接木，Y80横桥不得向下填入原路线净空。')
    # Low one-block iron rails preserve the downward view; no wall-rail 1.5 height.
    guard=set()
    for x,y,z in deck:
        if x in(-58,-55) or z in(-45,-39):guard.add((x,y+1,z))
    guard.discard((-55,85,-42));parts={}
    for p in guard:parts[p]=bars(**{side:add(p,v) in guard for side,v in HORIZONTAL.items()})
    parts[-58,85,-44]=state('cut_sandstone');parts[-58,86,-44]=lamp()
    # Stair handrails lie alongside treads, never on the registered centerline.
    lookout_clear={(x,y+k,z) for x,y,z in lookout for k in range(4)}
    for x,y,z in lookout:
        if y>76 and (x,y,z) not in deck:
            sides=((-1,0,0),(1,0,0)) if x==-47 and z<-42 else ((0,0,-1),(0,0,1))
            for side in sides:
                q=add((x,y,z),side);top=add(q,(0,1,0))
                if {q,top}&(lookout_clear|frozen) or q in parts or q in ed.blocks or top in ed.blocks:continue
                parts[q]=state('spruce_planks');parts[top]=bars()
    commit('观景台低铁栏与梯边护挡','beacon',parts,'一格高铁栏防止平走出边，保留向下回望的视线；不声称能防主动跳跃。原石城垛不拆。',
           'Y85围平台外沿，仅在X-55/Z-42留楼梯口；下段梯边设贴着踏步的木边和铁栏。灯柱用实心砂岩。')
    parts={(-57,85,-44):stair('north'),(-57,86,-44):trap('south')}
    commit('向来路的一张守望椅','beacon',parts,'椅子与一盏灯朝南侧来路，不摆成新的宴会厅；看向门塔和唱诗堂屋脊的位置与施工路线一同登记。','南向座面由北向云杉楼梯形成，上一格南向打开活板门作薄背；椅子不能实际坐下。')
    # Correct the last gallery/tower discrepancy with a real step, outside V11 bay.
    p=(65,55,13);assert b[p][0]=='spruce_planks';replaceable.add(p)
    commit('巡检阁入口的一阶接高','maintenance',{p:stair('east')},'原外廊地板Y54，塔内楼板Y55。先沿旧梯内侧到Z13，再一步上到真楼板；Z14上方原塔墙不拆。','在(65,55,13)原木板处改东向下半云杉楼梯，从(64,54,13)踏入；原窗廊Z15…17不改。')
    # Reserve routes and open only backed, same-height rail cells.
    routes=[dict(name=n,points=grid_route(ps),width=1,kind=k) for n,ps,k,z in BRANCHES];openings=set()
    for r in routes:
        for x,y,z in r['points']:
            for k in(1,2,3):
                p=x,y+k,z;s=ed.blocks.get(p)
                if not s:continue
                if k!=1 or p not in b or not s[0].endswith('_wall'):raise ValueError(('New route occupied',r['name'],p,s))
                if not all(solid(ed.blocks.get((x+dx,y,z+dz))) for dx,dz in((0,0),(1,0),(-1,0),(0,1),(0,-1))):raise ValueError(('Drop-edge rail',p))
                openings.add(p)
    replaceable.update(openings)
    for p in openings:ed.apply('同高栏杆支路口',{p:None},(p[0],p[0],p[1],p[1],p[2],p[2]))
    rail_updates={}
    for p in openings:
        for side,delta in HORIZONTAL.items():
            q=add(p,delta);s=rail_updates.get(q,ed.blocks.get(q))
            if s and s[0].endswith('_wall') and s[1].get(OPPOSITE[side])!='none':rail_updates[q]=(s[0],{**s[1],OPPOSITE[side]:'none'},s[2])
    for p,s in rail_updates.items():replaceable.add(p);ed.apply('栏杆断口收头',{p:s},(p[0],p[0],p[1],p[1],p[2],p[2]))
    for r in routes:frozen.update((x,y+k,z) for x,y,z in r['points'] for k in range(4))
    # Crown: existing lamp, its base and all old books stay; only nine table blocks change.
    table={(x,65,z) for x in range(-8,-3) for z in(-25,-24)}
    approved={p for p in table if p not in frozen};assert all(b[p][0]=='spruce_planks' for p in approved);replaceable.update(approved)
    parts={p:slab('spruce_slab','top') for p in approved}
    parts[-4,65,-24]=state('lectern',facing='south',powered='false',has_book='false')
    parts[-8,65,-24]=barrel('south')
    parts[-6,65,-23]=stair('south');parts[-6,66,-23]=trap('north')
    commit('未带走的抄谱桌','crown',parts,'旧灯留在原木座上，厚桌换薄台面与一个空谱架；唯一座椅靠桌，仍不预装可读乐谱。','保留(-6,65,-25)灯座和上方旧灯，其他旧桌格按差异表换上半木台阶/桶/空讲台；Y65的Z-23放椅，Z-22来访支路不占。')
    parts={}
    for z in(-24,-12):parts[-10,65,z]=state('stripped_spruce_log',axis='y')
    for z in range(-24,-11):parts[-10,66,z]=slab('spruce_slab','bottom')
    parts[-9,65,-24]=barrel('east');parts[-9,66,-24]=lamp()
    commit('旧书架外的后补木框','crown',parts,'原11格书架完整留下，用低端框和半格薄顶收边，不立远高于书架的大木门框。','在旧书架X-10、Z-23…-13两端放Y65木柱，Y66下半木台阶沿Z-24…-12作薄顶；边桶落在Y64旧地板，灯在桶顶。')
    parts={}
    for x in range(-27,-23):parts[x,49,-53]=stair('north');parts[x,50,-53]=trap('south')
    parts[-23,49,-53]=state('cut_sandstone');parts[-23,50,-53]=lamp()
    commit('交通节点旁的换岗短凳','north',parts,'短凳朝来人方向，留给走阶的人停一下；主通道仍能直接分向冠塔与烽塔。','在Y48旧地板上摆北向楼梯座与薄背，东端落地灯。新支路位于Z-51，不摆行李。')
    parts={(-19,49,-52):barrel('west'),(-19,50,-52):state('stripped_spruce_log',axis='y'),(-19,51,-52):state('stripped_spruce_log',axis='y'),
           (-19,52,-52):state('stripped_spruce_log',axis='z'),(-19,52,-51):state('stripped_spruce_log',axis='z'),(-19,51,-51):state('iron_chain',axis='y',waterlogged='false')}
    commit('空挂具与换下的行李桶','north',parts,'一处空铁链挂钩与行李桶，不伪造披风实体。这里是短暂停留位，不是另一间寝室。','桶上立柱，Y52短横臂接Y51铁链；不接红石，不加实体。')
    parts={(72,56,2):barrel('west'),(72,56,3):slab('oak_slab','top'),(72,56,4):barrel('west'),(72,57,4):lamp(),
           (72,57,2):state('grindstone',face='floor',facing='north'),(72,56,7):stair('east'),(72,57,7):trap('west')}
    commit('巡检阁的小修台与向内堡的椅子','maintenance',parts,'塔下大工坊修零件，塔上只留小修台与单椅。磨石、备用灯和朝向内堡的停留位让上下两层用途不同。','Y55原塔板保持，小台在X72/Z2…4、单席在Z7；磨石落桶顶，灯落另一端桶顶，X70支路保持空。')
    # A few low reading/supply lamps along new paths, all on old or new full floors.
    for zone,x,y,z in [('cistern',-39,-11,34),('cistern',-25,-11,36),('cistern',-25,-11,46),('beacon',-46,77,-48),('maintenance',69,56,0)]:
        commit(ZONES[zone]+f'侧座灯{x}_{z}',zone,{(x,y,z):state('chiseled_tuff_bricks'),(x,y+1,z):lamp()},'只在停留节点补暖灯，不改原灯、不用发光方块填满墙面。','底座必须有原完整楼板支撑，实心座上放落地灯。')
    a=ed.blocks
    # Only new iron-bar/wall states are normalized against final neighbors.
    # Existing frozen blocks are never adjusted.
    for p,s in list(a.items()):
        if p in b or s[0] not in('iron_bars','sandstone_wall'):continue
        joins={side:bool(a.get(add(p,v)) and (a[add(p,v)][0]==s[0] or solid(a[add(p,v)]))) for side,v in HORIZONTAL.items()}
        props={**s[1],**{side:('low' if yes else 'none') if s[0].endswith('_wall') else str(yes).lower() for side,yes in joins.items()}}
        a[p]=(s[0],props,s[2])
    for f in features:f['oldAnchors']=[p for p in f['oldAnchors'] if a.get(p)==b[p]]
    for r in routes:
        errors=validate_route(a,r['points'])
        if errors:raise ValueError((r['name'],errors[:12]))
    errors=support_errors(a,features)
    if errors:raise ValueError(('Unsupported features',errors[:12]))
    eye=(-56.5,86.62,-39.5);views=[]
    for name,x,z in [('东门塔屋冠',-28,104),('唱诗堂屋脊',7,71)]:
        y=max(q[1] for q in a if q[0]==x and q[2]==z);target=(x+.5,y+1.01,z+.5)
        hit=sight_trace(a,eye,target)
        if hit:raise ValueError(('Lookout cannot see nominated landmark',name,hit,a[hit]))
        views.append(dict(name=name,eye=eye,target=target,targetBlock=(x,y,z),method='占用格保守射线；栏/楼梯/玻璃按整格遮挡，未模拟游戏视角、纹理或外部世界地形。'))
    changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
    return dict(data=d,before=b,after=a,changed=changed,frozen=original_frozen,replaceable=replaceable,features=features,fixtures=fixtures,
                routes=routes,openings=sorted(openings),railUpdates=rail_updates,watermarks=watermarks,lookoutFloor=deck|new_floors,views=views)


@lru_cache(maxsize=1)
def watch_lighting():
    m=watchrooms();fields={key:spread_light(m[key],{p:EMISSION[s[0]] for p,s in m[key].items() if s[0] in EMISSION}) for key in('before','after')}
    def stats(field,ps):
        vals=[field.get(p,0) for p in ps];return dict(samples=len(vals),minimum=min(vals),mean=round(sum(vals)/len(vals),2),zero=sum(v==0 for v in vals))
    ps={(x,y+1,z) for r in m['data']['routes'] for x,y,z in route_cells(r['points'],r['width'])}
    ps.update((x,y+1,z) for x,y,z in m['data']['serviceV15']['floorCells'] if (x,y+1,z) not in m['before'])
    for c in m['data']['shortcutsV14']['shortcuts']:ps.update((x,y+1,z) for x,y,z in c['points'] if (x,y+1,z) not in set(map(tuple,c['gateParts'])))
    rows=[]
    for r in m['routes']:
        pts={(x,y+1,z) for x,y,z in r['points']};rows.append(dict(name=r['name'],kind=r['kind'],after=stats(fields['after'],pts),samples=[dict(pos=p,value=fields['after'].get(p,0)) for p in sorted(pts)]))
    return dict(before=stats(fields['before'],ps),after=stats(fields['after'],ps),newRoutes=rows,
        dimmerSamples=[dict(pos=p,before=fields['before'].get(p,0),after=fields['after'].get(p,0)) for p in sorted(ps) if fields['after'].get(p,0)<fields['before'].get(p,0)],
        method='保守六邻域建筑灯传播，旧48普通路线及三捷径脚部采样；不含天空光/反射/实际更新/刷怪判定。')
