"""Read saved V14 artifacts; never trust a generator's success flags alone."""
import hashlib
import json
import re
from collections import Counter,deque
from PIL import Image,ImageStat
from castle_detail import ROOT,read_model
from castle_front import route_cells
from castle_finish import protected,EMISSION
from castle_sample import validate_route
from castle_shortcuts import variant,player_collisions,evaluate_circuit,isolation_audit,solid,add,interaction_lower_bound,graph_distance
from build_castle_shortcuts import OUT,TITLE,lighting
from verify_castle_palette import References


def main():
    old,b=read_model(ROOT/'castle_v3/interior_v13/castle_v13.json');d,a=read_model(OUT/'castle_v14.json')
    load=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
    norm=lambda v:json.loads(json.dumps(v,ensure_ascii=False))
    meta=load('机关与通路.json');report=load('validation.json');diff=load('v14_changes.json');overlays=load('开启状态覆盖.json');materials=load('材料增减.json')
    assert d['shortcutsV14']==meta and d['report']==report
    changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
    assert len(changed)==54==report['changedCoordinates']
    assert len(a)==520725==report['totalBlocks'] and len(set(a)-set(b))==37==report['added']
    assert set(b)<=set(a) and report['removed']==0 and report['replaced']==17
    assert len(diff)==len(changed) and {tuple(c['pos']) for c in diff}==changed
    for c in diff:
        p=tuple(c['pos']);assert c['before']==norm(b.get(p)) and c['after']==norm(a.get(p))
    allowed={(x,y,60) for x in(-32,-31,-30) for y in(1,2,3)}|{(-46,33,2)}|{(-47,34,z) for z in range(-4,3)}
    assert allowed==set(map(tuple,meta['replaceable'])) and changed&set(b)==allowed
    for p,s in b.items():
        if p not in allowed:assert a.get(p)==s,p
    assert all(not protected(p) for p in changed)
    music={p for p,s in b.items() if s[2]=='control' or s[2].isdigit()};assert len(music)==32260
    for x,y,z in music:
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):
                    p=x+dx,y+dy,z+dz;assert a.get(p)==b.get(p)
    assert sum(s[0]=='note_block' for s in a.values())==2307
    for k in('offset','size','connections','interiorV13','musicAirLightingExceptions'):
        assert d[k]==old[k],k
    assert d['routes'][:40]==old['routes'] and d['routes'][40:]==meta['access'] and len(d['routes'])==43
    oldpoints={tuple(p) for r in old['routes'] for p in r['points']}
    for r in old['routes']:
        for x,y,z in route_cells(r['points'],r['width']):
            for k in range(4):assert a.get((x,y+k,z))==b.get((x,y+k,z))
    for r in meta['access']:
        assert tuple(r['points'][0]) in oldpoints and validate_route(a,r['points'])==[]
    assert d['features'][:-2]==old['features'] and d['features'][-2:]==meta['features']
    assert d['fixtures'][:-2]==old['fixtures'] and d['fixtures'][-2:]==meta['fixtures']
    for f in old['features']:
        r=f['region'];assert not any(r[0]<=x<=r[1] and r[2]<=y<=r[3] and r[4]<=z<=r[5] for x,y,z in changed)
    assert sum(s[0] in EMISSION for s in a.values())==512==report['lightBlocks']
    for f in meta['fixtures']:
        assert all(a[tuple(p)]==b[tuple(p)] for p in f['supports'])
        p=tuple(f['pos']);assert a[p][0]=='lantern' and a[p][1]['hanging']=='false' and solid(a.get(add(p,(0,-1,0))))
    # Every newly placed solid component has a face-connected path to an old solid.
    dirs=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))
    newsolid={p for p in changed if solid(a.get(p))}
    anchored={p for p in newsolid if any(q not in changed and solid(b.get(q)) for q in (add(p,v) for v in dirs))}
    queue=deque(anchored)
    while queue:
        for v in dirs:
            q=add(queue[0],v)
            if q in newsolid and q not in anchored:anchored.add(q);queue.append(q)
        queue.popleft()
    assert anchored==newsolid,sorted(newsolid-anchored)
    circuit_checks=[]
    for c in meta['shortcuts']:
        assert c['circuitOff']==evaluate_circuit(a,c,False) and c['circuitOn']==evaluate_circuit(a,c,True)
        gate=set(map(tuple,c['gateParts']))
        assert set(player_collisions(a,c['track']))==gate
        opened=dict(a)
        expected_parts={tuple(c['lever']),*map(tuple,c['wire']),*gate}
        if c.get('repeater'):expected_parts.add(tuple(c['repeater']))
        assert {tuple(v['pos']) for v in overlays[c['id']]}==expected_parts
        for v in overlays[c['id']]:
            p=tuple(v['pos']);assert v['before']==norm(a[p]);opened[p]=(v['after'][0],v['after'][1],v['after'][2])
        assert opened==variant(a,c,True)
        assert player_collisions(opened,c['track'])==[] and player_collisions(opened,list(reversed(c['track'])))==[]
        assert variant(opened,c,False)==a
        assert c['outsideLeverDistanceLowerBound']==interaction_lower_bound(c)>4.5
        assert c['ordinaryGraphSteps']==graph_distance(old['routes'],tuple(c['points'][0]),tuple(c['points'][-1]))>len(c['points'])-1==c['shortcutGraphSteps']
        circuit_checks.append(dict(id=c['id'],closedCollisionCells=sorted(gate),openSweptCollisionCells=[],reclosedIdentical=True,
                                   ordinaryGraphSteps=c['ordinaryGraphSteps'],shortcutGraphSteps=c['shortcutGraphSteps'],reachLowerBound=c['outsideLeverDistanceLowerBound']))
    both=variant(variant(a,meta['shortcuts'][0],True),meta['shortcuts'][1],True)
    for c in meta['shortcuts']:assert player_collisions(both,c['track'])==[]
    iso=isolation_audit(b,meta['shortcuts'],changed);assert norm(iso)==meta['isolation']
    place=Counter(a[p][0] for p in changed);recover=Counter(b[p][0] for p in changed if p in b)
    items=Counter(place);items['iron_door']=1
    assert materials['placeBlocks']==dict(place) and materials['removeBlocks']==dict(recover) and materials['placeItems']==dict(items)
    light=lighting(b,a,old['routes'],meta['access'],meta['shortcuts']);assert norm(light)==load('照明代理.json')
    assert light['dimmerSamples']==[] and all(r['after']['zero']==0 for r in light['gated'])
    for rel,h in report['sourceHashes'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h
    html=(OUT/TITLE).read_text(encoding='utf-8');p=json.loads(re.search(r'const P=(.*?),\$=id=>',html,re.S).group(1))
    assert p['meta']==meta and p['report']==report and p['changes']==diff and p['overlays']==overlays and p['materials']==materials and p['lighting']==norm(light)
    shown={tuple(row[i]-p['offset'][i] for i in range(3)):p['palette'][row[3]] for row in p['blocks']}
    wanted=set()
    for f in meta['features']:
        r=f['region'];wanted.update((x,y,z) for x in range(r[0]-2,r[1]+3) for y in range(r[2]-1,r[3]+2) for z in range(r[4]-2,r[5]+3))
    assert set(shown)==wanted&set(a) and all(s==norm(a[q]) for q,s in shown.items())
    refs=References();refs.feed(html);assert len(refs.ids)==len(set(refs.ids))
    for ref in refs.refs:
        if not ref.startswith(('http:','https:','#')) and ref!='artifact_audit.json':assert (OUT/ref).is_file(),ref
    images=[]
    for f in sorted(OUT.glob('*.png')):
        im=Image.open(f).convert('RGB');assert min(im.size)>1000 and sum(ImageStat.Stat(im).var)>100
        assert f.stat().st_mtime>=(OUT/'castle_v14.json').stat().st_mtime
        images.append(dict(file=f.name,size=im.size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    assert len(images)==4
    audit=dict(totalBlocks=len(a),changedCoordinates=len(changed),added=37,replaced=17,musicPreserved=32260,noteBlocks=2307,
               oldRoutesPreserved=40,accessRoutesVerified=3,gatedRoutesVerified=2,circuitChecks=circuit_checks,
               anchoredNewSolids=len(anchored),minimumMusicChebyshev=iso['minimumMusicChebyshev'],oldNearbyResponsiveParts=0,
               newLights=2,totalLights=512,oldRouteDimmerSamples=0,shortcutLightSamples=light['gated'],
               exactViewerNeighborhoodBlocks=len(shown),sourceHashesVerified=len(report['sourceHashes']),images=images,
               referencesChecked=len(refs.refs),uniqueDOMIds=len(refs.ids),staticArtifactCheck=True,browserTest=False,inGameTest=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('images','shortcutLightSamples')},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
