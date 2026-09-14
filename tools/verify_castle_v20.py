"""Saved complete V20 audit and air-inclusive NBT readback; never builds a world."""
import hashlib,json,zipfile,subprocess
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image,ImageStat
from castle_v20 import SOURCE,OUT,TITLE,REGIONS
from castle_detail import ROOT,read_model
from castle_finish import EMISSION,protected
from castle_front import route_cells
from castle_interior import support_errors
from castle_sample import validate_route
from castle_shortcuts import variant,evaluate_circuit,player_collisions
from castle_service import service_variant,evaluate_latch,latch_collisions,validate_service_routes
from castle_watchrooms import sight_trace
from verify_castle_story_rooms import saved_lighting
from verify_castle_palette import References
from nbt_structure_to_json import read_nbt
from vanilla_mesh import VanillaAssets,JAR

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
norm=lambda v:json.loads(json.dumps(v,ensure_ascii=False))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    old,b=read_model(SOURCE);d,a=read_model(OUT/'castle_v20.json');load=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
    r=load('release_report.json');mat=load('materials.json');tiles=load('tile_manifest.json');plan=load('construction_plan.json');meta=load('sidewall.json');diff=load('v20_changes.json')
    assert sha(OUT/'castle_v20.json')==r['modelHash'] and sha(OUT/'construction_plan.json')==r['constructionPlanHash']
    assert hashlib.sha256((r['modelHash']+r['constructionPlanHash']).encode()).hexdigest()==r['progressKeyHash']
    for rel,h in r['sourceHashes'].items():assert sha(ROOT/rel)==h
    assert sha(ROOT/'castle_v3/余响堡_V18完整施工包.zip')=='87641143c5662ace97a96bcf6629a2aaa88e3bdca761d07ec273e04e79e32bbf'
    assert len(a)==r['totalBlocks']==528573 and d['size']==r['size']==[189,170,267]
    changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)};assert len(changed)==r['newChanges']==1881
    assert not (set(b)-set(a)) and all(a[p]==s for p,s in b.items())
    assert len(diff)==len(changed) and {tuple(v['pos']) for v in diff}==changed
    for v in diff:p=tuple(v['pos']);assert norm(a.get(p))==v['after'] and norm(b.get(p))==v['before']
    for p in changed:assert not protected(p) and any(all(z[2*i]<=p[i]<=z[2*i+1] for i in range(3)) for z in REGIONS.values())
    for f in old['features']:
        z=f['region'];assert not any(all(z[2*i]<=p[i]<=z[2*i+1] for i in range(3)) for p in changed),f['name']
    for k in ('routes','connections','interiorV13','shortcutsV14','serviceV15','storyV16','watchV17','facadeV19'):assert d[k]==old[k],k
    assert d['features']==old['features']+meta['features'] and d['fixtures']==old['fixtures']+meta['fixtures']
    assert len(d['features'])==170 and len(meta['features'])==11 and not support_errors(a,meta['features'])
    for route in d['routes']:
        assert not validate_route(a,route['points'])
        for x,y,z in route_cells(route['points'],route['width']):
            for dy in range(4):assert a.get((x,y+dy,z))==b.get((x,y+dy,z))
    music={p:s for p,s in b.items() if s[2].isdigit() or s[2]=='control'};assert len(music)==32260
    for x,y,z in music:
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):p=x+dx,y+dy,z+dz;assert a.get(p)==b.get(p)
    for c in d['shortcutsV14']['shortcuts']:
        for on in(False,True):assert evaluate_circuit(a,c,on)==evaluate_circuit(b,c,on)
        assert not player_collisions(variant(a,c,True),c['track'])
    c=d['serviceV15']['shortcut'];opened=service_variant(a,c,True)
    for on in(False,True):assert evaluate_latch(a,c,on)==evaluate_latch(b,c,on)
    assert not latch_collisions(opened) and service_variant(opened,c,False)==a and not validate_service_routes(a)
    for v in old['watchV17']['sightlines']:assert sight_trace(a,v['eye'],v['target']) is None
    assert sum(s[0] in EMISSION for s in a.values())==543
    for p,s in b.items():
        if s[0] in EMISSION:
            for q in(p,(p[0],p[1]+1,p[2]),(p[0],p[1]-1,p[2])):assert a.get(q)==b.get(q)
    light=saved_lighting(old,b,a,[]);assert not light['dimmerSamples'];save(OUT/'lighting_audit.json',light)
    # Independent items, no call to the release material transform.
    items=Counter();groups=defaultdict(Counter)
    for p,(n,pr,g) in a.items():
        cost=Counter()
        if n=='piston_head':assert p==(55,4,32)
        elif n=='iron_door':
            if pr['half']=='lower':cost[n]=1;assert a[p[0],p[1]+1,p[2]][1]['half']=='upper'
        elif n.startswith('potted_'):cost['flower_pot']=1;cost[n[7:]]=1
        elif n=='redstone_wire':cost['redstone']=1
        elif n=='redstone_wall_torch':cost['redstone_torch']=1
        else:cost[n]=2 if n.endswith('_slab') and pr.get('type')=='double' else 1
        items.update(cost);groups['music' if g.isdigit() or g=='control' else g].update(cost)
    assert items==mat['items'] and dict(groups)==mat['byGroup'] and sum(items.values())==528572==r['materialItems']
    assert len(items)==88 and Counter(s[0] for s in a.values())==mat['blocks']
    assets=VanillaAssets();states={(s[0],tuple(sorted(s[1].items()))) for s in a.values()}
    for n,pr in states:assets.elements(n,pr)
    with zipfile.ZipFile(JAR) as jar:
        version=json.loads(jar.read('version.json'));assert version['id']==r['target']=='26.3-snapshot-9' and version['world_version']==5011
        for n in items:assert f'assets/minecraft/items/{n}.json' in jar.namelist()
    assert sha(Path(JAR))==r['targetJarHash']
    # Partition saved data independently: exact one phase/pass/page per nonair block.
    assert len(plan['blockPhases'])==len(plan['blockPasses'])==len(d['blocks'])==len(a)
    expected=Counter();rank={};pageids=[]
    for row,ph,sub in zip(d['blocks'],plan['blockPhases'],plan['blockPasses']):
        assert ph in range(6) and sub in(0,1);p=tuple(row[i]-d['offset'][i] for i in range(3));key=(ph,sub,p[1],row[2]//16,row[0]//16);expected[key]+=1;rank[p]=key
    for pg,(key,count) in zip(plan['pages'],sorted(expected.items())):
        ph,sub,y,tz,tx=key;assert pg==dict(id=f'{ph}:{sub}:{y}:{tx}:{tz}',phase=ph,sub=sub,y=y,tx=tx,tz=tz,count=count);pageids.append(pg['id'])
    assert len(pageids)==len(expected)==len(set(pageids))==r['constructionPages'] and sum(expected.values())==len(a)
    # Critical survival attachment dependencies, including cross-partition side torches.
    directions={'east':(1,0,0),'west':(-1,0,0),'north':(0,0,-1),'south':(0,0,1)};dependencies=0
    for p,(n,pr,g) in a.items():
        if rank[p][0]==5:continue # Explicit special initial-state procedure, not Y order.
        q=None
        if n in ('lantern','soul_lantern'):q=(p[0],p[1]+(1 if pr['hanging']=='true' else -1),p[2])
        elif n in ('redstone_wire','repeater','redstone_torch','note_block') or n.startswith('potted_'):q=(p[0],p[1]-1,p[2])
        elif n in ('redstone_wall_torch','ladder'):
            dd=directions[pr['facing']];q=tuple(p[i]-dd[i] for i in range(3))
        elif n=='grindstone' and pr.get('face')=='ceiling':q=(p[0],p[1]+1,p[2])
        if q is not None:
            assert q in a,(p,n,'missing support',q)
            assert rank[q]<=rank[p],(p,n,'late support',q,rank[p],rank[q]);dependencies+=1
    # Full 324-file readback, includes actual air cells and block properties.
    origins=[(x,y,z) for y in range(-48,122,32) for x in range(-90,99,32) for z in range(-84,183,32)];assert len(tiles)==len(origins)==324
    assert {p.name for p in (OUT/'structure_tiles').glob('*.nbt')}=={t['file'] for t in tiles}
    nonair={};total=0;allair=0
    for index,(tile,o) in enumerate(zip(tiles,origins),1):
        assert tile['designMin']==list(o) and tile['order']==index
        f=OUT/'structure_tiles'/tile['file'];assert sha(f)==tile['sha256'];nbt=read_nbt(f)
        size=[min(32,r['designMax'][i]-o[i]+1) for i in range(3)];assert nbt['size']==tile['size']==size and nbt['DataVersion']==5011 and not nbt['entities']
        seen=set();count=0
        for entry in nbt['blocks']:
            q=tuple(entry['pos']);assert q not in seen and all(0<=q[i]<size[i] for i in range(3));seen.add(q)
            p=tuple(q[i]+o[i] for i in range(3));s=nbt['palette'][entry['state']];value=(s['Name'].removeprefix('minecraft:'),s.get('Properties',{}));assert value==a.get(p,('air',{},''))[:2],p
            if value[0]!='air':assert p not in nonair;nonair[p]=value;count+=1
        assert len(seen)==size[0]*size[1]*size[2] and count==tile['nonAir'];total+=len(seen);allair+=count==0
        if index%54==0:print(f'NBT saved readback {index}/324',flush=True)
    assert nonair=={p:s[:2] for p,s in a.items()} and total==r['airInclusiveCells']==8578710 and total-len(a)==r['airCells']==8050137
    html=(OUT/TITLE).read_text(encoding='utf-8');payload=json.loads(html.split('const D=',1)[1].split(';/* END_DATA */',1)[0])
    for k in('palette','blocks','offset'):assert payload[k]==d[k]
    for k,v in [('plan',plan),('materials',mat),('report',r),('tiles',tiles),('routes',d['routes']),('connections',d['connections'])]:assert payload[k]==v,k
    assert len(payload['features'])==170 and len(payload['modules'])==11 and len(payload['gates'])==3
    refs=References();refs.feed(html);assert len(refs.ids)==len(set(refs.ids))
    for ref in refs.refs:
        if ref.startswith('#'):assert ref[1:] in refs.ids
        elif ref not in('verification.json','SHA256SUMS.json'):assert not ref.startswith(('http','../','file:')) and (OUT/ref).is_file(),ref
    images=[]
    for f in sorted(OUT.glob('*.png')):
        im=Image.open(f).convert('RGB');assert min(im.size)>1000 and sum(ImageStat.Stat(im).var)>100
        assert f.stat().st_mtime>=(OUT/'castle_v20.json').stat().st_mtime
        images.append(dict(file=f.name,size=im.size,sha256=sha(f)))
    assert len(images)==4
    subprocess.run(['node',str(ROOT/'tools/test_castle_manual_logic.cjs')],check=True)
    subprocess.run(['node',str(ROOT/'tools/test_castle_v20_dom.cjs'),str(OUT/TITLE)],check=True)
    result=dict(totalBlocks=len(a),items=sum(items.values()),itemKinds=88,newCoordinates=1881,oldV19BlocksUnchanged=True,
        musicStatesPreserved=32260,noteBlocks=2307,oldRoutesPreserved=53,gateStatesPreserved=6,oldFeaturesPreserved=159,newFeatures=11,
        totalLights=543,oldRouteLighting=light,constructionPages=len(plan['pages']),pageCoverageExact=True,attachmentDependenciesChecked=dependencies,
        targetStatesParsed=len(states),target='26.3-snapshot-9',NBTFiles=324,allAirTiles=allair,airInclusiveCells=total,airCells=total-len(a),
        completeHTMLMatchesSavedModel=True,DOMStubTest=True,browserTest=False,inGameTest=False,images=images,
        limitations=['图片是原版模型离线渲染，不是游戏截图。','静态支撑和电路检查不是全玩家动力学、全曲试听或真实光照验收。','NBT含空气，不能直接覆盖朋友服务器。','施工进度只是用户自行勾选，无游戏状态检测或多人自动同步。'])
    save(OUT/'verification.json',result)
    sums={str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'};save(OUT/'SHA256SUMS.json',sums)
    archive=OUT.parent/'余响堡_V20完整施工包.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,str(Path(OUT.name)/p.relative_to(OUT)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==len(sums)+1
        for name,h in sums.items():assert hashlib.sha256(z.read(OUT.name+'/'+name)).hexdigest()==h
        assert z.read(OUT.name+'/SHA256SUMS.json')==(OUT/'SHA256SUMS.json').read_bytes()
    print(json.dumps({k:v for k,v in result.items() if k!='images'},ensure_ascii=False),flush=True)
    print(f'ZIP bytes={archive.stat().st_size} SHA256={sha(archive)}',flush=True)

if __name__=='__main__':main()
