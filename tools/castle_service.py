"""V15 real service stair/corridor and one bounded, inverted sticky-piston latch.

No dynamic Minecraft event simulation. Steady states are checked against target
bytecode; movement and world reload still require an isolated game test.
"""
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_front import grid_route,route_cells
from castle_finish import EMISSION,protected
from castle_interior import RoomEditor
from castle_sample import validate_route
from castle_shortcuts import state,solid,add,wire_states,graph_distance,player_collisions

PATH=grid_route([(55,16,58),(55,16,54),(55,1,39),(55,1,5)])
WIRE=[(59,3,26),(59,4,27)]+[(59,5,z) for z in range(28,33)]
DIRS=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))
P=(55,5,32);HEAD=(55,4,32);STONE=(55,3,32);T=(56,5,32);C=(57,5,32);R=(58,5,32)
L=(57,3,26);A=(58,3,26)
QUERY=[(54,5,32),T,(55,5,31),(55,5,33),(55,6,32),P,(54,6,32),(56,6,32),(55,6,31),(55,6,33),(55,7,32)]
REACTIVE={'redstone_wire','redstone_block','redstone_torch','redstone_wall_torch','repeater','comparator','observer','lever','piston','sticky_piston','piston_head','moving_piston','note_block','daylight_detector','target'}
LAYOUT=dict(lever=L,leverMount=A,wire=WIRE,repeater=R,outputBlock=C,torch=T,piston=P,head=HEAD,stone=STONE)


def service_wire_states():
    result=wire_states(WIRE)
    # Actual west-hand repeater is a connecting neighbor, unlike a passive end block.
    result[WIRE[-1]]=state('redstone_wire',north='side',west='side',east='none',south='none',power='0')
    return result


def service_isolation(before,after):
    """Exclude foreign active/responsive blocks around inputs AND direct/QC sources.

    The two-cell expansion does not depend on a decorative block conductor
    whitelist: a source beyond a substituted cobblestone QC neighbor is caught.
    This bounded design has only a single conducting-block hop, not a world sim.
    """
    own={L,R,T,P,HEAD,STONE,*WIRE}
    influence={*own,A,C,*QUERY,*(add(q,(0,-1,0)) for q in WIRE)}
    nearby={add(p,(dx,dy,dz)) for p in influence for dx in range(-2,3) for dy in range(-2,3) for dz in range(-2,3)}
    reactive=REACTIVE|{'dispenser','dropper','hopper','tnt','redstone_lamp','powered_rail','activator_rail','detector_rail','tripwire_hook','lectern','lightning_rod','sculk_sensor','calibrated_sculk_sensor','trapped_chest'}
    foreign=[dict(pos=p,name=after[p][0]) for p in sorted(nearby-own) if p in after and
             (after[p][0] in reactive or after[p][0].endswith(('_button','_pressure_plate','_door','_trapdoor','_fence_gate')))]
    if foreign:raise ValueError(('Unreviewed source/response around S3',foreign))
    music=[p for p,s in before.items() if s[2]=='control' or s[2].isdigit()]
    distance=min((max(abs(p[i]-q[i]) for i in range(3)) for p in influence for q in music),default=None)
    if distance is not None and distance<=2:raise ValueError('S3 too close to old music')
    return dict(influenceCells=sorted(influence),foreignResponsive=foreign,minimumMusicChebyshev=distance,
                limitation='two-cell exclusion around full explicit input/output/QC neighborhood, not arbitrary world/update simulation')


def stair_profile(blocks):
    """Centerline surface profile on the stated full blocks / south bottom stairs.

    Samples each northern/southern half-cell. This checks half-step risers, not
    full avatar dynamics, edge handling, sprinting or event timing.
    """
    values=[]
    for x,y,z in PATH:
        s=blocks.get((x,y,z))
        if s==stair():heights=(y+1,y+.5)
        elif solid(s):heights=(y+1,y+1)
        else:raise ValueError(('Unsupported path surface',x,y,z,s))
        values.extend([dict(pos=(x+.5,heights[0],z+.75)),dict(pos=(x+.5,heights[1],z+.25))])
    rises=[abs(u['pos'][1]-v['pos'][1]) for u,v in zip(values,values[1:])]
    if max(rises)>.5:raise ValueError('More than half-block riser')
    return dict(maxRiser=max(rises),halfRisers=sum(v==.5 for v in rises),samples=values,
                limitation='half-cell centerline profile, combined with separate three-air route checks; no full stair traversal simulation')


def stair(facing='south',half='bottom',name='smooth_sandstone_stairs'):
    return state(name,facing=facing,half=half,shape='straight',waterlogged='false')


def validate_service_routes(blocks):
    errors=[]
    # Only latch's three rows have a declared two-high, one-wide portal.
    for dx in(-1,0,1):
        for lo,hi in((34,58),(5,30)):
            segment=[(x+dx,y,z) for x,y,z in PATH if lo<=z<=hi]
            errors.extend(validate_route(blocks,segment))
    for z in range(31,34):
        for x in(54,55,56):
            if not solid(blocks.get((x,1,z))):errors.append(f'Missing latch floor {(x,1,z)}')
    return errors


def latch_collisions(blocks):
    return player_collisions(blocks,[(55.5,2,35.5),(55.5,2,28.5)])


def evaluate_latch(blocks,c,on):
    """Validate this explicit circuit, then evaluate two held-input steady states."""
    for k,v in LAYOUT.items():
        actual=list(map(tuple,c.get(k,[]))) if k=='wire' else tuple(c.get(k,()))
        if actual!=v:raise ValueError(('Manifest does not match checked S3 layout',k))
    service_isolation({},blocks)
    if blocks.get(L)!=state('lever',face='wall',facing='west',powered=blocks.get(L,('',{},''))[1].get('powered','')):
        raise ValueError('Wrong real lever attachment/direction')
    if not solid(blocks.get(A)) or not solid(blocks.get(C)):raise ValueError('Missing conducting lever/torch mount')
    for p,expected in service_wire_states().items():
        s=blocks.get(p)
        if not s or s[0]!='redstone_wire' or not solid(blocks.get(add(p,(0,-1,0)))):raise ValueError(('Missing wire/support',p))
        if any(s[1].get(k)!=expected[1][k] for k in ('north','south','east','west')):raise ValueError(('Wrong wire shape',p))
    for p in ((59,4,26),(59,5,27)):
        if p in blocks:raise ValueError(('Blocked rising wire',p))
    r=blocks.get(R)
    if not r or r[0]!='repeater' or r[1].get('facing')!='east' or r[1].get('locked')!='false' or r[1].get('delay')!='1' or not solid(blocks.get(add(R,(0,-1,0)))):
        raise ValueError('Repeater must read east and output west, one delay')
    t=blocks.get(T)
    if not t or t[0]!='redstone_wall_torch' or t[1].get('facing')!='west':raise ValueError('Wall torch must attach east, facing west')
    p=blocks.get(P)
    if not p or p[0]!='sticky_piston' or p[1].get('facing')!='down' or p[1].get('extended') not in ('true','false'):
        raise ValueError('Missing downward sticky piston')
    closed=p[1]['extended']=='true'
    current_on=not closed
    if blocks[L][1].get('powered')!=str(current_on).lower() or r[1].get('powered')!=str(current_on).lower() or t[1].get('lit')!=str(closed).lower():
        raise ValueError('Saved lever/repeater/torch/piston states are not a consistent held-input steady state')
    for i,q in enumerate(WIRE):
        if blocks[q][1].get('power')!=str(15-i if current_on else 0):raise ValueError(('Inconsistent saved dust power',q))
    if closed:
        if blocks.get(HEAD)!=state('piston_head',facing='down',type='sticky',short='false') or blocks.get(STONE)!=state('chiseled_sandstone'):
            raise ValueError('Closed state needs matching complete sticky head and single latch stone')
    elif blocks.get(HEAD)!=state('chiseled_sandstone') or STONE in blocks:
        raise ValueError('Open state must retract exactly one stone to Y4')
    if (55,2,32) in blocks:raise ValueError('Extra block below latch travel')
    for q in {add(p,d) for p in (HEAD,STONE) for d in DIRS}:
        if blocks.get(q,('',))[0] in ('slime_block','honey_block','moving_piston'):raise ValueError('Foreign sticky/moving block beside stroke')
    for x in (54,56):
        for y in (2,3):
            if not solid(blocks.get((x,y,32))):raise ValueError('Latch can be bypassed beside its jambs')
    # Every direct/QC source cell, plus six neighbors when it is conductive.
    inspected=set(QUERY)
    for q in QUERY:
        if solid(blocks.get(q)):inspected.update(add(q,d) for d in DIRS)
    own={P,T,R,L,HEAD,STONE,*WIRE}
    for q in inspected-own:
        s=blocks.get(q)
        if s and (s[0] in REACTIVE or s[0].endswith(('_button','_pressure_plate'))):
            raise ValueError(('Unreviewed direct/QC input',q,s[0]))
    # Directly charged full blocks: only dust below, repeater output, lever mount.
    charged=({A,C}|{add(q,(0,-1,0)) for q in WIRE}) if on else set()
    torch_lit=not on
    if torch_lit:charged.add(add(T,(0,1,0)))
    powering=[q for q in QUERY if q==T and torch_lit or solid(blocks.get(q)) and q in charged]
    extended=bool(powering)
    if extended==on:raise ValueError(('Input bypasses the inversion',powering))
    return dict(wirePower=[15-i if on else 0 for i in range(7)],repeaterPowered=bool(on),torchLit=torch_lit,
                pistonExtended=extended,poweringQueryCells=powering,queryCells=QUERY,
                method='bounded held-input steady-state calculation; not events, short pulses, movement or game reload')


def service_variant(blocks,c,on):
    result=dict(blocks);v=evaluate_latch(blocks,c,on)
    for p,props in [(L,{'powered':str(on).lower()}),(R,{'powered':str(on).lower()}),(T,{'lit':str(not on).lower()}),(P,{'extended':str(not on).lower()})]:
        n,pr,g=result[p];result[p]=(n,{**pr,**props},g)
    for p,power in zip(WIRE,v['wirePower']):n,pr,g=result[p];result[p]=(n,{**pr,'power':str(power)},g)
    if on:result[HEAD]=state('chiseled_sandstone');result.pop(STONE,None)
    else:result[HEAD]=state('piston_head',facing='down',type='sticky',short='false');result[STONE]=state('chiseled_sandstone')
    return result


@lru_cache(maxsize=1)
def service_castle():
    data,b=read_model(ROOT/'castle_v3/shortcuts_v14/castle_v14.json')
    music={p for p,s in b.items() if s[2]=='control' or s[2].isdigit()}
    frozen={add(p,(dx,dy,dz)) for p in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    frozen.update(p for p,s in b.items() if s[2]=='terrain')
    for r in data['routes']:frozen.update((x,y+k,z) for x,y,z in route_cells(r['points'],r['width']) for k in range(4))
    for c in data['shortcutsV14']['shortcuts']:frozen.update((x,y+k,z) for x,y,z in c['points'] for k in range(4))
    for f in data['fixtures']:frozen.update(map(tuple,f['parts']));frozen.update(map(tuple,f['supports']))
    for p,s in b.items():
        if s[0] in EMISSION:frozen.update((p,add(p,(0,1,0)),add(p,(0,-1,0))))
    for f in data['features']:
        r=f['region'];frozen.update((x,y,z) for x in range(r[0],r[1]+1) for y in range(r[2],r[3]+1) for z in range(r[4],r[5]+1))
    edits={};fixtures=[];roof_kept=[]
    def get(p):return edits.get(p,b.get(p))
    def put(p,s,keep=False):
        if keep and get(p):return
        edits[p]=s
    floors=route_cells(PATH,3);air={(x,y+k,z) for x,y,z in floors for k in (1,2,3)}
    stairs={}
    for u,v in zip(PATH,PATH[1:]):
        if u[1]!=v[1]:
            high=max((u,v),key=lambda p:p[1])
            for dx in (-1,0,1):stairs[high[0]+dx,high[1],high[2]]='south'
    for p in sorted(floors):
        put(p,stair() if p in stairs else state('tuff_bricks'),keep=p not in stairs)
        below=add(p,(0,-1,0))
        if not get(below):put(below,state('tuff_bricks'))
    for p in air:
        if get(p):put(p,None)
    # Full-depth side walls enclose the descending stair; old surfaces stay where possible.
    for x,y,z in PATH:
        if z<7 or z>55:continue
        for sx in (53,57):
            for k in range(0,4):
                put((sx,y+k,z),state('cut_sandstone' if k==1 and z%7==0 else 'mud_bricks'),keep=True)
            # A thin coping above each side is outside the full-width walking air.
            put((sx,y+4,z),state('cut_sandstone_slab',type='bottom',waterlogged='false'),keep=True)
        for sx in(54,55,56):
            p=sx,y+4,z
            if p in frozen:roof_kept.append(p);continue
            put(p,state('mud_bricks'),keep=True)
    # Garden opening protection. No new rails in the original main-path air at Z57..59.
    for x in(53,57):
        for z in range(50,56):
            put((x,17,z),state('sandstone_wall',up='true',north='low',south='low',east='none',west='none',waterlogged='false'),keep=True)
    # Repair canopy: log posts and beam, steep stair/slab roof, standing outside old main route.
    for x in (53,57):
        for y in range(17,21):put((x,y,55),state('stripped_spruce_log',axis='y'))
    for x in range(53,58):put((x,20,55),state('stripped_spruce_log',axis='x'))
    for x in range(52,59):
        for z in range(54,57):
            y=23-abs(x-55)
            put((x,y,z),state('deepslate_tile_slab',type='bottom',waterlogged='false') if x==55 else stair('east' if x<55 else 'west',name='deepslate_tile_stairs'))
            for yy in range(21,y):put((x,yy,z),state('spruce_planks'))
    # Correct both railing ends around the new, supported three-wide mouths.
    ends=[(x,y,z) for x in(53,57) for y,z in((2,6),(17,56))]
    for p in ends:
        s=b[p];props=dict(s[1]);props['east' if p[0]==53 else 'west']='none'
        props['south' if p[2]==6 else 'north']='low';put(p,(s[0],props,s[2]))
    # Latch pocket and one-cell-wide jamb. All motion is at Y3/Y4 above a flat floor.
    for x in (54,56):
        for y in (2,3,4):put((x,y,32),state('cut_sandstone'))
    put(P,state('sticky_piston',facing='down',extended='true'))
    put(HEAD,state('piston_head',facing='down',type='sticky',short='false'));put(STONE,state('chiseled_sandstone'))
    put((55,2,32),None);put((55,6,32),state('cut_sandstone'),keep=True)
    for x in range(53,58):put((x,7,32),state('tuff_bricks'),keep=True)
    put(C,state('cut_sandstone'));put(T,state('redstone_wall_torch',facing='west',lit='true'))
    put(R,state('repeater',facing='east',delay='1',locked='false',powered='false'))
    put(add(R,(0,-1,0)),state('cut_sandstone'),keep=True)
    put(A,state('cut_sandstone'));put(L,state('lever',face='wall',facing='west',powered='false'))
    put(add(A,(0,-1,0)),state('cut_sandstone'),keep=True)
    for p,s in service_wire_states().items():
        put(p,s)
        support=add(p,(0,-1,0));put(support,state('cut_sandstone'),keep=True)
        # New early wire pedestals continue down to an old floor, at most six cells.
        for dy in range(2,8):
            q=add(p,(0,-dy,0))
            if get(q):break
            put(q,state('tuff_bricks'))
    for p in ((59,4,26),(59,5,27)):put(p,None)
    # Six genuine recessed warm lamps, never inside the 3-wide route volume.
    for z in (10,18,26,36,44,51):
        h=next(y for x,y,zz in PATH if zz==z);p=53,h+2,z;support=53,h+1,z
        put(support,state('cut_sandstone'));put(p,state('lantern',hanging='false',waterlogged='false'))
        fixtures.append(dict(name=f'S3维修道灯 Z{z}',zone='S3',kind='侧龛灯',pos=p,parts=[support,p],supports=[(53,h,z)]))
    # Only actual changes go to the frozen editor; keep identical old/frozen cells.
    edits={p:s for p,s in edits.items() if s!=b.get(p)}
    replaceable=set(edits)&set(b)
    e=RoomEditor(b,frozen,replaceable);e.apply('S3庭院下维修道',edits,(52,59,-4,23,5,58));a=e.blocks
    errors=validate_service_routes(a)
    if errors:raise ValueError(('S3 stair/landing clearance',errors[:10]))
    c=dict(id='S3',name='庭院下维修道与升降石闩',kind='inverted_sticky_latch',points=PATH,nominalFloorWidth=3,portalWidth=1,
           lever=L,leverMount=A,wire=WIRE,repeater=R,outputBlock=C,torch=T,piston=P,head=HEAD,stone=STONE,
           default='closed',ordinaryGraphSteps=graph_distance(data['routes'],PATH[0],PATH[-1]),shortcutGraphSteps=len(PATH)-1,
           controlStanding=(55,1,26),reachLowerBound=round(STONE[2]+1+.3-(L[2]+1),4),
           discovery='首次沿东长廊下旧阶梯到音乐门厅，向南进入维修道，在Z26拨拉杆，再向南过石闩、上新阶梯返回庭院。')
    c['off']=evaluate_latch(a,c,False);c['on']=evaluate_latch(a,c,True)
    if not latch_collisions(a) or latch_collisions(service_variant(a,c,True)):raise ValueError('Latch sweep does not match states')
    return dict(data=data,before=b,after=a,changed=set(edits),frozen=frozen,replaceable=replaceable,
                shortcut=c,fixtures=fixtures,railEnds=ends,floorCells=sorted(floors),stairCells=sorted(stairs),roofPreserved=roof_kept)
