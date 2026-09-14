"""Independent saved-artifact checks for V15, including excavation bounds."""
import hashlib
import json
import re
from collections import Counter,deque
from PIL import Image,ImageStat
from castle_detail import ROOT,read_model
from castle_front import route_cells
from castle_finish import protected,EMISSION
from castle_service import PATH,WIRE,STONE,DIRS,service_variant,evaluate_latch,latch_collisions,validate_service_routes,service_isolation,stair_profile
from castle_shortcuts import add,solid,player_collisions,variant,evaluate_circuit,graph_distance
from build_castle_service import OUT,TITLE,lighting,material_counts
from verify_castle_palette import References


def main():
    old,b=read_model(ROOT/'castle_v3/shortcuts_v14/castle_v14.json');d,a=read_model(OUT/'castle_v15.json')
    load=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
    norm=lambda v:json.loads(json.dumps(v,ensure_ascii=False))
    report=load('validation.json');meta=load('机关与通路.json');diff=load('v15_changes.json');overlay=load('开启状态覆盖.json');materials=load('材料增减.json')
    assert d['report']==report and d['serviceV15']==meta
    changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
    assert len(a)==521025==report['totalBlocks'] and len(changed)==742==report['changedCoordinates']
    assert len(set(a)-set(b))==507==report['added'] and len(set(b)-set(a))==207==report['removed']
    assert len(changed&set(a)&set(b))==28==report['replaced']
    assert len(diff)==len(changed) and {tuple(v['pos']) for v in diff}==changed
    for v in diff:
        p=tuple(v['pos']);assert v['before']==norm(b.get(p)) and v['after']==norm(a.get(p))
    floors=route_cells(PATH,3);air={(x,y+k,z) for x,y,z in floors for k in(1,2,3)}
    # Existing shell may be excavated only along exact floor/air profile, plus
    # this fixed set of corner rails, lamp pockets and real circuit positions.
    extra={(x,y,z) for x in(53,57) for y,z in((2,6),(17,56))}|{(53,7,44),(53,8,44),(53,15,51),
           (55,5,32),(56,5,32),(57,3,26),(57,5,32),(58,5,32),*( (59,5,z) for z in range(29,33))}
    assert changed&set(b)<=(floors|air|extra)
    assert changed&set(b)==set(map(tuple,meta['replacedPositions']))
    assert set(b)-set(a)<=air
    assert all(52<=x<=59 and -4<=y<=23 and 5<=z<=58 for x,y,z in changed)
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
    for k in('offset','size','connections','interiorV13','shortcutsV14','musicAirLightingExceptions','routes'):
        assert d[k]==old[k],k
    assert len(d['routes'])==43
    for r in old['routes']:
        for x,y,z in route_cells(r['points'],r['width']):
            for k in range(4):assert a.get((x,y+k,z))==b.get((x,y+k,z))
    assert d['features'][:-3]==old['features'] and d['features'][-3:]==meta['features']
    assert d['fixtures'][:-6]==old['fixtures'] and d['fixtures'][-6:]==meta['fixtures']
    for f in old['features']:
        r=f['region'];assert not any(r[0]<=x<=r[1] and r[2]<=y<=r[3] and r[4]<=z<=r[5] for x,y,z in changed)
    for f in old['fixtures']:
        for p in f['parts']+f['supports']:p=tuple(p);assert a.get(p)==b.get(p)
    for c in old['shortcutsV14']['shortcuts']:
        for x,y,z in c['points']:
            for k in range(4):assert a.get((x,y+k,z))==b.get((x,y+k,z))
        assert evaluate_circuit(a,c,False)==evaluate_circuit(b,c,False)
        assert player_collisions(variant(a,c,True),c['track'])==[]
    c=meta['shortcut']
    assert set(map(tuple,meta['floorCells']))==floors and c['points']==norm(PATH)
    assert validate_service_routes(a)==[] and norm(stair_profile(a))==meta['stairProfile']
    assert meta['stairProfile']['halfRisers']==30 and len(meta['stairCells'])==45
    assert graph_distance(d['routes'],PATH[0],PATH[-1])==77==c['ordinaryGraphSteps']
    assert len(PATH)-1==53==c['shortcutGraphSteps']
    for x in(54,55,56):
        for y,z in((2,6),(17,56)):
            assert b[x,y,z][0].endswith('_wall') and (x,y,z) not in a and solid(a.get((x,y-1,z)))
    for x in(53,57):
        for y,z in((2,6),(17,56)):
            assert a[x,y,z][0].endswith('_wall') and a[x,y,z][1]['east' if x==53 else 'west']=='none'
    assert set(latch_collisions(a))=={STONE}
    opened=dict(a)
    for v in overlay:
        p=tuple(v['pos']);assert norm(a.get(p))==v['before']
        if v['after']:opened[p]=(v['after'][0],v['after'][1],v['after'][2])
        else:opened.pop(p)
    assert len(overlay)==13 and opened==service_variant(a,c,True)
    assert not latch_collisions(opened) and service_variant(opened,c,False)==a
    assert service_variant(opened,c,True)==opened and service_variant(a,c,False)==a
    assert norm(evaluate_latch(a,c,False))==c['off'] and norm(evaluate_latch(a,c,True))==c['on']
    # Reverse portal travel and a reachable ordinary control standing position.
    assert player_collisions(opened,[(55.5,2,28.5),(55.5,2,35.5)])==[]
    control=[(55.5,2,28.5),(55.5,2,26.5),(56.5,2,26.5)]
    assert player_collisions(a,control)==[]
    assert round(STONE[2]+1+.3-(c['lever'][2]+1),4)==c['reachLowerBound']==6.3
    assert sum(s[0] in EMISSION for s in a.values())==518==report['lightBlocks']
    for f in meta['fixtures']:
        p=tuple(f['pos']);assert a[p][0]=='lantern' and a[p][1]['hanging']=='false'
        assert solid(a.get(add(p,(0,-1,0)))) and all(tuple(q) in a for q in f['parts']+f['supports'])
    # Visible masonry/timber/half-block contact, not a structural physics claim.
    # Moving stone/head/piston cannot act as construction anchors.
    structural=lambda s:solid(s) or bool(s and s[0].endswith(('_stairs','_slab','_wall')))
    new={p for p in changed if p!=STONE and structural(a.get(p))}
    seen={p for p in new if any(q not in changed and structural(b.get(q)) for q in (add(p,v) for v in DIRS))}
    queue=deque(seen)
    while queue:
        p=queue.popleft()
        for v in DIRS:
            q=add(p,v)
            if q in new and q not in seen:seen.add(q);queue.append(q)
    assert seen==new,sorted(new-seen)
    iso=service_isolation(b,a);assert norm(iso)==meta['isolation'] and iso['minimumMusicChebyshev']==12
    assert norm(material_counts(b,a,changed))==materials
    assert materials['placeItems'].get('piston_head',0)==0 and materials['placeItems']['chiseled_sandstone']==1
    assert materials['placeItems']['redstone']==7 and len(materials['stateOnlyPositions'])==4
    light=lighting(b,a,old['routes'],floors);assert norm(light)==load('照明代理.json')
    assert not light['dimmerSamples'] and light['newRoute']['zero']==0 and light['newRoute']['minimum']==5
    for rel,h in report['sourceHashes'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h
    html=(OUT/TITLE).read_text(encoding='utf-8');p=json.loads(re.search(r'const P=(.*?),\$=id=>',html,re.S).group(1))
    assert p['meta']==meta and p['report']==report and p['changes']==diff and p['overlay']==overlay and p['materials']==materials and p['lighting']==norm(light)
    shown={tuple(row[i]-p['offset'][i] for i in range(3)):p['palette'][row[3]] for row in p['blocks']}
    wanted={p:s for p,s in a.items() if 51<=p[0]<=62 and -1<=p[1]<=24 and 3<=p[2]<=60}
    assert set(shown)==set(wanted) and all(s==norm(a[q]) for q,s in shown.items())
    refs=References();refs.feed(html);assert len(refs.ids)==len(set(refs.ids))
    for ref in refs.refs:
        if not ref.startswith(('http:','https:','#')) and ref!='artifact_audit.json':assert (OUT/ref).is_file(),ref
    images=[]
    for f in sorted(OUT.glob('*.png')):
        im=Image.open(f).convert('RGB');assert min(im.size)>1000 and sum(ImageStat.Stat(im).var)>100
        assert f.stat().st_mtime>=(OUT/'castle_v15.json').stat().st_mtime
        images.append(dict(file=f.name,size=im.size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    assert len(images)==4
    audit=dict(totalBlocks=len(a),changedCoordinates=len(changed),added=507,removed=207,replaced=28,musicPreserved=32260,noteBlocks=2307,
               oldRoutesPreserved=43,oldShortcutsPreserved=2,newGatedRoute=1,ordinaryGraphSteps=77,shortcutGraphSteps=53,
               stairBlocks=45,maxHalfCellRiser=.5,closedCollisionCells=[STONE],openedCollisionCells=[],openHoldIdempotent=True,closeRestoresExactModel=True,
               controlSweepClear=True,designatedClosedApproachReachLowerBound=6.3,faceConnectedNewStructuralParts=len(seen),minimumMusicChebyshev=12,
               foreignResponsiveParts=0,newArchitecturalLights=6,totalArchitecturalLights=518,oldRouteDimmerSamples=0,newRouteLight=light['newRoute'],
               exactViewerNeighborhoodBlocks=len(shown),sourceHashesVerified=len(report['sourceHashes']),images=images,referencesChecked=len(refs.refs),uniqueDOMIds=len(refs.ids),
               staticArtifactCheck=True,fullStairDynamics=False,browserTest=False,inGameTest=False,newNBT=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='images'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
