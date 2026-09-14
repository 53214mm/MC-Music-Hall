"""Two bounded, latched vanilla shortcuts. Static checks are NOT Minecraft runtime."""
import math
from collections import deque
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_front import route_cells,grid_route
from castle_finish import protected,EMISSION
from castle_sculpt import FULL
from castle_interior import RoomEditor

DIR={'east':(1,0,0),'west':(-1,0,0),'south':(0,0,1),'north':(0,0,-1)}
OPP={'east':'west','west':'east','south':'north','north':'south'}
S1_WIRE=[(-35,5,z) for z in range(53,58)]+[(-35,4,58),(-34,3,58),(-33,2,58),(-32,1,58)]
S2_WIRE=[(-47,34,z) for z in range(-4,3)]


def state(n,**props):return(n,props,'shell')
def add(p,d):return tuple(p[i]+d[i] for i in range(3))
def solid(s):return bool(s and (s[0] in FULL or s[0] in('oak_planks',)))


def wire_states(path):
    result={}
    for i,p in enumerate(path):
        props={k:'none' for k in DIR};props['power']='0'
        for q in path[max(0,i-1):i]+path[i+1:i+2]:
            direction=next(k for k,d in DIR.items() if (q[0]-p[0],q[2]-p[2])==(d[0],d[2]))
            props[direction]='up' if q[1]>p[1] else 'side'
        connected=[k for k in DIR if props[k]!='none']
        if len(connected)==1:props[OPP[connected[0]]]='side'
        result[p]=state('redstone_wire',**props)
    return result


def evaluate_circuit(blocks,c,on):
    """Validate these two explicit topologies; compute ONLY their steady-state power.

    No general update-order, torch, pulse, chunks, or event simulation. Direction
    rules are cross-checked against this user's target-version bytecode.
    """
    validate_portal(blocks,c)
    wire=list(map(tuple,c['wire']));lever=tuple(c['lever']);mount=tuple(c['leverMount'])
    s=blocks.get(lever)
    if not s or s[0]!='lever' or s[1].get('face')!='wall' or add(lever,DIR[OPP[s[1]['facing']]])!=mount:
        raise ValueError('Lever must face away from its actual mounting block')
    if not solid(blocks.get(mount)):raise ValueError('Lever mount is not solid')
    if sum(abs(wire[0][i]-mount[i]) for i in range(3))!=1:raise ValueError('Source wire is not adjacent to the strongly powered mount')
    levels=[];expected=wire_states(wire)
    for i,p in enumerate(wire):
        if blocks.get(p,('',))[0]!='redstone_wire' or not solid(blocks.get((p[0],p[1]-1,p[2]))):
            raise ValueError(f'Missing wire or support: {p}')
        if any(blocks[p][1].get(k)!=expected[p][1][k] for k in DIR):
            raise ValueError(f'Wrong declared dust connection: {p}')
        if i:
            q=wire[i-1]
            if abs(p[0]-q[0])+abs(p[2]-q[2])!=1 or abs(p[1]-q[1])>1:raise ValueError('Disconnected wire')
            if p[1]!=q[1]:
                low=min((p,q),key=lambda v:v[1]);head=add(low,(0,1,0))
                if head in blocks:raise ValueError(f'Blocked dust step: {head}')
        levels.append(max(0,15-i) if on else 0)
    if on and levels[-1]==0:raise ValueError('Signal exhausted')
    target=tuple(c['outputBlock'])
    if not solid(blocks.get(target)):raise ValueError('Output block does not conduct')
    if c.get('repeater'):
        p=tuple(c['repeater']);s=blocks.get(p)
        if not s or s[0]!='repeater' or add(p,DIR[s[1]['facing']])!=wire[-1] or add(p,DIR[OPP[s[1]['facing']]])!=target:
            raise ValueError('Repeater FACING must point to its INPUT, not output')
        if s[1].get('locked')!='false' or not solid(blocks.get(add(p,(0,-1,0)))):raise ValueError('Invalid repeater support/lock')
        output=15 if on else 0
    else:
        if target!=add(wire[-1],(0,-1,0)):raise ValueError('S2 output is the wire support directly below it')
        output=levels[-1]
    gate=tuple(c['gate'])
    if sum(abs(gate[i]-target[i]) for i in range(3))!=1:raise ValueError('Gate is not adjacent to powered block')
    return dict(wirePower=levels,outputPower=output,open=bool(output),method='validated bounded steady state; not runtime')


def validate_portal(blocks,c):
    """Check actual gates, continuous climbable blocks and solid supporting faces."""
    gate=tuple(c['gate']);s=blocks.get(gate)
    if not s:raise ValueError('Missing gate')
    n,p,g=s
    if c['kind']=='door':
        upper=add(gate,(0,1,0));u=blocks.get(upper)
        if n!='iron_door' or p.get('half')!='lower' or not u or u[0]!='iron_door' or u[1].get('half')!='upper':
            raise ValueError('Iron door needs both real halves')
        if set(map(tuple,c['gateParts']))!={gate,upper} or any(p.get(k)!=u[1].get(k) for k in ('facing','hinge','open','powered')):
            raise ValueError('Inconsistent door halves')
        if p.get('facing')!='north' or p.get('hinge')!='left' or not solid(blocks.get(add(gate,(0,-1,0)))):
            raise ValueError('S1 door orientation/support changed')
    else:
        if n!='iron_trapdoor' or p.get('facing')!='east' or p.get('half')!='bottom' or list(map(tuple,c['gateParts']))!=[gate]:
            raise ValueError('S2 hatch orientation/type changed')
        x,top,z=gate
        for y in range(c['ladderBottom'],top):
            q=x,y,z;t=blocks.get(q)
            if not t or t[0]!='ladder' or t[1].get('facing')!=p['facing'] or not solid(blocks.get(add(q,DIR[OPP[p['facing']]]))):
                raise ValueError(f'Invalid ladder or backing: {q}')
    if p.get('open') not in ('true','false') or p.get('open')!=p.get('powered'):
        raise ValueError('Gate must represent a consistent steady state')


def variant(blocks,c,on):
    r=evaluate_circuit(blocks,c,on);result=dict(blocks)
    edits={tuple(c['lever']):{'powered':str(on).lower()}}
    edits.update({tuple(p):{'power':str(v)} for p,v in zip(c['wire'],r['wirePower'])})
    if c.get('repeater'):edits[tuple(c['repeater'])]={'powered':str(on).lower()}
    for p in map(tuple,c['gateParts']):edits[p]={'open':str(on).lower(),'powered':str(on).lower()}
    for p,props in edits.items():n,q,g=result[p];result[p]=(n,{**q,**props},g)
    return result


@lru_cache(maxsize=None)
def thin_boxes(n,props):
    # Actual panel collision rules from target-version getShape, NOT texture holes.
    p=dict(props);direction=p['facing'];t=3/16
    vertical={'north':(0,1,0,1,1-t,1),'east':(0,t,0,1,0,1),
              'south':(0,1,0,1,0,t),'west':(1-t,1,0,1,0,1)}
    if n=='iron_trapdoor':
        if p['open']=='true':return [vertical[direction]]
        return [(0,1,0,t,0,1) if p['half']=='bottom' else (0,1,1-t,1,0,1)]
    if n=='iron_door':
        if p['open']=='true':
            order=['north','east','south','west'];direction=order[(order.index(direction)+(1 if p['hinge']=='left' else -1))%4]
        return [vertical[direction]]
    if n=='ladder':return [vertical[direction]]
    raise ValueError('Unsupported thin collision block')


def interaction_lower_bound(c):
    """Distance from specified closed approach eye-volume to WHOLE lever cell.

    Whole-cell target is more permissive than the lever shape. This is a bound
    for the designated approach, not proof against breaking/flying/other exploits.
    """
    x,y,z=c['gate'];lx,ly,lz=c['lever']
    if c['id']=='S1':
        # Closed north-facing panel's south edge is z+1; body radius is .3.
        return round(z+1+.3-(lz+1),4)
    # Closed bottom hatch underside y; 1.8-tall body, 1.62 eye height.
    eye=(x+.3,x+.7,-1000,y-1.8+1.62,z+.3,z+.7)
    target=(lx,lx+1,ly,ly+1,lz,lz+1)
    return round(math.sqrt(sum(max(eye[2*i]-target[2*i+1],target[2*i]-eye[2*i+1],0)**2 for i in range(3))),4)


def player_collisions(blocks,track):
    """Continuous swept AABB along axis-aligned segments, width .6, height 1.8.

    Flat approach/climb segments only; collision data is exact for the selected
    panel variants and conservative full cubes for other encountered blocks.
    Not a complete movement simulation (jumping, velocity, ladder speed, etc.).
    """
    hits=set()
    for u,v in zip(track,track[1:]):
        if sum(u[i]!=v[i] for i in range(3))!=1:raise ValueError('Sweep requires a single changing axis')
        body=(min(u[0],v[0])-.3,max(u[0],v[0])+.3,min(u[1],v[1]),max(u[1],v[1])+1.8,min(u[2],v[2])-.3,max(u[2],v[2])+.3)
        for x in range(math.floor(body[0]),math.ceil(body[1])):
            for y in range(math.floor(body[2]),math.ceil(body[3])):
                for z in range(math.floor(body[4]),math.ceil(body[5])):
                    p=x,y,z;s=blocks.get(p)
                    if not s:continue
                    local=thin_boxes(s[0],tuple(sorted(s[1].items()))) if s[0] in('iron_door','iron_trapdoor','ladder') else [(0,1,0,1,0,1)]
                    for box in local:
                        if all(body[2*i]<box[2*i+1]+p[i]-1e-8 and body[2*i+1]>box[2*i]+p[i]+1e-8 for i in range(3)):hits.add(p)
    return sorted(hits)


def graph_distance(routes,start,end):
    graph={}
    for r in routes:
        for a,b in zip(r['points'],r['points'][1:]):
            a=tuple(a);b=tuple(b);graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    if start not in graph or end not in graph:raise ValueError('Shortcut endpoints must be on registered ordinary routes')
    todo=deque([(start,0)]);seen={start}
    while todo:
        p,d=todo.popleft()
        if p==end:return d
        for q in graph[p]-seen:seen.add(q);todo.append((q,d+1))
    raise ValueError('Ordinary alternative is disconnected')


def isolation_audit(before,shortcuts,changed):
    """Conservative two-cell exclusion around sources, wires and powered solids.

    Not a simulator. A remote pre-existing active component is forbidden near
    these bounded circuits; fixed passive blocks do not relay power indefinitely.
    """
    influence=set()
    for c in shortcuts:
        influence.update(map(tuple,c['wire']))
        influence.update(add(tuple(p),(0,-1,0)) for p in c['wire'])
        influence.update(tuple(c[k]) for k in ('lever','leverMount','outputBlock'))
        if c.get('repeater'):influence.add(tuple(c['repeater']))
    nearby={add(p,(dx,dy,dz)) for p in influence for dx in range(-2,3) for dy in range(-2,3) for dz in range(-2,3)}
    reactive={'note_block','redstone_wire','repeater','comparator','redstone_torch','redstone_wall_torch','redstone_block',
              'lever','observer','piston','sticky_piston','dispenser','dropper','hopper','tnt','redstone_lamp','powered_rail','activator_rail'}
    found=[]
    for p in sorted(nearby-set(changed)):
        s=before.get(p)
        if s and (s[0] in reactive or s[0].endswith(('_door','_trapdoor','_fence_gate','_button','_pressure_plate'))):
            found.append(dict(pos=p,name=s[0]))
    music=[p for p,s in before.items() if s[2]=='control' or s[2].isdigit()]
    distance=min(max(abs(p[i]-q[i]) for i in range(3)) for p in influence for q in music)
    if found or distance<=2:raise ValueError(('Potential old-circuit coupling',found,distance))
    return dict(influenceCells=sorted(influence),oldResponsiveWithinTwo=found,minimumMusicChebyshev=distance,
                limitation='bounded exclusion, not all-world redstone or chunk/update simulation')


@lru_cache(maxsize=1)
def shortcut_castle():
    data,b=read_model(ROOT/'castle_v3/interior_v13/castle_v13.json')
    music={p for p,s in b.items() if s[2]=='control' or s[2].isdigit()}
    frozen={(x+dx,y+dy,z+dz) for x,y,z in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    frozen.update(p for p,s in b.items() if s[2]=='terrain')
    for r in data['routes']:frozen.update((x,y+k,z) for x,y,z in route_cells(r['points'],r['width']) for k in range(4))
    for f in data['fixtures']:frozen.update(map(tuple,f['parts']));frozen.update(map(tuple,f['supports']))
    for p,s in b.items():
        if s[0] in EMISSION:frozen.update((p,add(p,(0,-1,0)),add(p,(0,1,0))))
    for f in data['features']:
        r=f['region'];frozen.update((x,y,z) for x in range(r[0],r[1]+1) for y in range(r[2],r[3]+1) for z in range(r[4],r[5]+1))
    replaceable={(x,y,60) for x in(-32,-31,-30) for y in(1,2,3)}|{(-46,33,2)}|set(S2_WIRE)
    e=RoomEditor(b,frozen,replaceable);edits={};features=[]
    # S1: both visible frame and the arched overhead wire carrier have real supports.
    for x in(-32,-30):
        for y in(1,2,3):edits[x,y,60]=state('cut_sandstone')
    edits[-31,3,60]=state('chiseled_sandstone')
    for y,half in [(1,'lower'),(2,'upper')]:edits[-31,y,60]=state('iron_door',facing='north',half=half,hinge='left',open='false',powered='false')
    for y in range(1,5):edits[-35,y,53]=state('tuff_bricks' if y<3 else 'cut_sandstone')
    for y in(1,2):edits[-35,y,58]=state('tuff_bricks')
    for x,y,z in S1_WIRE:
        support=x,y-1,z
        if support not in b and support not in edits:edits[support]=state('cut_sandstone')
    edits.update(wire_states(S1_WIRE))
    edits[-34,4,53]=state('lever',face='wall',facing='east',powered='false')
    edits[-32,1,59]=state('repeater',facing='north',delay='1',locked='false',powered='false')
    edits[-30,1,65]=state('chiseled_tuff_bricks');edits[-30,2,65]=state('lantern',hanging='false',waterlogged='false')
    # The old polished-tuff lintel at Y4 remains; no outer arch is rebuilt.
    e.apply('S1 回廊便门',edits,(-35,-30,1,5,53,65))
    features.append(dict(name='S1 回廊便门与高位线槽',family='shortcut',region=[-35,-30,0,5,53,65],parts=list(edits),
        note='门框、持久拉杆、高于原路三格净空的导线桥与阶梯落线；默认关闭，内侧拉杆开启后维持。'))
    edits={(-46,y,2):state('ladder',facing='east',waterlogged='false') for y in range(17,23)}
    edits[-46,33,2]=state('iron_trapdoor',facing='east',half='bottom',open='false',powered='false',waterlogged='false')
    edits[-46,33,-4]=state('cut_sandstone');edits[-46,34,-4]=state('cut_sandstone');edits[-45,34,-4]=state('lever',face='wall',facing='east',powered='false')
    edits.update(wire_states(S2_WIRE))
    edits[-46,25,3]=state('cut_sandstone');edits[-46,26,3]=state('lantern',hanging='false',waterlogged='false')
    e.apply('S2 藏谱折返梯口',edits,(-47,-45,17,34,-4,3))
    features.append(dict(name='S2 固定梯与上廊控制梯口',family='shortcut',region=[-48,-43,16,35,-4,3],parts=list(edits),
        note='补齐原缺失6架梯子，顶端改同向铁活板门；仅内墙七格成为线槽，第二层背墙和原支撑保持。'))
    # Real floor-based access to each lever, and S2 lower/upper landings.
    access=[dict(name='S1回廊控制位',points=grid_route([(-34,0,56),(-34,0,54)]),width=1,kind='control_access'),
            dict(name='S2下厅梯脚入口',points=grid_route([(-40,16,0),(-40,16,2),(-45,16,2)]),width=1,kind='control_access'),
            dict(name='S2上廊梯口入口',points=grid_route([(-43,32,2),(-45,32,2)]),width=1,kind='control_access')]
    from castle_sample import validate_route
    for r in access:
        errors=validate_route(e.blocks,r['points'])
        if errors:raise ValueError((r['name'],errors))
    s1points=grid_route([(-31,0,74),(-31,0,56)])
    s2lower=grid_route([(-40,16,0),(-40,16,2),(-46,16,2)])
    s2points=s2lower+[(-46,y,2) for y in range(17,33)]+[(-45,32,2),(-44,32,2),(-43,32,2)]
    shortcuts=[dict(id='S1',name='回廊便门',kind='door',wire=S1_WIRE,lever=(-34,4,53),leverMount=(-35,4,53),repeater=(-32,1,59),
        outputBlock=(-32,1,60),gate=(-31,1,60),gateParts=[(-31,1,60),(-31,2,60)],points=s1points,
        discovery='从普通路线先进入回廊，站(-34,0,54)抬头拨内侧拉杆；前庭一侧不开外部开关。'),
        dict(id='S2',name='藏谱折返梯口',kind='ladder_hatch',ladderBottom=17,wire=S2_WIRE,lever=(-45,34,-4),leverMount=(-46,34,-4),
        outputBlock=(-47,33,2),gate=(-46,33,2),gateParts=[(-46,33,2)],points=s2points,
        discovery='首次沿原普通楼梯到上廊，站(-43,32,-4)拨墙侧拉杆；固定梯子不移动，开的是梯口。')]
    for c in shortcuts:
        c['track']=[(x+.5,y+1,z+.5) for x,y,z in c['points']]
        c['ordinaryGraphSteps']=graph_distance(data['routes'],tuple(c['points'][0]),tuple(c['points'][-1]))
        c['shortcutGraphSteps']=len(c['points'])-1
        c['outsideLeverDistanceLowerBound']=interaction_lower_bound(c)
        c['default']='closed';c['reset']='从同一内侧拉杆关闭；普通路线始终保留。'
        c['circuitOff']=evaluate_circuit(e.blocks,c,False);c['circuitOn']=evaluate_circuit(e.blocks,c,True)
        if not player_collisions(e.blocks,c['track']):raise ValueError(f'{c["id"]} does not block when closed')
        errors=player_collisions(variant(e.blocks,c,True),c['track'])
        if errors:raise ValueError((c['id'],'open route blocked',errors))
    a=e.blocks;changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
    fixtures=[dict(name='S1门外短廊灯',zone='S1',kind='柱灯',pos=(-30,2,65),parts=[(-30,1,65),(-30,2,65)],supports=[(-30,0,65)]),
              dict(name='S2梯井中段灯',zone='S2',kind='壁座灯',pos=(-46,26,3),parts=[(-46,25,3),(-46,26,3)],supports=[(-47,25,3)])]
    return dict(data=data,before=b,after=a,changed=changed,frozen=frozen,replaceable=replaceable,
                features=features,shortcuts=shortcuts,access=access,fixtures=fixtures)
