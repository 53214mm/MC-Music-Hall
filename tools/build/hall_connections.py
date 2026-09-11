"""Explicit repeater timers with routed dust/stair links; static connectivity checks only."""
import heapq
from itertools import count

DIRS={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}
OPP={'east':'west','west':'east','north':'south','south':'north'}


def generate_connections(modules, transform, is_north):
    occupied=dict(modules)
    additions={}
    protected={(x,y+1,z) for (x,y,z),s in modules.items() if s[0]=='note_block'}
    control_paths=[]
    ports=[]
    report=[]
    def put(p,n,props=None,replace=False):
        state=(n,props or {},'control')
        if p in protected: raise ValueError(f'Covering note at {p}')
        if p in occupied and occupied[p][:2]!=state[:2] and not replace:
            raise ValueError(f'Control collision at {p}: {occupied[p]} vs {state}')
        occupied[p]=state;additions[p]=state
    def support(p):
        q=(p[0],p[1]-1,p[2])
        if q not in occupied: put(q,'stone')
        elif occupied[q][0] not in ['stone','dirt','oak_planks','blue_wool']:
            raise ValueError(f'Bad wire support {q} {occupied[q]}')
    def dust(p):
        support(p);put(p,'redstone_wire',{'power':'0','north':'side','south':'side','east':'side','west':'side'})
    def repeater(p,direction,delay=1,replace=False):
        support(p);put(p,'repeater',{'facing':OPP[direction],'delay':str(delay),'powered':'false','locked':'false'},replace)
    def local(number,p): return transform(number,p)
    def direction(number,name): return OPP[name] if is_north(number) else name
    for i in range(1,12):
        h=6 if i==11 else 9
        target=local(i,(19,h,3))
        if i>1:
            repeater(local(i,(19,h,2)),direction(i,'north'),replace=True)
            # A second manual-test button on the side of the same wool input.
            put(local(i,(18,h,1)),'stone_button',{'face':'wall','facing':direction(i,'west'),'powered':'false'})
        if i==11:
            ports.append({'target':target});continue
        tap=local(i,(19,9,-1))
        repeater(tap,direction(i,'north'))
        route_start=local(i,(19,9,-2))
        cells=[]
        for lane,x in enumerate([2,4,6,8]):
            zs=range(1,21) if lane%2==0 else range(20,0,-1)
            out=direction(i,'south' if lane%2==0 else 'north')
            for z in zs:
                p=local(i,(x,8,z));repeater(p,out,4);cells.append(p)
            if lane<3:
                turn=21 if lane%2==0 else 0
                for xx in range(x,x+3): dust(local(i,(xx,8,turn)))
        entry=local(i,(2,8,0));end=local(i,(8,8,0))
        dust(entry);dust(end)
        ports.append({'start':route_start,'entry':entry,'end':end,'target':target,'timer':cells})

    def electrically_sensitive(n): return n in ['redstone_wire','redstone_wall_torch','redstone_torch','repeater','note_block','stone_button']

    def route(start,end,tag,endpoint_allow):
        # Dust can step one block up/down. Avoid all unrelated electrical components,
        # and reserve both a wire and its supporting solid block.
        forbidden=set(protected)
        forbidden.update((x,y,z) for x in range(14,22) for y in range(29,33) for z in range(1,7))
        electrical=set()
        for p,s in occupied.items():
            if electrically_sensitive(s[0]): electrical.add(p)
        exceptions=set(endpoint_allow)|{start,end}
        for p in electrical:
            if p in exceptions: continue
            x,y,z=p
            for dx,dz in DIRS:
                for dy in [-1,0,1]: forbidden.add((x+dx,y+dy,z+dz))
            forbidden.add((x,y+1,z));forbidden.add((x,y-1,z))
        def free(p):
            if p==end or p==start: return True
            x,y,z=p
            if not(-5<=x<=47 and 1<=y<=74 and -34<=z<=35):return False
            q=(x,y-1,z)
            return p not in occupied and p not in forbidden and q not in occupied and q not in forbidden and (x,y+1,z) not in occupied
        def heuristic(p):
            return abs(p[0]-end[0])+abs(p[2]-end[2])+abs(p[1]-end[1])*2.5
        first=(start,(0,0,0),0)
        serial=count();heap=[(heuristic(start),next(serial),first)];cost={first:0};parent={}
        while heap:
            _,_,state=heapq.heappop(heap)
            p,last,span=state
            if p==end:break
            ancestor=state;prior=set()
            while ancestor!=first:
                ancestor=parent[ancestor];prior.add(ancestor[0])
            supports={(v[0],v[1]-1,v[2]) for v in prior|{p}}
            headrooms={(v[0],v[1]+1,v[2]) for v in prior|{p}}
            for dx,dz in DIRS:
                for dy in [0,1,-1]:
                    q=(p[0]+dx,p[1]+dy,p[2]+dz)
                    if not free(q):continue
                    support_q=(q[0],q[1]-1,q[2])
                    if q in prior or q in supports or support_q in prior or support_q in headrooms:continue
                    if (q[0],q[1]+1,q[2]) in supports:continue
                    if any(abs(q[0]-v[0])+abs(q[2]-v[2])==1 and abs(q[1]-v[1])<=1 for v in prior):continue
                    # Dust stairs must have clear headroom on the lower side.
                    head=(p[0],p[1]+1,p[2]) if dy==1 else (q[0],q[1]+1,q[2])
                    if dy and head in occupied and head not in exceptions:continue
                    move=(dx,dy,dz)
                    next_span=0 if dy==0 and last==move else span+1
                    if next_span>9:continue
                    candidate=(q,move,next_span)
                    new=cost[state]+1+abs(dy)*2.5
                    if new<cost.get(candidate,float('inf')):
                        cost[candidate]=new;parent[candidate]=state;heapq.heappush(heap,(new+heuristic(q),next(serial),candidate))
        else: raise ValueError(f'No safe path {tag}: {start} to {end}')
        path=[end]
        while state!=first:
            state=parent[state];path.append(state[0])
        path.reverse()
        # Repeaters require a straight same-height triple. Limit each intervening
        # dust run to <=12 cells so branch strengths are conservatively maintained.
        candidates=[i for i in range(1,len(path)-1) if path[i-1][1]==path[i][1]==path[i+1][1]
                    and (path[i][0]-path[i-1][0],path[i][2]-path[i-1][2])==(path[i+1][0]-path[i][0],path[i+1][2]-path[i][2])]
        repeat=[];prev=-1
        while len(path)-1-prev>12:
            options=[i for i in candidates if prev+2<=i<=prev+12]
            if not options: raise ValueError(f'No repeater landing in {tag}, path={path}, previous={prev}')
            prev=max(options);repeat.append(prev)
        for i,p in enumerate(path):
            if p in occupied and p in exceptions:continue
            if i in repeat:
                dx=path[i+1][0]-p[0];dz=path[i+1][2]-p[2];repeater(p,DIRS[(dx,dz)])
            else:dust(p)
        control_paths.append({'name':tag,'positions':path,'repeaterIndices':repeat,'delay':len(repeat)})
        return len(repeat)

    for i in range(1,11):
        p=ports[i-1];nxt=ports[i]
        input_delay=route(p['start'],p['entry'],f'{i:02}_timer_input',
                          [local(i,(19,9,-1)),p['entry'],local(i,(2,8,1))])
        next_h=6 if i==10 else 9
        link_delay=route(p['end'],nxt['target'],f'{i:02}_to_{i+1:02}',
                         [p['end'],local(i,(8,8,1)),nxt['target'],local(i+1,(19,next_h,2))])
        target=322 if i==10 else 320
        timer_delay=target-1-input_delay-link_delay-1
        if not 80<=timer_delay<=320:raise ValueError(f'Unsupported timer budget {timer_delay}')
        settings=[1]*80
        remaining=timer_delay-80
        for j in range(80):
            inc=min(3,remaining);settings[j]+=inc;remaining-=inc
        for pos,delay in zip(p['timer'],settings):
            old=occupied[pos];put(pos,'repeater',{**old[1],'delay':str(delay)},replace=True)
        report.append({'from':i,'to':i+1,'targetTicks':target,'inputIsolator':1,'inputWireDelay':input_delay,
                       'timerDelay':timer_delay,'timerSettings':settings,'linkWireDelay':link_delay,'nextInputRelay':1,
                       'totalTicks':2+input_delay+timer_delay+link_delay})
    return additions,{'status':'static routing and delay budget; requires in-game verification','connections':report,'paths':control_paths}


def verify_rising_signal(modules, additions, transform):
    """Conservative rising-edge graph with dust attenuation and repeater delays.

    Does not model Minecraft update order, falling edges, or the original torch towers.
    The documented module-internal 7/5-tick offsets are checked separately.
    """
    blocks={**modules,**additions}
    wires={p:s for p,s in blocks.items() if s[2]=='control' and s[0] in ['redstone_wire','repeater']}
    wool={transform(i,(19,6 if i==11 else 9,1)):i for i in range(1,12)}
    tops={i:transform(i,(19,6 if i==11 else 9,0)) for i in range(1,12)}
    for i,p in tops.items():wires[p]=blocks[p]
    def input_direction(s):
        return next(v for v,name in DIRS.items() if name==s[1]['facing'])
    received={};best={};seq=count();heap=[]
    def push(t,p,strength):
        if strength<1:return
        key=(p,strength)
        if t>=best.get(key,float('inf')):return
        best[key]=t;heapq.heappush(heap,(t,next(seq),p,strength))
    push(0,next(p for p,i in wool.items() if i==1),15)
    while heap:
        t,_,p,strength=heapq.heappop(heap)
        if best.get((p,strength))!=t:continue
        if p in wool:
            i=wool[p];received[i]=min(t,received.get(i,float('inf')));push(t,tops[i],15);continue
        s=wires.get(p)
        if not s:continue
        x,y,z=p
        if s[0]=='repeater':
            ix,iz=input_direction(s);q=(x-ix,y,z-iz);time=t+int(s[1]['delay'])
            if q in wool:push(time,q,15)
            if q in wires:
                dest=wires[q]
                if dest[0]=='redstone_wire' or (q[0]+input_direction(dest)[0],q[1],q[2]+input_direction(dest)[1])==p:
                    push(time,q,15)
            # Strongly powered solid block may feed adjacent repeaters or dust above.
            elif q in blocks and blocks[q][0] not in ['redstone_wire','repeater','ladder','stone_button']:
                above=(q[0],q[1]+1,q[2])
                if above in wires and wires[above][0]=='redstone_wire':push(time,above,15)
                for dx,dz in DIRS:
                    neighbor=(q[0]+dx,q[1],q[2]+dz)
                    if neighbor in wires and wires[neighbor][0]=='repeater':
                        di=input_direction(wires[neighbor])
                        if (neighbor[0]+di[0],neighbor[1],neighbor[2]+di[1])==q:push(time,neighbor,15)
        else:
            for dx,dz in DIRS:
                for dy in [0,1,-1]:
                    q=(x+dx,y+dy,z+dz);dest=wires.get(q)
                    if not dest:continue
                    if dy==1 and (x,y+1,z) in blocks:continue
                    if dy==-1 and (q[0],q[1]+1,q[2]) in blocks:continue
                    if dest[0]=='redstone_wire':push(t,q,strength-1)
                    elif dy==0:
                        di=input_direction(dest)
                        if (q[0]+di[0],q[1],q[2]+di[1])==p:push(t,q,15)
    expected={i:320*(i-1)+(2 if i==11 else 0) for i in range(1,12)}
    if received!=expected:raise ValueError(f'Rising-edge graph mismatch: received={received}, expected={expected}')
    return {'model':'rising-edge dust/repeater graph, not Minecraft runtime','receivedInputTicks':received,
            'musicZeroTicks':{i:t+(5 if i==11 else 7) for i,t in received.items()},'expectedInputTicks':expected}
