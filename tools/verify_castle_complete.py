"""Independent shipped-data/NBT readback, music and old-unit preservation audit."""
import json
import zipfile
from pathlib import Path
from collections import Counter,defaultdict,deque
from nbt_structure_to_json import read_nbt
from castle_sample import validate_route
from castle_front import route_cells

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'castle_v3'/'full_castle'
JAR=Path(r'E:\PCL\PCL 正式版 2.8.12\.minecraft\versions\26.3-snapshot-9\26.3-snapshot-9.jar')


def main():
    d=json.loads((OUT/'castle.json').read_text(encoding='utf-8'))
    expected={tuple(b[:3]):(d['palette'][b[3]][0],d['palette'][b[3]][1]) for b in d['blocks']}
    design={tuple(p[i]-d['offset'][i] for i in range(3)):(*v,'audit') for p,v in expected.items()}
    manifest=json.loads((OUT/'tile_manifest.json').read_text(encoding='utf-8'))
    origins={(x,y,z) for x in range(0,d['size'][0],32) for y in range(0,d['size'][1],32) for z in range(0,d['size'][2],32)}
    assert len(manifest)==len(origins) and {tuple(m['offset']) for m in manifest}==origins
    assert {p.name for p in (OUT/'structure_tiles').glob('*.nbt')}=={m['file'] for m in manifest}
    checked=0;non_air={};counts=Counter()
    for index,m in enumerate(manifest):
        nbt=read_nbt(OUT/'structure_tiles'/m['file'])
        size=[min(32,d['size'][i]-m['offset'][i]) for i in range(3)]
        assert nbt['size']==size==m['size'] and nbt['DataVersion']==5011
        assert len(nbt['blocks'])==size[0]*size[1]*size[2]
        seen=set();solid=0
        for b in nbt['blocks']:
            q=tuple(b['pos']);assert q not in seen;seen.add(q)
            assert all(0<=q[i]<size[i] for i in range(3))
            p=tuple(q[i]+m['offset'][i] for i in range(3));st=nbt['palette'][b['state']]
            n=st['Name'].removeprefix('minecraft:');props=st.get('Properties',{})
            assert (n,props)==expected.get(p,('air',{})),(m['file'],p,n)
            if n!='air':
                assert p not in non_air;non_air[p]=(n,props);counts[n]+=1;solid+=1
        assert solid==m['solidBlocks'];checked+=len(seen)
        if index%60==59:print(f'Read back {index+1}/{len(manifest)} tiles.',flush=True)
    assert non_air==expected and dict(counts)==d['report']['materials']
    assert checked==d['size'][0]*d['size'][1]*d['size'][2]
    # Compare with the shipped earlier stage, not a fresh call to the same builder.
    old=json.loads((ROOT/'castle_v3'/'gate_west_combined'/'combined.json').read_text(encoding='utf-8'))
    for b in old['blocks']:
        p=tuple(b[i]-old['offset'][i]+d['offset'][i] for i in range(3));s=old['palette'][b[3]]
        assert expected[p]==(s[0],s[1]),('Prior gate/west changed',p)
    # Compare original music states against the independently shipped V2 reference NBT.
    v2=read_nbt(ROOT/'music_hall'/'music_hall_reference.nbt')
    v2_states={tuple(b['pos']):(v2['palette'][b['state']]['Name'].removeprefix('minecraft:'),v2['palette'][b['state']].get('Properties',{})) for b in v2['blocks']}
    music={};control_positions=set()
    for b in d['blocks']:
        n,props,g=d['palette'][b[3]]
        if g.isdigit() or g=='control':
            p=tuple(b[i]-d['offset'][i] for i in range(3));oldp=(p[0]+29,p[1]+32+3,p[2]+40)
            assert v2_states[oldp]==(n,props),('Music state differs from V2',p)
            music[p]=(n,props)
            if g=='control':control_positions.add(p)
    assert len(music)==32260 and counts['note_block']==2307
    for (x,y,z),(n,props) in music.items():
        if n=='note_block':
            assert (x,y+1,z) not in design
            below=design.get((x,y-1,z));assert below and below[:2]==v2_states[(x+29,y-1+35,z+40)]
        if n=='redstone_wire' and (x,y,z) in control_positions:assert (x,y+1,z) not in design
    conn=json.loads((ROOT/'music_hall'/'connection_report.json').read_text(encoding='utf-8'))
    for a,b in zip(conn['connections'],d['connections']['connections']):
        for k in a:
            if k in ('tapPosition','nextRelayPosition'):assert b[k]==[a[k][0],a[k][1]-32,a[k][2]]
            elif k=='timerPositions':assert b[k]==[[p[0],p[1]-32,p[2]] for p in a[k]]
            else:assert a[k]==b[k],k
    assert len(conn['connections'])==len(d['connections']['connections'])==10
    for a,b in zip(conn['paths'],d['connections']['paths']):
        for k in a:
            assert b[k]==([[p[0],p[1]-32,p[2]] for p in a[k]] if k=='positions' else a[k]),k
    assert len(conn['paths'])==len(d['connections']['paths'])
    # All declared route points form one connected walk graph, including side branches.
    graph=defaultdict(set)
    for r in d['routes']:
        ps=list(map(tuple,r['points']));assert not validate_route(design,ps),r['name']
        for p in route_cells(ps,r['width']):assert not validate_route(design,[p]),(r['name'],p)
        for a,b in zip(ps,ps[1:]):graph[a].add(b);graph[b].add(a)
    start=(-18,-28,178);seen={start};queue=deque([start])
    while queue:
        for p in graph[queue.popleft()]-seen:seen.add(p);queue.append(p)
    assert seen==set(graph),('Disconnected route points',list(set(graph)-seen)[:10])
    assert (21,-3,4) in seen
    # Current target identifiers, no downloaded or guessed version constants.
    with zipfile.ZipFile(JAR) as jar:
        entries=set(jar.namelist());v=json.loads(jar.read('version.json'));assert v['world_version']==5011
        for n in counts:assert f'assets/minecraft/blockstates/{n}.json' in entries,n
    report=dict(nonAirBlocks=len(non_air),airInclusiveCells=checked,tiles=len(manifest),preservedGateWestBlocks=len(old['blocks']),
                preservedMusicBlocks=len(music),notes=2307,coveredNotes=0,connectedRoutePoints=len(seen),routes=len(d['routes']),targetVersion=v['id'],dataVersion=5011,
                status='NBT逐格回读、音乐与旧门楼/西翼状态、连接坐标和路线连通性通过。HTML仅文件级检查，未进行浏览器视觉或Minecraft实机验收。')
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
