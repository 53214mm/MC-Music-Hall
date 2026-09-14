"""Read saved V15/V16 artifacts and check the room delta without rebuilding it."""
import hashlib
import json
import re
from collections import Counter
from PIL import Image,ImageStat
from castle_detail import ROOT,read_model
from castle_front import route_cells
from castle_finish import protected,EMISSION,spread_light
from castle_interior import support_errors
from castle_sample import validate_route
from castle_shortcuts import add,solid,variant,evaluate_circuit,player_collisions
from castle_service import service_variant,evaluate_latch,latch_collisions,service_isolation,validate_service_routes
from build_castle_story_rooms import OUT,TITLE,VIEWS
from verify_castle_palette import References
from vanilla_mesh import VanillaAssets

OPENINGS={(4,17,64),(4,17,68),(6,17,78),(10,17,62),(10,17,78),(10,18,82),(69,17,43),(69,17,51)}
RAILS={(3,17,64),(3,17,68),(5,17,64),(5,17,68),(6,17,77),(6,17,79),
       (10,17,61),(10,17,63),(10,17,77),(10,17,79),(10,18,81),(10,18,83),
       (69,17,40),(69,17,42),(69,17,44),(69,17,50),(69,17,52)}
norm=lambda v:json.loads(json.dumps(v,ensure_ascii=False))


def saved_lighting(old,b,a,routes):
    fields=[spread_light(blocks,{p:EMISSION[s[0]] for p,s in blocks.items() if s[0] in EMISSION}) for blocks in(b,a)]
    def stats(field,ps):
        vals=[field.get(p,0) for p in ps]
        return dict(samples=len(vals),minimum=min(vals),mean=round(sum(vals)/len(vals),2),zero=sum(v==0 for v in vals))
    ps={(x,y+1,z) for r in old['routes'] for x,y,z in route_cells(r['points'],r['width'])}
    ps.update((x,y+1,z) for x,y,z in old['serviceV15']['floorCells'] if (x,y+1,z) not in b)
    for c in old['shortcutsV14']['shortcuts']:
        gates=set(map(tuple,c['gateParts']))
        ps.update((x,y+1,z) for x,y,z in c['points'] if (x,y+1,z) not in gates)
    rows=[]
    for r in routes:
        pts={(x,y+1,z) for x,y,z in r['points']}
        rows.append(dict(name=r['name'],kind=r['kind'],after=stats(fields[1],pts),samples=[dict(pos=p,value=fields[1].get(p,0)) for p in sorted(pts)]))
    return dict(before=stats(fields[0],ps),after=stats(fields[1],ps),newRoutes=rows,
                dimmerSamples=[dict(pos=p,before=fields[0].get(p,0),after=fields[1].get(p,0)) for p in sorted(ps) if fields[1].get(p,0)<fields[0].get(p,0)])


def main():
    old,b=read_model(ROOT/'castle_v3/service_v15/castle_v15.json');d,a=read_model(OUT/'castle_v16.json')
    load=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
    report=load('validation.json');meta=load('房间与通路.json');diff=load('v16_changes.json');mat=load('材料增减.json');light=load('照明代理.json')
    assert d['report']==report and d['storyV16']==meta
    changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
    assert len(a)==521219==report['totalBlocks'] and len(changed)==274==report['changedCoordinates']
    assert len(set(a)-set(b))==219==report['added'] and len(set(b)-set(a))==25==report['removed']
    assert len(changed&set(a)&set(b))==30==report['replaced']
    assert len(diff)==274 and {tuple(v['pos']) for v in diff}==changed
    for v in diff:
        p=tuple(v['pos']);assert v['before']==norm(b.get(p)) and v['after']==norm(a.get(p))
    chairs={p for p,s in b.items() if s[0]=='spruce_stairs' and -7<=p[0]<=21 and p[1]==17 and 58<=p[2]<=76}
    table={(x,y,z) for x in(71,72) for y in(17,18) for z in range(45,49)}
    assert len(chairs)==14 and all(b[p][0]=='spruce_planks' for p in table)
    assert changed&set(b)==chairs|table|OPENINGS|RAILS
    assert set(map(tuple,meta['oldChairs']))==chairs and set(map(tuple,meta['oldTable']))==table
    assert set(map(tuple,meta['openings']))==OPENINGS and {tuple(v['pos']) for v in meta['railUpdates']}==RAILS
    assert set(map(tuple,meta['replacedPositions']))==changed&set(b)
    for v in meta['railUpdates']:
        p=tuple(v['pos']);assert norm(a[p])==v['state'] and a[p][0]==b[p][0] and a[p][0].endswith('_wall')
    assert all(not protected(p) for p in changed)
    assert all((-7<=x<=21 and 17<=y<=26 and 58<=z<=86) or (69<=x<=74 and 14<=y<=23 and 40<=z<=52) for x,y,z in changed)
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
    for k in('offset','size','connections','interiorV13','shortcutsV14','serviceV15','musicAirLightingExceptions'):assert d[k]==old[k],k
    assert d['routes'][:43]==old['routes'] and d['routes'][43:]==meta['routes'] and len(d['routes'])==48
    assert d['features'][:-12]==old['features'] and d['features'][-12:]==meta['features']
    assert d['fixtures'][:-10]==old['fixtures'] and d['fixtures'][-10:]==meta['fixtures']
    for r in old['routes']:
        for x,y,z in route_cells(r['points'],r['width']):
            for k in range(4):assert a.get((x,y+k,z))==b.get((x,y+k,z))
    for f in old['features']:
        r=f['region'];assert not any(r[0]<=x<=r[1] and r[2]<=y<=r[3] and r[4]<=z<=r[5] for x,y,z in changed)
    for f in old['fixtures']:
        for p in f['parts']+f['supports']:p=tuple(p);assert a.get(p)==b.get(p)
    for c in old['shortcutsV14']['shortcuts']:
        for on in(False,True):assert evaluate_circuit(a,c,on)==evaluate_circuit(b,c,on)
        assert player_collisions(variant(a,c,True),c['track'])==[]
    c=old['serviceV15']['shortcut'];opened=service_variant(a,c,True)
    for on in(False,True):assert evaluate_latch(a,c,on)==evaluate_latch(b,c,on)
    assert not latch_collisions(opened) and service_variant(opened,c,False)==a and validate_service_routes(a)==[]
    assert norm(service_isolation(b,a))==old['serviceV15']['isolation']
    connected={tuple(p) for r in old['routes'] for p in r['points']}
    for r in meta['routes']:
        assert r['width']==1 and tuple(r['points'][0]) in connected and validate_route(a,r['points'])==[]
        assert player_collisions(a,[(x+.5,y+1,z+.5) for x,y,z in r['points']])==[]
        connected.update(map(tuple,r['points']))
    assert meta['routes'][-1]['points'][0]==meta['routes'][-1]['points'][-1]
    for x,y,z in OPENINGS:
        assert b[x,y,z][0].endswith('_wall') and (x,y,z) not in a
        assert all(solid(a.get((x+dx,y-1,z+dz))) for dx,dz in((0,0),(1,0),(-1,0),(0,1),(0,-1)))
    deck={(x,16,z) for x in range(70,74) for z in range(40,53)}
    assert len(deck-set(b))==49 and all(a[p][0]=='spruce_planks' for p in deck-set(b))
    assert all(a[p]==b[p] for p in deck&set(b))
    for z in(42,50):
        assert all(a[x,15,z][0]=='stripped_spruce_log' and a[x,15,z][1]['axis']=='x' for x in range(69,74))
        assert a[73,14,z][0]=='spruce_stairs' and a[73,14,z][1]['half']=='top'
        assert solid(b.get((74,15,z))) and solid(b.get((74,14,z)))
    assert all(a.get((x,10,z))==b.get((x,10,z)) for x in range(69,75) for z in range(40,53))
    assert not support_errors(a,meta['features'])
    for f in meta['features']:
        for p in f['oldAnchors']:p=tuple(p);assert a.get(p)==b[p]
    lamps={tuple(f['pos']) for f in meta['fixtures']}
    assert len(lamps)==10 and lamps=={p for p in changed if p in a and a[p][0]=='lantern'}
    for p in lamps:
        base=a.get(add(p,(0,-1,0)));assert solid(base) or base and (base[0]=='barrel' or base[0].endswith('_slab') and base[1].get('type')=='top')
    assert sum(s[0] in EMISSION for s in a.values())==528
    assert a[14,20,84][0]=='potted_oxeye_daisy' and solid(a.get((14,19,84)))
    assert a[73,18,46][0]=='grindstone' and a[73,17,46][1].get('type')=='top'
    assert a[13,18,80][0]=='lectern' and a[13,18,80][1]['has_book']=='false'
    assert not {a[p][0] for p in changed if p in a}&{'note_block','redstone_wire','repeater','sticky_piston','piston','redstone_torch','lever'}
    state_only={p for p in changed&set(a)&set(b) if a[p][0]==b[p][0]}
    assert len(state_only)==22 and set(map(tuple,mat['stateOnlyPositions']))==state_only
    assert mat['placeBlocks']==Counter(a[p][0] for p in changed&set(a)) and mat['removeBlocks']==Counter(b[p][0] for p in changed&set(b))
    expected_items=Counter(a[p][0] for p in (changed&set(a))-state_only)
    count=expected_items.pop('potted_oxeye_daisy');expected_items.update(flower_pot=count,oxeye_daisy=count)
    assert count==1 and mat['placeItems']==expected_items
    assert mat['dismantleBlocks']==Counter(b[p][0] for p in (changed&set(b))-state_only)
    checks=saved_lighting(old,b,a,meta['routes'])
    for k,v in checks.items():assert light[k]==norm(v),k
    assert not checks['dimmerSamples'] and [r['after']['minimum'] for r in checks['newRoutes']]==[6,10,8,9,9]
    assets=VanillaAssets();states={(s[0],tuple(sorted(s[1].items()))) for s in a.values() if s[2] in('shell','terrain')}
    for n,props in states:assets.elements(n,props)
    assert len(states)==185==report['modelStatesChecked']
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
        assert f.stat().st_mtime>=(OUT/'castle_v16.json').stat().st_mtime
        images.append(dict(file=f.name,size=im.size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    assert len(images)==6
    audit=dict(totalBlocks=len(a),changedCoordinates=len(changed),added=219,removed=25,replaced=30,musicPreserved=32260,noteBlocks=2307,
               oldOrdinaryRoutesPreserved=43,oldGatedRoutesPreserved=3,newRoutes=5,newRoutesSweepClear=True,newFeatures=12,
               floorBackedRailOpenings=8,existingRailStateChanges=17,stateOnlyCoordinates=22,newMezzaninePlanks=49,
               newArchitecturalLights=10,totalArchitecturalLights=528,oldRouteDimmerSamples=0,newRouteMinimumLight=[6,10,8,9,9],
               exactViewerNeighborhoodBlocks=len(shown),sourceHashesVerified=len(report['sourceHashes']),modelStatesChecked=len(states),
               images=images,referencesChecked=len(refs.refs),uniqueDOMIds=len(refs.ids),
               staticArtifactCheck=True,browserTest=False,inGameTest=False,newNBT=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='images'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
