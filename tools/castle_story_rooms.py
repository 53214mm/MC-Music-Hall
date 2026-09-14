"""V16 occupied room scenes with supported access; no new redstone mechanism.""" 
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_front import grid_route,route_cells
from castle_finish import EMISSION,spread_light
from castle_interior import RoomEditor,state,slab,stair,trap,barrel,support_errors
from castle_sample import validate_route
from castle_shortcuts import add,solid

REGIONS={'choir':(-7,21,17,26,58,86),'workshop':(69,74,14,23,40,52)}
ZONE_NAMES={'choir':'空席唱诗堂','workshop':'守曲人的维修夹廊'}
BRANCHES=[
 ('西席折返通路',[(8,16,78),(4,16,78),(4,16,66)],'interior_loop_link'),
 ('西北席旁支路',[(4,16,66),(4,16,60)],'interior_deadend'),
 ('东席折返通路',[(8,16,62),(12,16,62),(12,16,78),(8,16,78)],'interior_loop_link'),
 ('后殿独席支路',[(8,17,82),(11,17,82)],'interior_deadend'),
 ('维修夹廊工作环线',[(67,16,43),(71,16,43),(71,16,51),(67,16,51),(67,16,43)],'interior_loop')]
DIRS=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))
HORIZONTAL={'east':(1,0,0),'west':(-1,0,0),'south':(0,0,1),'north':(0,0,-1)}
OPPOSITE={'east':'west','west':'east','south':'north','north':'south'}


def frozen_cells(data,b):
    music={p for p,s in b.items() if s[2]=='control' or s[2].isdigit()}
    frozen={add(p,(dx,dy,dz)) for p in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    frozen.update(p for p,s in b.items() if s[2]=='terrain')
    for r in data['routes']:frozen.update((x,y+k,z) for x,y,z in route_cells(r['points'],r['width']) for k in range(4))
    for c in data['shortcutsV14']['shortcuts']:frozen.update((x,y+k,z) for x,y,z in c['points'] for k in range(4))
    # Includes S3 stair air and all control/QC cells, whether currently air or solid.
    for f in data['features']:
        r=f['region'];frozen.update((x,y,z) for x in range(r[0],r[1]+1) for y in range(r[2],r[3]+1) for z in range(r[4],r[5]+1))
    for f in data['fixtures']:frozen.update(map(tuple,f['parts']));frozen.update(map(tuple,f['supports']))
    for p,s in b.items():
        if s[0] in EMISSION:frozen.update((p,add(p,(0,1,0)),add(p,(0,-1,0))))
    return frozen


def wall(**sides):
    return state('sandstone_wall',up='true',north=sides.get('north','none'),south=sides.get('south','none'),east=sides.get('east','none'),west=sides.get('west','none'),waterlogged='false')


@lru_cache(maxsize=1)
def story_rooms():
    data,b=read_model(ROOT/'castle_v3/service_v15/castle_v15.json');frozen=frozen_cells(data,b)
    original_frozen=set(frozen)
    chairs={p for p,s in b.items() if s[0]=='spruce_stairs' and -7<=p[0]<=21 and p[1]==17 and 58<=p[2]<=76}
    table={(x,y,z) for x in(71,72) for y in(17,18) for z in range(45,49)}
    assert len(chairs)==14 and all(b[p][0]=='spruce_planks' for p in table)
    replaceable=chairs|table
    editor=RoomEditor(b,frozen,replaceable);features=[];fixtures=[]
    def commit(name,zone,parts,note,build):
        edits={p:s for p,s in parts.items() if editor.blocks.get(p)!=s}
        editor.apply(name,edits,REGIONS[zone])
        ps=[p for p,s in parts.items() if s is not None]
        if not ps:return
        # Anchors may be previously built V16 platform components; record old ones separately.
        anchors={add(p,dd) for p in ps for dd in DIRS if add(p,dd) not in ps and add(p,dd) in editor.blocks}
        features.append(dict(name=name,zone=zone,family='story_room',parts=sorted(ps),anchors=sorted(anchors),oldAnchors=sorted(q for q in anchors if q in b and b[q]==editor.blocks[q]),
                             region=[v for i in range(3) for v in(min(p[i] for p in ps),max(p[i] for p in ps))],note=note,build=build))
        for p in ps:
            if editor.blocks[p][0]=='lantern' and b.get(p,('',))[0]!='lantern':
                fixtures.append(dict(name=name+'灯',zone=zone,kind='家具实心座灯',pos=p,parts=[p],supports=[add(p,(0,-1,0))]))
    editor.apply('旧零散座椅',dict.fromkeys(chairs),REGIONS['choir'])
    editor.apply('旧厚木工台',dict.fromkeys(table),REGIONS['workshop'])
    # An actual 4x13 deck, carried by transverse beams into the old east wall.
    parts={}
    for x in range(70,74):
        for z in range(40,53):
            p=x,16,z
            if p not in editor.blocks:parts[p]=state('spruce_planks')
    for z in(42,50):
        for x in range(69,74):parts[x,15,z]=state('stripped_spruce_log',axis='x')
        parts[73,14,z]=stair('east','spruce_stairs','top')
    commit('接东墙的木工作夹层','workshop',parts,'厚工台下方原本没有完整楼板；新木平台以两道横梁接东墙，下面仍保留高低空间，不填满维修长廊。',
           '先沿Z42/50在Y15架X69…73横梁，Y14东端倒楼梯托臂靠X74旧墙；再补Y16的X70…73、Z40…52木板，已有原块保持。')
    # Guard the new deck's north/south drop edges, preserving old lamps.
    guard={}
    for z in(40,52):
        for x in range(70,74):
            p=x,17,z
            if p not in editor.blocks:guard[p]=wall(east='low',west='low')
    commit('工作平台端部护栏','workshop',guard,'北端和南端护栏围住新增平台，东面接原墙，西面接原主廊。旧三座灯柱都保留。','先做护栏和楼板，再打开主廊入口；旧灯座处不用再叠一面墙。')
    # Real paths are reserved before furnishing. Only one-block-high interior
    # walls on continuous same-height floors may be opened.
    routes=[dict(name=n,points=grid_route(ps),width=1,kind=kind) for n,ps,kind in BRANCHES]
    openings=set()
    for r in routes:
        for x,y,z in r['points']:
            if not solid(editor.blocks.get((x,y,z))):raise ValueError(('New room path has no real floor',r['name'],(x,y,z)))
            for k in(1,2,3):
                p=x,y+k,z;s=editor.blocks.get(p)
                if s is None:continue
                if k!=1 or not s[0].endswith('_wall') or p not in b:raise ValueError(('New room access blocked',r['name'],p,s))
                if not all(solid(editor.blocks.get((x+dx,y,z+dz))) for dx,dz in((0,0),(1,0),(-1,0),(0,1),(0,-1))):
                    raise ValueError(('Cannot remove a drop-edge rail',p))
                openings.add(p)
    replaceable.update(openings)
    for p in openings:
        zone='workshop' if p[0]>60 else 'choir';editor.apply('同高室内栏杆开口',{p:None},REGIONS[zone])
    rail_updates={}
    for p in sorted(openings):
        for name,dd in HORIZONTAL.items():
            q=add(p,dd);s=rail_updates.get(q,editor.blocks.get(q))
            if s and s[0].endswith('_wall') and s[1].get(OPPOSITE[name])!='none':
                rail_updates[q]=(s[0],{**s[1],OPPOSITE[name]:'none'},s[2])
    # Two new deck end rails join the existing gallery rail, not a disconnected cap.
    for z in(40,52):
        q=69,17,z;s=rail_updates.get(q,editor.blocks[q]);rail_updates[q]=(s[0],{**s[1],'east':'low'},s[2])
    for p,s in rail_updates.items():
        if s==b.get(p):continue
        replaceable.add(p);editor.apply('栏杆口收头与新平台接角',{p:s},REGIONS['workshop' if p[0]>60 else 'choir'])
    for r in routes:frozen.update((x,y+k,z) for x,y,z in r['points'] for k in range(4))
    # Pew backs and arms use thin, open trapdoors. South stair back -> look north.
    for side,rows,left,right in [('西',(61,70,76),-3,1),('东',(64,70,76),14,18)]:
        for z in rows:
            right_end=-1 if side=='西' and z==76 else right
            parts={}
            for x in range(left,right_end+1):
                parts[x,17,z]=stair('south');parts[x,18,z]=trap('north')
            for x,facing in [(left-1,'west'),(right_end+1,'east')]:parts[x,17,z]=trap(facing)
            lamp_x=right_end+1 if side=='西' else left-1
            parts[lamp_x,17,z]=state('cut_sandstone');parts[lamp_x,18,z]=state('lantern',hanging='false',waterlogged='false')
            commit(f'{side}侧Z{z}'+('缩短的空席' if right_end!=right else '薄背长席'),'choir',parts,
                   '长席朝向北侧音乐内堡，竖薄木背和端部灯座代替零散椅子；西南一排缩短，不把每一排复制成同样长度。',
                   'Y17朝南下半云杉楼梯形成面向北的座面，Y18同格北向打开活板门作薄背；端头切制砂岩上放落地灯，其余端头竖活板门。')
    parts={}
    for x in range(12,17):
        parts[x,18,84]=state('cut_sandstone')
    for x in(12,16):
        for y in range(19,23):parts[x,y,84]=wall()
        parts[x,23,84]=stair('east' if x==12 else 'west','smooth_sandstone_stairs','top')
        parts[x,18,83]=state('chiseled_sandstone');parts[x,19,83]=state('lantern',hanging='false',waterlogged='false')
    for x in(13,15):parts[x,24,84]=stair('east' if x==13 else 'west','smooth_sandstone_stairs','top')
    parts[14,25,84]=state('chiseled_sandstone');parts[14,26,84]=slab('smooth_sandstone_slab','bottom')
    # Solid backing bridges the arch tiers; no diagonal-floating arch pieces.
    for x in range(12,17):
        for y in range(18,24):parts[x,y,85]=state('tuff_bricks' if x in(12,16) else 'smooth_sandstone')
    for x in range(13,16):parts[x,24,85]=state('smooth_sandstone')
    parts[14,25,85]=state('smooth_sandstone')
    parts[14,19,84]=state('chiseled_sandstone');parts[14,20,84]=state('potted_oxeye_daisy')
    commit('后殿有花的纪念龛','choir',parts,'纪念龛偏在东侧，暖色新石框、旧色背板与一盆花形成被照看的痕迹；高挑中殿不填第二层地板。',
           'Y17原台基保持；先建Y18座和Z85背板，再立细墙柱、倒楼梯拱肩与拱顶。花盆落在Y19实心雕纹砂岩上，灯落在Y18侧座。')
    parts={(13,18,82):stair('south'),(13,19,82):trap('north'),(12,18,82):trap('west'),
           (14,18,82):trap('east'),(13,18,80):state('lectern',facing='north',powered='false',has_book='false')}
    commit('独席与空谱架','choir',parts,'一张独席不在长排中；面前的谱架暂空。没有伪造已放入乐谱或可读书本，玩家手建后可自行放书。','Y17台基上放南向楼梯椅及薄木背，北侧Z80放北向空讲台；X11新支路不摆家具。')
    parts={}
    for x in(72,73):
        for z in range(44,49):
            p=x,17,z
            parts[p]=b[p] if p in b and b[p][0]=='barrel' else barrel('west') if z in(44,48) else slab('oak_slab','top')
    parts[73,18,46]=state('grindstone',face='floor',facing='north')
    parts[72,18,48]=state('lantern',hanging='false',waterlogged='false')
    parts[72,17,42]=state('smithing_table')
    commit('磨石与薄木工台','workshop',parts,'原厚木堆换成桶柜承托的薄台面，一端仍有整块工具台，中间磨石表示维修用途；桶和工具台未预装物品。','先有Y16木平台，Y17摆端头桶柜、上半橡木台阶；原两只桶保留。Y18磨石放台面上，落地灯放实心端柜上。')
    parts={}
    for z in(50,52):
        for y in range(17,22):
            p=73,y,z
            parts[p]=editor.blocks[p] if y==17 and z==52 else b[p] if p in b and b[p][0]=='barrel' else state('stripped_spruce_log',axis='y')
    for z in range(50,53):parts[73,21,z]=state('stripped_spruce_log',axis='z')
    parts[73,17,51]=state('waxed_weathered_cut_copper');parts[73,18,51]=state('iron_bars',north='false',south='false',east='false',west='false',waterlogged='false')
    parts[73,19,51]=state('iron_bars',north='false',south='false',east='false',west='false',waterlogged='false')
    parts[72,17,50]=slab('waxed_weathered_cut_copper_slab','bottom')
    parts[72,17,51]=stair('west','waxed_weathered_cut_copper_stairs')
    parts[73,22,51]=state('lantern',hanging='false',waterlogged='false')
    commit('不同长度的备用金属件架','workshop',parts,'上蜡风化铜的短件、铁栏长件和原木架示意换下来的构件；这些是备用零件造景，不会发声，也不是新的红石电路。','架脚落在Y16平台，Z50旧桶保留；Y21原木横梁连接两侧立柱，Y22灯在横梁上。铜件不放进X71工作环线。')
    a=editor.blocks
    # A later rail joint adjustment may change an earlier feature's anchor.
    # Keep its physical adjacency, but do not label it an unchanged V15 block.
    for f in features:
        f['oldAnchors']=[p for p in f['oldAnchors'] if a.get(p)==b[p]]
    for r in routes:
        errors=validate_route(a,r['points'])
        if errors:raise ValueError((r['name'],errors[:8]))
    errors=support_errors(a,features)
    if errors:raise ValueError(('Unanchored room components',errors[:12]))
    changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
    return dict(data=data,before=b,after=a,changed=changed,frozen=original_frozen,replaceable=replaceable,
                chairs=chairs,oldTable=table,openings=sorted(openings),railUpdates=rail_updates,features=features,fixtures=fixtures,routes=routes)


@lru_cache(maxsize=1)
def story_lighting():
    m=story_rooms();fields={k:spread_light(m[k],{p:EMISSION[s[0]] for p,s in m[k].items() if s[0] in EMISSION}) for k in('before','after')}
    def stats(field,ps):
        vals=[field.get(p,0) for p in ps]
        return dict(samples=len(vals),minimum=min(vals),mean=round(sum(vals)/len(vals),2),zero=sum(v==0 for v in vals))
    old={(x,y+1,z) for r in m['data']['routes'] for x,y,z in route_cells(r['points'],r['width'])}
    old.update((x,y+1,z) for x,y,z in m['data']['serviceV15']['floorCells'] if (x,y+1,z) not in m['before'])
    for c in m['data']['shortcutsV14']['shortcuts']:
        old.update((x,y+1,z) for x,y,z in c['points'] if (x,y+1,z) not in set(map(tuple,c['gateParts'])))
    rows=[]
    for r in m['routes']:
        ps={(x,y+1,z) for x,y,z in r['points']}
        rows.append(dict(name=r['name'],kind=r['kind'],after=stats(fields['after'],ps),samples=[dict(pos=p,value=fields['after'].get(p,0)) for p in sorted(ps)]))
    return dict(before=stats(fields['before'],old),after=stats(fields['after'],old),newRoutes=rows,
                dimmerSamples=[dict(pos=p,before=fields['before'].get(p,0),after=fields['after'].get(p,0)) for p in sorted(old) if fields['after'].get(p,0)<fields['before'].get(p,0)],
                method='同V15保守六邻域建筑灯传播；旧43普通路线和三条捷径脚部采样均检查，不含天空光/反射/实际邻居更新/刷怪判定。')
