"""Independent saved-artifact checks, not a game engine or browser test."""
import hashlib
import json
import re
from collections import Counter
from PIL import Image,ImageStat
from castle_detail import ROOT,read_model
from castle_front import route_cells
from castle_sample import validate_route
from castle_finish import protected,EMISSION,spread_light
from castle_interior import support_errors
from verify_castle_palette import References

OUT=ROOT/'castle_v3/interior_v13'


def main():
    old,b=read_model(ROOT/'castle_v3/light_v12/castle_v12.json');full,a=read_model(OUT/'castle_v13.json')
    load=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
    report=load('validation.json');diff=load('v13_changes.json');meta=load('内饰与室内通路.json');light=load('照明代理.json')
    normalized=lambda v:json.loads(json.dumps(v,ensure_ascii=False))
    changed={p for p in set(b)|set(a) if b.get(p)!=a.get(p)}
    assert len(changed)==237==report['changedCoordinates']
    assert {tuple(c['pos']) for c in diff}==changed and len(diff)==len(changed)
    for c in diff:
        p=tuple(c['pos']);assert c['before']==normalized(b.get(p)) and c['after']==normalized(a.get(p))
    assert len(a)==520688==report['totalBlocks']
    for key in('connections','musicAirLightingExceptions','offset','size'):
        assert full[key]==old[key],key
    openings={(-61,1,40),(-61,1,52),(-61,1,65),(-62,1,21),(-60,1,19)}
    assert set(b)-set(a)==openings==set(map(tuple,meta['openings']))
    rails={tuple(e['pos']) for e in meta['railUpdates']}
    cot={(x,y,z+j) for z in(42,49,56,63) for x in range(-66,-62) for y in(1,2) for j in(0,1)}
    stove={(x,y,z) for x in range(-68,-65) for y in range(1,5) for z in range(17,23)}
    allowed=cot|stove|openings|rails
    for p,s in b.items():
        if p not in allowed:assert a.get(p)==s,p
    assert changed&set(b)<=allowed
    for x,y,z in openings:
        assert b[x,y,z][0]=='stone_brick_wall'
        for dx,dz in((0,0),(1,0),(-1,0),(0,1),(0,-1)):
            assert b.get((x+dx,y-1,z+dz))==a.get((x+dx,y-1,z+dz)) and (x+dx,y-1,z+dz) in a
    for p in rails:
        assert b[p][0]==a[p][0]=='stone_brick_wall'
        assert any(sum(abs(p[i]-q[i]) for i in range(3))==1 for q in openings)
        for key,v in b[p][1].items():
            if a[p][1][key]!=v:assert key in('east','west','north','south') and a[p][1][key]=='none'
    assert all(not protected(p) for p in changed)
    music={p for p,s in b.items() if s[2]=='control' or s[2].isdigit()}
    assert len(music)==32260
    for x,y,z in music:
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                for dz in(-1,0,1):
                    p=x+dx,y+dy,z+dz;assert a.get(p)==b.get(p)
    assert sum(s[0]=='note_block' for s in a.values())==2307
    assert full['routes'][:35]==old['routes'] and full['routes'][35:]==meta['routes']
    assert len(meta['routes'])==5
    for r in old['routes']:
        for x,y,z in route_cells(r['points'],r['width']):
            for k in range(4):assert b.get((x,y+k,z))==a.get((x,y+k,z))
    oldpoints={tuple(p) for r in old['routes'] for p in r['points']}
    for r in meta['routes']:
        assert r['width']==1 and tuple(r['points'][0]) in oldpoints
        assert validate_route(a,r['points'])==[]
    loop=next(r for r in meta['routes'] if r['kind']=='interior_loop');assert loop['points'][0]==loop['points'][-1]
    assert len(set(map(tuple,loop['points'])))==30
    assert full['features'][:-14]==old['features'] and full['features'][-14:]==meta['features']
    assert support_errors(a,meta['features'])==[]
    for f in meta['features']:
        assert all(tuple(p) in b and a[tuple(p)]==b[tuple(p)] for p in f['anchors'])
    for f in old['features']:
        r=f['region'];assert not any(r[0]<=x<=r[1] and r[2]<=y<=r[3] and r[4]<=z<=r[5] for x,y,z in changed)
    assert full['fixtures'][:-2]==old['fixtures']
    for f in full['fixtures'][-2:]:
        p=tuple(f['pos']);assert a[p][0]=='lantern';s=a[tuple(f['supports'][0])]
        assert s[0]=='barrel' or s[0]=='spruce_slab' and s[1]['type']=='top'
    assert sum(s[0] in EMISSION for s in a.values())==510
    assert a[-37,17,7][0]=='oak_slab' and all((-37,y,7) not in a for y in range(18,34))
    materials=load('材料增减.json');place=Counter(a[p][0] for p in changed if p in a);recover=Counter(b[p][0] for p in changed if p in b)
    assert dict(place)==materials['place'] and dict(recover)==materials['recover']
    assert materials['net']=={n:place[n]-recover[n] for n in sorted(set(place)|set(recover))}
    fields={k:spread_light(model,{p:EMISSION[s[0]] for p,s in model.items() if s[0] in EMISSION}) for k,model in [('before',b),('after',a)]}
    points={(x,y+1,z) for r in old['routes'] for x,y,z in route_cells(r['points'],r['width'])}
    def stats(field,ps):
        vs=[field.get(p,0) for p in ps]
        return dict(samples=len(vs),minimum=min(vs),mean=round(sum(vs)/len(vs),2),zero=sum(v==0 for v in vs),below5=sum(v<5 for v in vs))
    for k in('before','after'):assert light[k]==stats(fields[k],points)
    assert all(fields['after'].get(p,0)>=fields['before'].get(p,0) for p in points)
    assert light['dimmerSamples']==[]
    for r,row in zip(meta['routes'],light['newRoutes']):
        ps={(x,y+1,z) for x,y,z in r['points']};assert row['after']==stats(fields['after'],ps)
        assert row['samples']==normalized([dict(pos=p,value=fields['after'].get(p,0)) for p in sorted(ps)])
        assert row['after']['zero']==0
    for rel,expected in report['sourceHashes'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected
    html=(OUT/'余响堡_V13生活与藏谱内饰.html').read_text(encoding='utf-8')
    payload=json.loads(re.search(r'const P=(.*?),\$=id=>',html,re.S).group(1))
    shown={tuple(v-payload['offset'][i] for i,v in enumerate(row[:3])):payload['palette'][row[3]] for row in payload['blocks']}
    assert all(s==normalized(a[p]) for p,s in shown.items()) and payload['changes']==diff
    assert payload['features'][:14]==meta['features'] and len(payload['features'])==19
    assert payload['report']==report and payload['lighting']==light
    wanted=set()
    for f in meta['features']:
        r=f['region'];wanted.update((x,y,z) for x in range(r[0]-2,r[1]+3) for y in range(r[2]-2,r[3]+3) for z in range(r[4]-2,r[5]+3))
    for px,py,pz in openings:wanted.update((x,y,z) for x in range(px-2,px+3) for y in range(py-1,py+4) for z in range(pz-2,pz+3))
    assert set(shown)==wanted&set(a)
    refs=References();refs.feed(html)
    for ref in refs.refs:
        if not ref.startswith(('http:','https:','#')):assert(OUT/ref).is_file(),ref
    assert len(refs.ids)==len(set(refs.ids))
    for k in('shelter','kitchen','archive','upper'):assert k in refs.ids and k+'Image' in refs.ids
    images=[]
    for p in sorted(OUT.glob('*.png')):
        im=Image.open(p).convert('RGB');assert min(im.size)>1000 and sum(ImageStat.Stat(im).var)>100
        assert p.stat().st_mtime>=(OUT/'castle_v13.json').stat().st_mtime
        images.append(dict(file=p.name,size=im.size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    assert len(images)==6
    audit=dict(fullModelBlocks=len(a),changedCoordinates=len(changed),added=len(set(a)-set(b)),removed=len(openings),
        replaced=len(changed&set(a)&set(b)),musicBlocksPreserved=len(music),oldRoutesVerified=35,newRoutesVerified=5,
        interiorLoopUniquePoints=len(set(map(tuple,loop['points']))),interiorOpenings=len(openings),furnishingGroups=14,
        exactViewerNeighborhoodBlocks=len(shown),oldRouteProxySamples=len(points),oldRouteDimmerSamples=0,
        newRouteMinima=[r['after']['minimum'] for r in light['newRoutes']],sourceHashesVerified=len(report['sourceHashes']),
        localReferencesChecked=len(refs.refs),uniqueDOMIds=len(refs.ids),images=images,staticArtifactCheck=True,browserTest=False,inGameTest=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
