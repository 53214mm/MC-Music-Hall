"""Saved V17 artifact audit; no call to the room construction generator."""
import hashlib
import json
import re
from collections import Counter
from PIL import Image,ImageStat
from castle_detail import ROOT,read_model
from castle_front import route_cells
from castle_finish import protected,EMISSION
from castle_interior import support_errors
from castle_sample import validate_route
from castle_shortcuts import add,solid,variant,evaluate_circuit,player_collisions
from castle_service import service_variant,evaluate_latch,latch_collisions,service_isolation,validate_service_routes
from castle_watchrooms import sight_trace,REGIONS
from build_castle_watchrooms import OUT,TITLE,VIEWS
from verify_castle_story_rooms import saved_lighting
from verify_castle_palette import References
from vanilla_mesh import VanillaAssets

norm=lambda v:json.loads(json.dumps(v,ensure_ascii=False))


def main():
    old,b=read_model(ROOT/'castle_v3/story_v16/castle_v16.json');d,a=read_model(OUT/'castle_v17.json');load=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
    meta=load('房间通路与视线.json');report=load('validation.json');diff=load('v17_changes.json');mat=load('材料增减.json');light=load('照明代理.json')
    assert meta==d['watchV17'] and report==d['report']
    changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
    assert len(a)==521445==report['totalBlocks'] and len(changed)==293==report['changedCoordinates']
    assert len(set(a)-set(b))==227==report['added'] and len(set(b)-set(a))==1==report['removed']
    assert len(changed&set(a)&set(b))==65==report['replaced']
    assert len(diff)==len(changed) and {tuple(v['pos']) for v in diff}==changed
    for v in diff:p=tuple(v['pos']);assert v['before']==norm(b.get(p)) and v['after']==norm(a.get(p))
    water={(-42,y,z) for y in(-8,-7) for z in range(34,53)};patch={(x,-12,z) for x in range(-32,-28) for z in range(47,51)}
    table={(x,65,z) for x in range(-8,-3) for z in(-25,-24)}-{(-6,65,-25)}
    openings={(-22,49,-49)};rails={(-23,49,-49)};riser={(65,55,13)}
    assert changed&set(b)==water|patch|table|openings|rails|riser
    assert set(b)-set(a)==openings and set(map(tuple,meta['openings']))==openings
    assert set(map(tuple,meta['watermarks']))==water and all(a[p][0]=='mossy_stone_bricks' for p in water)
    assert {tuple(v['pos']) for v in meta['railUpdates']}==rails
    assert set(map(tuple,meta['replacedPositions']))==changed&set(b)
    assert all(any(r[0]<=p[0]<=r[1] and r[2]<=p[1]<=r[3] and r[4]<=p[2]<=r[5] for r in REGIONS.values()) for p in changed)
    assert all(not protected(p) for p in changed)
    music={p for p,s in b.items() if s[2]=='control' or s[2].isdigit()};assert len(music)==32260
    for x,y,z in music:
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):p=x+dx,y+dy,z+dz;assert a.get(p)==b.get(p)
    assert sum(s[0]=='note_block' for s in a.values())==2307
    for p,s in b.items():
        if s[2]=='terrain':assert a.get(p)==s
        if s[0] in EMISSION:
            for q in(p,add(p,(0,1,0)),add(p,(0,-1,0))):assert a.get(q)==b.get(q)
    for k in('offset','size','connections','interiorV13','shortcutsV14','serviceV15','storyV16','musicAirLightingExceptions'):assert d[k]==old[k],k
    assert d['routes'][:48]==old['routes'] and d['routes'][48:]==meta['routes'] and len(d['routes'])==53
    assert d['features'][:-18]==old['features'] and d['features'][-18:]==meta['features']
    assert d['fixtures'][:-11]==old['fixtures'] and d['fixtures'][-11:]==meta['fixtures']
    for r in old['routes']:
        for x,y,z in route_cells(r['points'],r['width']):
            for k in range(4):assert a.get((x,y+k,z))==b.get((x,y+k,z))
    for f in old['features']:
        r=f['region'];assert not any(r[0]<=x<=r[1] and r[2]<=y<=r[3] and r[4]<=z<=r[5] for x,y,z in changed)
    for f in old['fixtures']:
        for p in f['parts']+f['supports']:p=tuple(p);assert a.get(p)==b.get(p)
    for c in old['shortcutsV14']['shortcuts']:
        for on in(False,True):assert evaluate_circuit(a,c,on)==evaluate_circuit(b,c,on)
        assert not player_collisions(variant(a,c,True),c['track'])
    c=old['serviceV15']['shortcut'];opened=service_variant(a,c,True)
    for on in(False,True):assert evaluate_latch(a,c,on)==evaluate_latch(b,c,on)
    assert not latch_collisions(opened) and service_variant(opened,c,False)==a and validate_service_routes(a)==[]
    assert norm(service_isolation(b,a))==old['serviceV15']['isolation']
    connected={tuple(p) for r in old['routes'] for p in r['points']};flat_sweeps=0;risers=0
    for r in meta['routes']:
        assert r['width']==1 and tuple(r['points'][0]) in connected and validate_route(a,r['points'])==[]
        for u,v in zip(r['points'],r['points'][1:]):
            if u[1]!=v[1]:risers+=1;continue
            if a[tuple(u)][0].endswith('_stairs') or a[tuple(v)][0].endswith('_stairs'):continue
            assert not player_collisions(a,[(x+.5,y+1,z+.5) for x,y,z in(u,v)]);flat_sweeps+=1
        connected.update(map(tuple,r['points']))
    assert risers==9 and a[65,55,13][1]['facing']=='east'
    for x,y,z in openings:
        assert all(solid(a.get((x+dx,y-1,z+dz))) for dx,dz in((0,0),(1,0),(-1,0),(0,1),(0,-1)))
    assert not support_errors(a,meta['features'])
    for f in meta['features']:
        for p in f['oldAnchors']:p=tuple(p);assert a.get(p)==b[p]
    for z in(-44,-40):
        assert b[-57,76,z][0]=='spruce_planks'
        for y in range(77,83):assert a[-57,y,z][0]=='stripped_spruce_log'
    for z in range(-23,-12):assert a[-10,65,z]==b[-10,65,z] and a[-10,65,z][0]=='bookshelf'
    assert a[-6,66,-25]==b[-6,66,-25] and a[-6,65,-25]==b[-6,65,-25]
    lamps={tuple(f['pos']) for f in meta['fixtures']};assert len(lamps)==11 and lamps=={p for p in changed if p in a and a[p][0]=='lantern'}
    for p in lamps:
        s=a.get(add(p,(0,-1,0)));assert solid(s) or s and (s[0]=='barrel' or s[0].endswith('_slab') and s[1].get('type')=='top')
    assert sum(s[0] in EMISSION for s in a.values())==539
    assert not {a[p][0] for p in changed if p in a}&{'water','lava','fire','note_block','redstone_wire','repeater','piston','sticky_piston','lever'}
    for v in meta['sightlines']:
        assert tuple(v['eye'])==(-56.5,86.62,-39.5) and tuple(v['targetBlock']) in a
        assert sight_trace(a,v['eye'],v['target']) is None
        assert tuple(v['target'])==tuple(v['targetBlock'][i]+(.5 if i!=1 else 1.01) for i in range(3))
    assert len(meta['sightlines'])==2 and (-57,84,-40) in connected
    state_only={p for p in changed&set(a)&set(b) if a[p][0]==b[p][0]};assert len(state_only)==1 and set(map(tuple,mat['stateOnlyPositions']))==state_only
    assert mat['placeItems']==Counter(a[p][0] for p in changed&set(a)-state_only)
    assert mat['dismantleBlocks']==Counter(b[p][0] for p in changed&set(b)-state_only)
    assert mat['placeBlocks']==Counter(a[p][0] for p in changed&set(a)) and mat['removeBlocks']==Counter(b[p][0] for p in changed&set(b))
    checks=saved_lighting(old,b,a,meta['routes'])
    for k,v in checks.items():assert light[k]==norm(v),k
    assert not checks['dimmerSamples'] and [r['after']['minimum'] for r in checks['newRoutes']]==[6,4,6,8,6]
    assets=VanillaAssets();states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in('shell','terrain')}
    for n,p in states:assets.elements(n,p)
    assert len(states)==report['modelStatesChecked']
    for rel,h in report['sourceHashes'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h
    html=(OUT/TITLE).read_text(encoding='utf-8');p=json.loads(re.search(r'const P=(.*?),\$=id=>',html,re.S).group(1))
    for key,value in [('meta',meta),('report',report),('changes',diff),('materials',mat),('lighting',light)]:assert p[key]==value
    shown={tuple(row[i]-p['offset'][i] for i in range(3)):p['palette'][row[3]] for row in p['blocks']}
    wanted={q:s for q,s in a.items() if any(v['region'][0]<=q[0]<=v['region'][1] and v['region'][2]<=q[1]<=v['region'][3] and v['region'][4]<=q[2]<=v['region'][5] for v in VIEWS)}
    assert set(shown)==set(wanted) and all(s==norm(a[q]) for q,s in shown.items())
    refs=References();refs.feed(html);assert len(refs.ids)==len(set(refs.ids))
    for ref in refs.refs:
        if not ref.startswith(('http:','https:','#')) and ref!='artifact_audit.json':assert (OUT/ref).is_file(),ref
    images=[]
    for f in sorted(OUT.glob('*.png')):
        im=Image.open(f).convert('RGB');assert min(im.size)>1000 and sum(ImageStat.Stat(im).var)>100
        assert f.stat().st_mtime>=(OUT/'castle_v17.json').stat().st_mtime
        images.append(dict(file=f.name,size=im.size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    assert len(images)==7
    audit=dict(totalBlocks=len(a),changedCoordinates=len(changed),added=227,removed=1,replaced=65,musicPreserved=32260,noteBlocks=2307,
        oldOrdinaryRoutesPreserved=48,oldGatedRoutesPreserved=3,newRoutes=5,flatSegmentsSwept=flat_sweeps,newOneBlockStairTransitions=risers,newFeatures=18,
        newArchitecturalLights=11,totalArchitecturalLights=539,oldRouteDimmerSamples=0,newRouteMinimumLight=[6,4,6,8,6],
        sightlinesChecked=2,sightMethod='exact segment versus conservative block AABBs; walls/fences 1.5 high',
        exactViewerNeighborhoodBlocks=len(shown),sourceHashesVerified=len(report['sourceHashes']),modelStatesChecked=len(states),
        images=images,referencesChecked=len(refs.refs),uniqueDOMIds=len(refs.ids),staticArtifactCheck=True,fullStairDynamics=False,browserTest=False,inGameTest=False,newNBT=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='images'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
