"""Read back V12 artifacts and verify additive guard, music exceptions and light."""
import hashlib
import json
from collections import Counter
from urllib.parse import unquote
from PIL import Image
from castle_detail import ROOT,read_model
from castle_finish import EMISSION,protected
from castle_front import route_cells
from castle_pathlight import audit_models
from verify_castle_palette import References
from verify_castle_sculpt import cells

OUT=ROOT/'castle_v3/light_v12'
IMAGES=[('01_试听走廊梁下灯.png',(2600,1220)),('02_前庭落差端柱灯.png',(2200,1360)),
        ('03_南入口坡道双灯.png',(2200,1360)),('04_照明采样对照_非游戏实测.png',(2400,1360))]


def main():
    olddata,old=read_model(ROOT/'castle_v3/detail_v11/castle_v11.json');data,now=read_model(OUT/'castle_v12.json')
    read=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
    report=read('validation.json');diff=read('v12_changes.json');manifest=read('灯具定位.json');approval=read('音乐区精确例外.json');lighting=read('照明代理与剩余待验点.json')
    assert len(now)==report['totalBlocks']==520591
    assert set(old)<=set(now) and all(now[p]==s for p,s in old.items())
    added=set(now)-set(old);assert len(added)==len(diff)==report['added']==30
    assert report['removed']==report['replaced']==0
    assert {tuple(d['pos']) for d in diff}==added
    for d in diff:assert d['before'] is None and tuple(d['after'])==now[tuple(d['pos'])]
    assert Counter(now[p][0] for p in added)==report['materials']=={'lantern':7,'iron_chain':19,'chiseled_tuff_bricks':4}
    assert data['routes']==olddata['routes'] and data['connections']==olddata['connections']
    assert data['features'][:-7]==olddata['features'] and data['features'][-7:]==manifest['features']
    assert data['fixtures'][:-7]==olddata['fixtures'] and data['fixtures'][-7:]==manifest['fixtures']
    assert len(manifest['fixtures'])==7
    music={p for p,s in old.items() if s[2]=='control' or s[2].isdigit()}
    halo={(x+dx,y+dy,z+dz) for x,y,z in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    assert not added & halo and len(music)==32260
    assert sum(s[0]=='note_block' for s in now.values())==2307
    assert sum(s[0] in EMISSION for s in now.values())==508
    expected={}
    for x,y,z,roof in [(20,1,4,3),(30,5,5,15),(38,5,5,15)]:
        for yy in range(y,roof):
            expected[x,yy,z]=('lantern',{'hanging':'true','waterlogged':'false'},'shell') if yy==y else ('iron_chain',{'axis':'y','waterlogged':'false'},'shell')
    assert len(expected)==22
    assert {tuple(d['pos']):tuple(d['state']) for d in approval}==expected
    assert {p:now[p] for p in added if protected(p)}==expected
    assert data['musicAirLightingExceptions']==approval
    separations=[]
    for f in manifest['fixtures'][:3]:
        separation=min(max(abs(p[i]-q[i]) for i in range(3)) for p in map(tuple,f['parts']) for q in music)
        separations.append(dict(name=f['name'],minimumChebyshevDistance=separation))
    assert separations==report['musicSeparation']==manifest['musicSeparation']
    for r in data['routes']:
        for x,y,z in route_cells(r['points'],r['width']):
            for dy in range(4):assert old.get((x,y+dy,z))==now.get((x,y+dy,z))
    for f in manifest['fixtures']:
        x,y,z=f['pos'];anchor=tuple(f['supports'][0]);assert now[anchor]==old[anchor]
        assert set(map(tuple,f['parts']))<=added
        if f['kind']=='梁下悬灯':
            assert now[x,y,z][1]['hanging']=='true'
            for yy in range(y+1,anchor[1]):assert now[x,yy,z][0]=='iron_chain'
        else:assert now[x,y-1,z][0]=='chiseled_tuff_bricks' and now[x,y,z][1]['hanging']=='false'
    for path,sha in report['sourceHashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
    former=json.loads((ROOT/'castle_v3/detail_v11/照明代理与待验坐标.json').read_text(encoding='utf-8'))['zeroSampleLocations']
    calculated,_=audit_models(data,old,now,former)
    # Tuples become lists in saved JSON, normalize before comparing the complete report.
    assert json.loads(json.dumps(calculated))==lighting
    assert not lighting['dimmerSamples'] and lighting['after']['zero']==0
    assert len(lighting['remainingBelow5'])==24 and len(lighting['formerZeros'])==28
    html=(OUT/'余响堡_V12入口与试听走廊照明.html').read_text(encoding='utf-8');assert '__DATA__' not in html
    parser=References();parser.feed(html);assert len(parser.ids)==len(set(parser.ids))
    for ref in parser.refs:
        if not ref.startswith(('https://','http://','#')):assert (OUT/unquote(ref)).exists(),ref
    for k in ('window','dormer','timber'):assert k in parser.ids and k+'Image' in parser.ids
    payload=json.loads(html.split('const P=',1)[1].split(',$=id=>',1)[0])
    assert payload['report']==report and payload['lighting']==lighting and payload['changes']==diff and payload['features']==manifest['features']
    selected={tuple(b[i]-payload['offset'][i] for i in range(3)):tuple(payload['palette'][b[3]]) for b in payload['blocks']}
    wanted={p for f in manifest['features'] for p in cells(f['region'],2)}
    assert selected=={p:now[p] for p in wanted if p in now}
    images=[]
    for name,size in IMAGES:
        p=OUT/name
        with Image.open(p) as im:
            im.load();assert im.size==size and len(set(im.resize((100,100)).getdata()))>50
        assert p.stat().st_mtime>(OUT/'castle_v12.json').stat().st_mtime
        images.append(dict(file=name,size=size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    audit=dict(fullModelBlocks=len(now),addedBlocks=len(added),oldBlocksExactlyPreserved=len(old),musicHaloPreserved=True,exactMusicExceptionCells=22,
        musicSeparations=[d['minimumChebyshevDistance'] for d in separations],routesVerified=35,newSupportedFixtures=7,finalLightSources=508,
        routeProxySamples=6331,previousZeroSamples=28,remainingZeroSamples=0,remainingBelow5=24,dimmerSamples=0,
        sourceHashesVerified=len(report['sourceHashes']),exactViewerNeighborhoodBlocks=len(selected),
        localReferencesChecked=len(parser.refs),uniqueDOMIds=len(parser.ids),images=images,staticArtifactCheck=True,browserTest=False,inGameTest=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
