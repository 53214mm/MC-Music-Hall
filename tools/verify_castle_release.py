"""Independent on-disk V18 readback, then hash and zip the verified offline package."""
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter,defaultdict,deque
from pathlib import Path
from PIL import Image
from castle_release import ROOT,SOURCE,OUT,TITLE
from castle_detail import read_model
from nbt_structure_to_json import read_nbt
from castle_front import route_cells
from castle_sample import validate_route
from castle_shortcuts import variant,evaluate_circuit,player_collisions
from castle_service import service_variant,evaluate_latch,latch_collisions,validate_service_routes
from vanilla_mesh import VanillaAssets,JAR
from verify_castle_palette import References

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    d,b=read_model(OUT/'castle_v17.json');r=json.loads((OUT/'release_report.json').read_text(encoding='utf-8'))
    mat=json.loads((OUT/'materials.json').read_text(encoding='utf-8'));tiles=json.loads((OUT/'tile_manifest.json').read_text(encoding='utf-8'))
    assert digest(SOURCE)==digest(OUT/'castle_v17.json')==r['sourceHashes'][str(SOURCE.relative_to(ROOT))]
    assert len(b)==r['totalBlocks']==521445
    assert r['changedModelCoordinates']==0 and r['browserTest'] is r['inGameTest'] is r['worldsModified'] is False
    assert d['size']==r['size']==[189,170,267] and r['designMin']==[-90,-48,-84] and r['designMax']==[98,121,182]
    for rel,h in r['sourceHashes'].items():assert digest(ROOT/rel)==h,rel
    for rel,h in d['report']['sourceHashes'].items():assert digest(ROOT/rel)==h,rel
    assert digest(Path(JAR))==r['targetJarHash']
    # Compute coverage independently of the export partition helper.
    origins=[(x,y,z) for y in range(-48,122,32) for x in range(-90,99,32) for z in range(-84,183,32)]
    assert len(tiles)==len(origins)==324 and [tuple(t['designMin']) for t in tiles]==origins
    assert len({t['file'] for t in tiles})==324
    assert {p.name for p in (OUT/'structure_tiles').glob('*')}=={t['file'] for t in tiles}
    nonair={};cells=0;all_air=0
    for index,(t,o) in enumerate(zip(tiles,origins),1):
        file=OUT/'structure_tiles'/t['file'];assert digest(file)==t['sha256']
        nbt=read_nbt(file);size=[min(32,r['designMax'][i]-o[i]+1) for i in range(3)]
        assert nbt['size']==t['size']==size and nbt['DataVersion']==5011 and not nbt['entities']
        assert t['order']==index and t['offset']==[o[i]-r['designMin'][i] for i in range(3)]
        assert t['file']==f'castle_{t["offset"][0]//32}_{t["offset"][1]//32}_{t["offset"][2]//32}.nbt'
        assert len(nbt['blocks'])==size[0]*size[1]*size[2]
        seen=set();count=0
        for entry in nbt['blocks']:
            q=tuple(entry['pos']);assert q not in seen and len(q)==3;seen.add(q)
            assert all(0<=q[i]<size[i] for i in range(3)) and 'nbt' not in entry
            p=tuple(q[i]+o[i] for i in range(3));s=nbt['palette'][entry['state']]
            n=s['Name'].removeprefix('minecraft:');pr=s.get('Properties',{})
            assert (n,pr)==b.get(p,('air',{},None))[:2],(t['file'],p,s)
            if n!='air':assert p not in nonair;nonair[p]=(n,pr);count+=1
        assert count==t['nonAir'];cells+=len(seen);all_air+=count==0
        if index%54==0:print(f'Readback {index}/324',flush=True)
    assert nonair=={p:s[:2] for p,s in b.items()}
    assert cells==r['airInclusiveCells']==8578710 and cells-len(nonair)==r['airCells']==8057265
    assert all_air==164
    # Count items independently, including coupled door halves and generated parts.
    counts=Counter(s[0] for s in b.values());items=Counter();groups=defaultdict(Counter)
    for p,(n,pr,g) in b.items():
        c=Counter()
        if n=='piston_head':
            assert p==(55,4,32) and b[55,5,32][0]=='sticky_piston'
        elif n=='iron_door':
            if pr['half']=='lower':
                assert b[p[0],p[1]+1,p[2]][0]=='iron_door'
                assert b[p[0],p[1]+1,p[2]][1]['half']=='upper';c[n]=1
            else:assert b[p[0],p[1]-1,p[2]][1]['half']=='lower'
        elif n=='potted_oxeye_daisy':c['flower_pot']=1;c['oxeye_daisy']=1
        elif n=='redstone_wire':c['redstone']=1
        elif n=='redstone_wall_torch':c['redstone_torch']=1
        else:c[n]=2 if n.endswith('_slab') and pr.get('type')=='double' else 1
        items.update(c);groups['music' if g.isdigit() or g=='control' else g].update(c)
        if n=='barrel':assert pr.get('open')=='false'
        if n=='furnace':assert pr.get('lit')=='false'
        if n=='lectern':assert pr.get('has_book')==pr.get('powered')=='false'
    assert counts==mat['blocks'] and items==mat['items'] and dict(groups)==mat['byGroup']
    assert sum(items.values())==mat['itemTotal']==r['materialItems']==521444 and len(items)==88==mat['itemKinds']
    assert mat['doubleSlabs']==0
    assets=VanillaAssets();states={(n,tuple(sorted(pr.items()))) for n,pr,g in b.values()}
    for n,pr in states:assets.elements(n,pr)
    with zipfile.ZipFile(JAR) as jar:
        entries=set(jar.namelist());version=json.loads(jar.read('version.json'))
        assert version['id']==r['target']=='26.3-snapshot-9' and version['world_version']==5011
        for n in items:assert f'assets/minecraft/items/{n}.json' in entries,n
    # Music match the older independent complete reference, not another V18 conversion.
    old=read_nbt(ROOT/'music_hall/music_hall_reference.nbt')
    oldmap={tuple(e['pos']):(old['palette'][e['state']]['Name'].removeprefix('minecraft:'),old['palette'][e['state']].get('Properties',{})) for e in old['blocks']}
    music={p:s for p,s in b.items() if s[2].isdigit() or s[2]=='control'}
    assert len(music)==r['musicBlocks']==32260 and counts['note_block']==2307
    for (x,y,z),(n,pr,g) in music.items():
        assert oldmap[x+29,y+35,z+40]==(n,pr),(x,y,z)
        if n=='note_block':
            assert (x,y+1,z) not in b
            assert b[x,y-1,z][:2]==oldmap[x+29,y+34,z+40]
    conn=json.loads((ROOT/'music_hall/connection_report.json').read_text(encoding='utf-8'))
    current=d['connections'];assert len(current['connections'])==len(conn['connections'])==10
    for oldc,newc in zip(conn['connections'],current['connections']):
        for key,v in oldc.items():
            if key in ('tapPosition','nextRelayPosition'):expected=[v[0],v[1]-32,v[2]]
            elif key=='timerPositions':expected=[[p[0],p[1]-32,p[2]] for p in v]
            else:expected=v
            assert newc[key]==expected,key
        assert len(newc['timerPositions'])==80
        assert [int(b[tuple(p)][1]['delay']) for p in newc['timerPositions']]==newc['timerSettings']
    assert [c['totalTicks'] for c in current['connections']]==[320]*9+[322]
    assert len(conn['paths'])==len(current['paths'])==20
    for a,c in zip(conn['paths'],current['paths']):
        for k,v in a.items():assert c[k]==([[p[0],p[1]-32,p[2]] for p in v] if k=='positions' else v)
    graph=defaultdict(set)
    for route in d['routes']:
        ps=list(map(tuple,route['points']));assert not validate_route(b,ps),route['name']
        for p in route_cells(ps,route['width']):assert not validate_route(b,[p]),(route['name'],p)
        for u,v in zip(ps,ps[1:]):graph[u].add(v);graph[v].add(u)
    start=(-18,-28,178);seen={start};queue=deque([start])
    while queue:
        for p in graph[queue.popleft()]-seen:seen.add(p);queue.append(p)
    assert set(graph)==seen and (21,-3,4) in seen and len(d['routes'])==53
    for c in d['shortcutsV14']['shortcuts']:
        for on in (False,True):evaluate_circuit(b,c,on)
        assert not player_collisions(variant(b,c,True),c['track'])
    c=d['serviceV15']['shortcut']
    for on in (False,True):evaluate_latch(b,c,on)
    opened=service_variant(b,c,True)
    assert not latch_collisions(opened) and service_variant(opened,c,False)==b and not validate_service_routes(b)
    html=(OUT/TITLE).read_text(encoding='utf-8');payload=json.loads(html.split('const D=',1)[1].split(',$=id=>',1)[0])
    for key in ('palette','blocks','offset','size','routes','connections'):assert payload[key]==d[key],key
    assert payload['report']==r and payload['materials']==mat and payload['tiles']==tiles
    assert payload['gates']==[*d['shortcutsV14']['shortcuts'],d['serviceV15']['shortcut']]
    assert payload['features']==[dict(name=f['name'],region=f['region'],note=f.get('note',''),build=f.get('build','')) for f in d['features']]
    assert [m['number'] for m in payload['modules']]==list(range(1,12))
    for m in payload['modules']:
        group=str(m['number']).zfill(2);module_cells={p:s for p,s in b.items() if s[2]==group}
        assert m['group']==group and m['blocks']==len(module_cells)
        assert m['designMin']==[min(p[k] for p in module_cells) for k in range(3)]
        assert m['designMax']==[max(p[k] for p in module_cells) for k in range(3)]
        assert m['input']==([23,-23,-3] if m['number']==1 else current['connections'][m['number']-2]['nextRelayPosition'])
        assert m['buttons']==[list(p) for p,s in module_cells.items() if s[0]=='stone_button']
    refs=References();refs.feed(html);assert len(refs.ids)==len(set(refs.ids))
    for ref in refs.refs:
        assert not ref.startswith(('http','../','file:'))
        assert (OUT/ref).exists() or ref in ('verification.json','SHA256SUMS.json'),ref
    images=[]
    for file in sorted(OUT.glob('*.png')):
        with Image.open(file) as im:im.load();assert len(set(im.resize((100,100)).getdata()))>100;images.append(dict(file=file.name,size=list(im.size),sha256=digest(file)))
    assert len(images)==4
    assert type(cells) is int and cells==8578710
    result=dict(totalBlocks=len(b),items=sum(items.values()),itemKinds=len(items),tiles=len(tiles),allAirTiles=all_air,
        airInclusiveCells=cells,noteBlocks=2307,musicStatesPreserved=len(music),modelChangedCoordinates=0,
        routes=53,connectedRoutePoints=len(seen),staticGateStates=6,targetModelStates=len(states),images=images,
        HTMLPayloadMatchesFullModel=True,browserInteractionTest=False,inGameTest=False,
        limitations=['NBT逐格回读不模拟放置/邻居更新或容器清空。','图片不是游戏截图；仅原版模型材质离线渲染。','路线是静态支持/净空及有限薄片碰撞，不是完整玩家动力学。','未完成全曲试听、真实照明、防跌落、开关后保存重进。'])
    save(OUT/'verification.json',result)
    # Include verification in checksum inventory; inventory itself is checked by ZIP bytes.
    files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.json')
    sums={str(p.relative_to(OUT)).replace('\\','/'):digest(p) for p in files};save(OUT/'SHA256SUMS.json',sums)
    subprocess.run(['node',str(ROOT/'tools/check_castle_html.cjs'),str(OUT/TITLE)],check=True)
    subprocess.run(['node',str(ROOT/'tools/test_castle_release_ui.cjs'),str(OUT/TITLE)],check=True)
    subprocess.run(['node',str(ROOT/'tools/test_castle_release_dom.cjs'),str(OUT/TITLE)],check=True)
    archive=OUT.parent/'余响堡_V18完整施工包.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,str(Path(OUT.name)/p.relative_to(OUT)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(sums)+1 and len(set(z.namelist()))==len(z.namelist())
        for name,h in sums.items():assert hashlib.sha256(z.read(OUT.name+'/'+name)).hexdigest()==h,name
        assert z.read(OUT.name+'/SHA256SUMS.json')==(OUT/'SHA256SUMS.json').read_bytes()
    print(json.dumps(result,ensure_ascii=False),flush=True)
    print(f'ZIP {archive.stat().st_size:,} bytes SHA256 {digest(archive)}',flush=True)


if __name__=='__main__':main()
