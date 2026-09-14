"""Independent saved-artifact verification for V11; no game or browser access."""
import hashlib
import json
from urllib.parse import unquote
from collections import Counter
from PIL import Image
from castle_detail import ROOT,read_model
from castle_finish import EMISSION,protected,spread_light
from castle_front import route_cells
from verify_castle_palette import References
from verify_castle_sculpt import cells

OUT=ROOT/'castle_v3/detail_v11'
IMAGES=['01_整堡南东窗廊对照.png','02_整堡西南窗廊对照.png','03_烽塔平台窗廊.png','04_维修塔低拱窗.png','05_长墙拱龛挂灯.png','06_拱龛照明剖面_非游戏实测.png']


def main():
    olddata,old=read_model(ROOT/'castle_v3/detail_v10/castle_v10.json');data,now=read_model(OUT/'castle_v11.json')
    read=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
    report=read('validation.json');diff=read('v11_changes.json');manifest=read('构件与新灯定位.json');lighting=read('照明代理与待验坐标.json')
    changed={p for p in set(old)|set(now) if old.get(p)!=now.get(p)}
    assert len(now)==report['totalBlocks']==520561
    assert len(changed)==len(diff)==report['changedCoordinates']==178
    assert len(set(now)-set(old))==report['added']==92
    assert len(set(old)-set(now))==report['removed']==53
    assert len(changed & set(old) & set(now))==report['replaced']==33
    assert {tuple(d['pos']) for d in diff}==changed
    for d in diff:
        p=tuple(d['pos'])
        assert (tuple(d['before']) if d['before'] else None)==old.get(p)
        assert (tuple(d['after']) if d['after'] else None)==now.get(p)
    assert data['routes']==olddata['routes'] and data['connections']==olddata['connections']
    assert data['features'][:-28]==olddata['features'] and data['features'][-28:]==manifest['features']
    assert data['fixtures'][:-30]==olddata['fixtures'] and data['fixtures'][-30:]==manifest['fixtures']
    assert len(manifest['fixtures'])==report['newFixtures']==30
    assert data['deferredFeatures']==[]
    assert data['resolvedV10Deferrals']==manifest['resolvedV10Deferrals']==olddata['deferredFeatures']
    assert Counter(f['family'] for f in manifest['features'])=={'platform_window':2,'niche_light':26}
    regions=manifest['bayRegions']
    inside=lambda p,r:all(r[i*2]<=p[i]<=r[i*2+1] for i in range(3))
    for p,s in old.items():
        if not any(inside(p,r) for r in regions):assert now.get(p)==s,p
    for f in olddata['features'][:12]:
        for p in cells(f['region']):assert old.get(p)==now.get(p),p
    for f in olddata['fixtures']:
        for pos in f['parts']+f['supports']:
            p=tuple(pos);assert old.get(p)==now.get(p),p
    assert {p:s for p,s in old.items() if s[2]!='shell'}=={p:s for p,s in now.items() if s[2]!='shell'}
    for p in set(old)|set(now):
        if protected(p):assert old.get(p)==now.get(p),p
    for p,s in old.items():
        if s[0] in EMISSION:assert now[p]==s
    for n,count in [('note_block',2307),('lantern',sum(s[0]=='lantern' for s in old.values())+30)]:
        assert sum(s[0]==n for s in now.values())==count
    assert sum(s[0] in EMISSION for s in now.values())==501
    assert sum(s[2]=='control' or s[2].isdigit() for s in now.values())==32260
    allpoints=set()
    for r in data['routes']:
        for x,y,z in route_cells(r['points'],r['width']):
            allpoints.add((x,y+1,z))
            for dy in range(4):
                p=(x,y+dy,z);assert old.get(p)==now.get(p),(r['name'],p)
    for path,sha in report['sourceHashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
    # Recompute proxy values from the saved models, not the transformation cache.
    fields={key:spread_light(b,{p:EMISSION[s[0]] for p,s in b.items() if s[0] in EMISSION}) for key,b in [('before',old),('after',now)]}
    for key in fields:
        values=[fields[key].get(p,0) for p in allpoints]
        assert lighting[key]==dict(samples=len(values),minimum=min(values),mean=round(sum(values)/len(values),2),zero=sum(v==0 for v in values),below5=sum(v<5 for v in values))
    assert not any(fields['after'].get(p,0)<fields['before'].get(p,0) for p in allpoints)
    assert {tuple(d['pos']) for d in lighting['zeroSampleLocations']}=={p for p in allpoints if fields['after'].get(p,0)==0}
    assert len(allpoints)==6331 and lighting['after']['zero']==28
    for f in manifest['fixtures']:
        x,y,z=f['pos'];assert now[x,y,z][0]=='lantern' and now[x,y+1,z][0]=='iron_chain'
        for pos in f['parts']+f['supports']:assert tuple(pos) in now
    html=(OUT/'余响堡_V11窗廊与暖灯.html').read_text(encoding='utf-8');assert '__DATA__' not in html
    parser=References();parser.feed(html);assert len(parser.ids)==len(set(parser.ids))
    for ref in parser.refs:
        if not ref.startswith(('https://','http://','#')):assert (OUT/unquote(ref)).exists(),ref
    for key in ('east','west','window','dormer','timber'):assert key in parser.ids and key+'Image' in parser.ids
    payload=json.loads(html.split('const P=',1)[1].split(',$=id=>',1)[0])
    assert payload['report']==report and payload['lighting']==lighting and payload['changes']==diff and payload['features']==manifest['features']
    selected={tuple(b[i]-payload['offset'][i] for i in range(3)):tuple(payload['palette'][b[3]]) for b in payload['blocks']}
    wanted={p for f in manifest['features'] for p in cells(f['region'],2)}
    assert selected=={p:now[p] for p in wanted if p in now}
    images=[]
    for i,name in enumerate(IMAGES):
        p=OUT/name
        with Image.open(p) as im:
            im.load();assert im.size==((2400,1560) if i<2 else (2200,1360))
            assert len(set(im.resize((100,100)).getdata()))>50
            size=list(im.size)
        assert p.stat().st_mtime>(OUT/'castle_v11.json').stat().st_mtime
        images.append(dict(file=name,size=size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    audit=dict(fullModelBlocks=len(now),exactChangedCoordinates=len(changed),resolvedV10Windows=2,newSupportedFixtures=30,
        oldLightsPreserved=471,finalLightSources=501,routesVerified=35,routeProxySamples=len(allpoints),routeProxyDimmer=0,
        zeroProxySamplesToCheck=28,musicProtectionZeroSamples=sum(d['inMusicProtection'] for d in lighting['zeroSampleLocations']),
        sourceHashesVerified=len(report['sourceHashes']),exactViewerNeighborhoodBlocks=len(selected),
        localReferencesChecked=len(parser.refs),uniqueDOMIds=len(parser.ids),images=images,
        staticArtifactCheck=True,browserTest=False,inGameTest=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
