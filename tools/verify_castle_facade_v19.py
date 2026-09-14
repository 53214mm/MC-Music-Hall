"""Audit saved V19 geometry and images independently of the facade builder."""
import hashlib
import json
import re
from collections import Counter,deque
from PIL import Image,ImageStat
from castle_detail import ROOT,read_model
from castle_facade_v19 import OUT,SOURCE,TITLE,REGION
from castle_front import route_cells
from castle_finish import protected,EMISSION
from castle_interior import support_errors,DIRECTIONS
from castle_sample import validate_route
from castle_shortcuts import variant,evaluate_circuit,player_collisions
from castle_service import service_variant,evaluate_latch,latch_collisions,validate_service_routes
from castle_watchrooms import sight_trace
from verify_castle_story_rooms import saved_lighting
from verify_castle_palette import References
from vanilla_mesh import VanillaAssets
from render_castle_facade_v19 import SCENES

norm=lambda x:json.loads(json.dumps(x,ensure_ascii=False))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    old,b=read_model(SOURCE);d,a=read_model(OUT/'castle_v19.json')
    load=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
    report=load('validation.json');meta=load('构件与接坡.json');diff=load('v19_changes.json');mat=load('增量材料.json')
    assert report==d['report'] and meta==d['facadeV19']
    assert sha(SOURCE)==report['sourceHash']=='4c4d4dbdd5be8a14de2312becf0e042977103c83e9ceb09941ea3ce9c46bb85f'
    assert sha(ROOT/'castle_v3/release_v18/castle_v17.json')==report['sourceHash']
    bundle=sha(ROOT/'castle_v3/余响堡_V18完整施工包.zip')
    assert bundle=='87641143c5662ace97a96bcf6629a2aaa88e3bdca761d07ec273e04e79e32bbf'
    for rel,h in old['report']['sourceHashes'].items():assert sha(ROOT/rel)==h,rel
    changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
    assert len(a)==report['totalBlocks']==526692 and len(changed)==report['changedCoordinates']==6340
    assert len(set(a)-set(b))==report['added']==5423 and len(set(b)-set(a))==report['removed']==176
    assert len(changed&set(a)&set(b))==report['replaced']==741
    assert {tuple(v['pos']) for v in diff}==changed and len(diff)==len(changed)
    for v in diff:
        p=tuple(v['pos']);assert norm(b.get(p))==v['before'] and norm(a.get(p))==v['after']
    for p in changed:
        assert not protected(p)
        assert any(all(r[2*i]<=p[i]<=r[2*i+1] for i in range(3)) for r in REGION.values())
        assert p not in a or a[p][2]=='shell'
    music={p for p,s in b.items() if s[2]=='control' or s[2].isdigit()};assert len(music)==32260
    for x,y,z in music:
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):p=x+dx,y+dy,z+dz;assert a.get(p)==b.get(p)
    assert sum(s[0]=='note_block' for s in a.values())==2307
    for p,s in b.items():
        if s[2]=='terrain':assert a.get(p)==s
        if s[0] in EMISSION:
            for q in(p,(p[0],p[1]-1,p[2]),(p[0],p[1]+1,p[2])):assert a.get(q)==b.get(q)
        if s[0] in('amethyst_block','light_blue_stained_glass','purple_stained_glass','sea_lantern'):
            assert a[p]==s
            for dd in DIRECTIONS:q=tuple(p[i]+dd[i] for i in range(3));assert a.get(q)==b.get(q)
    for k in('offset','size','routes','connections','interiorV13','shortcutsV14','serviceV15','storyV16','watchV17','musicAirLightingExceptions'):
        assert d[k]==old[k],k
    assert len(old['features'])==142 and len(meta['features'])==17
    assert d['features']==old['features']+meta['features'] and d['fixtures']==old['fixtures']+meta['fixtures']
    for f in old['features']:
        r=f['region'];assert not any(all(r[2*i]<=p[i]<=r[2*i+1] for i in range(3)) for p in changed),f['name']
    for f in old['fixtures']:
        for q in f['parts']+f['supports']:p=tuple(q);assert a.get(p)==b.get(p)
    for r in old['routes']:
        assert validate_route(a,r['points'])==[],r['name']
        for x,y,z in route_cells(r['points'],r['width']):
            for k in range(4):assert a.get((x,y+k,z))==b.get((x,y+k,z))
    for c in old['shortcutsV14']['shortcuts']:
        for on in(False,True):assert evaluate_circuit(a,c,on)==evaluate_circuit(b,c,on)
        assert not player_collisions(variant(a,c,True),c['track'])
    c=old['serviceV15']['shortcut'];opened=service_variant(a,c,True)
    for on in(False,True):assert evaluate_latch(a,c,on)==evaluate_latch(b,c,on)
    assert not latch_collisions(opened) and service_variant(opened,c,False)==a and not validate_service_routes(a)
    for v in old['watchV17']['sightlines']:assert sight_trace(a,v['eye'],v['target']) is None
    assert not support_errors(a,meta['features'])
    # Every new/replaced component must join unchanged old geometry by face adjacency.
    remaining=changed&set(a);components=0
    while remaining:
        q=deque([remaining.pop()]);anchored=False;components+=1
        while q:
            p=q.popleft()
            for dd in DIRECTIONS:
                n=tuple(p[i]+dd[i] for i in range(3))
                if n in remaining:remaining.remove(n);q.append(n)
                elif n in a and n not in changed:anchored=True
        assert anchored,'Disconnected new component'
    for p in meta['blindBacks']:assert tuple(p) in a
    for p in meta['roofJoins']:p=tuple(p);assert p in b and a[p]==b[p]
    for p,s in b.items():
        if 0<=p[0]<=51 and 5<=p[1]<=45 and p[2]==-40:assert a[p]==s
    lamps={tuple(f['pos']) for f in meta['fixtures']}
    assert lamps=={(21,30,-46),(30,30,-46)}
    for x,y,z in lamps:
        assert a[x,y,z][0]=='lantern' and a[x,y,z][1]['hanging']=='true'
        assert a[x,y+1,z][0]=='iron_chain' and a[x,y+2,z][0]=='cut_sandstone'
    assert sum(s[0] in EMISSION for s in a.values())==report['lightBlocks']==541
    state_only={p for p in changed&set(a)&set(b) if a[p][0]==b[p][0]}
    assert set(map(tuple,mat['stateOnlyPositions']))==state_only
    # This facade uses one-item masonry/chain/lantern states only, no door/pot aliases.
    assert mat['placeItems']==Counter(a[p][0] for p in changed&set(a)-state_only)
    assert mat['dismantleItems']==Counter(b[p][0] for p in changed&set(b)-state_only)
    assets=VanillaAssets();states={(a[p][0],tuple(sorted(a[p][1].items()))) for p in changed if p in a}
    for n,pr in states:assets.elements(n,pr)
    assert len(states)==report['checkedChangedStates']
    light=saved_lighting(old,b,a,[]);assert not light['dimmerSamples'] and light['after']['zero']==0
    (OUT/'照明代理.json').write_text(json.dumps(light,ensure_ascii=False,indent=2),encoding='utf-8')
    html=(OUT/TITLE).read_text(encoding='utf-8');p=json.loads(re.search(r'const P=(.*?),\$=id=>',html,re.S).group(1))
    for k,v in [('report',report),('materials',mat),('changes',diff),('features',meta['features'])]:assert p[k]==v
    shown={tuple(row[i]-p['offset'][i] for i in range(3)):p['palette'][row[3]] for row in p['blocks']}
    regions=[v['region'] for v in p['views']]+[f['region'] for f in p['features']]
    wanted={q:s for q,s in a.items() if any(all(r[2*i]-1<=q[i]<=r[2*i+1]+1 for i in range(3)) for r in regions)}
    assert set(shown)==set(wanted) and all(s==norm(a[q]) for q,s in shown.items())
    for f in p['features']:
        r=f['region']
        for q in a:
            if all(r[2*i]<=q[i]<=r[2*i+1] for i in range(3)):assert q in shown,(f['name'],q)
    refs=References();refs.feed(html);assert len(refs.ids)==len(set(refs.ids))
    for ref in refs.refs:
        if not ref.startswith(('http:','https:','#')) and ref!='artifact_audit.json':assert (OUT/ref).is_file(),ref
    images=[]
    for name,r,angle,title,w,h in SCENES:
        f=OUT/name;im=Image.open(f).convert('RGB');assert im.size==(w,h) and sum(ImageStat.Stat(im).var)>100
        assert f.stat().st_mtime>=(OUT/'castle_v19.json').stat().st_mtime
        images.append(dict(file=name,size=im.size,sha256=sha(f)))
    assert not list(OUT.rglob('*.nbt'))
    audit=dict(totalBlocks=len(a),changedCoordinates=len(changed),sourceHash=report['sourceHash'],unchangedV18ZipHash=bundle,
        sourceHashesVerified=2+len(old['report']['sourceHashes']),musicPreserved=32260,noteBlocks=2307,oldFeaturesPreserved=142,
        oldRoutesPreserved=53,gatedRoutesPreserved=3,sightlinesPreserved=2,newFeatures=17,faceAnchoredComponents=components,
        roofJoinCells=len(meta['roofJoins']),blindBackingCells=len(meta['blindBacks']),oldLightsPreserved=539,newLights=2,totalLights=541,
        oldRouteLighting=light,changedStatesParsed=len(states),placeItems=sum(mat['placeItems'].values()),
        dismantleItems=sum(mat['dismantleItems'].values()),viewerBlocks=len(shown),images=images,
        staticArtifactCheck=True,fullStairDynamics=False,browserTest=False,inGameTest=False,newNBT=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='images'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
