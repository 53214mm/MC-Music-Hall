"""Verify saved V9 model/diff, frozen source files and review artifacts."""
import hashlib
import json
from urllib.parse import unquote
from PIL import Image
from castle_detail import ROOT,read_model
from castle_finish import EMISSION
from verify_castle_palette import References

OUT=ROOT/'castle_v3/ground_v9'


def main():
    olddata,old=read_model(ROOT/'castle_v3/palette_v8/castle_v8.json');data,now=read_model(OUT/'castle_v9.json')
    report=json.loads((OUT/'validation.json').read_text(encoding='utf-8'));diff=json.loads((OUT/'v9_changes.json').read_text(encoding='utf-8'))
    assert old.keys()==now.keys() and len(now)==518511
    changed={p for p in old if old[p]!=now[p]}
    assert len(changed)==len(diff)==report['changedCoordinates']==14342
    assert {tuple(d['pos']) for d in diff}==changed
    tops={}
    for x,y,z in old:tops[x,z]=max(y,tops.get((x,z),-999))
    for p,s in old.items():
        assert s[1:]==now[p][1:]
        if p[1]<tops[p[0],p[2]]:assert s==now[p]
    for d in diff:
        p=tuple(d['pos']);assert tuple(d['before'])==old[p] and tuple(d['after'])==now[p]
        assert p[1]==tops[p[0],p[2]] and p[1]>-40
    assert len({(p[0],p[2]) for p in changed})==len(changed)
    for key in ('routes','connections','fixtures','features'):assert data[key]==olddata[key],key
    assert {p:s for p,s in old.items() if s[2] not in ('shell','terrain') or s[0] in EMISSION}=={p:s for p,s in now.items() if s[2] not in ('shell','terrain') or s[0] in EMISSION}
    previous=json.loads((ROOT/'castle_v3/palette_v8/v8_changes.json').read_text(encoding='utf-8'))
    for d in previous:assert tuple(d['after'])==now[tuple(d['pos'])]
    for path,sha in report['sourceHashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
    assert sum(report['zones'].values())==len(changed)
    images=[]
    for i,n in enumerate(['01_整堡南东地表对照.png','02_整堡西南地表对照.png','03_入口地表近景.png']):
        p=OUT/n
        with Image.open(p) as im:
            im.load();assert im.size==((2400,1560) if i<2 else (2200,1460))
            assert len(set(im.resize((100,100)).getdata()))>100
            size=list(im.size)
        assert p.stat().st_mtime>(OUT/'castle_v9.json').stat().st_mtime
        images.append(dict(file=n,size=size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    html=(OUT/'余响堡_V9地表配色对照.html').read_text(encoding='utf-8');assert '__DATA__' not in html
    parser=References();parser.feed(html);assert len(parser.ids)==len(set(parser.ids))
    for ref in parser.refs:
        if not ref.startswith(('https://','http://','#')):assert (OUT/unquote(ref)).exists(),ref
    for k in ('east','west'):assert k in parser.ids and k+'Image' in parser.ids
    audit=dict(fullModelBlocks=len(now),exactChangedCoordinates=len(changed),coordinateAndPropertiesUnchanged=True,oneTopCellPerColumn=True,subsurfaceUnchanged=True,
               allV8ColorChangesPreserved=len(previous),sourceHashesVerified=len(report['sourceHashes']),localReferencesChecked=len(parser.refs),uniqueDOMIds=len(parser.ids),
               images=images,staticArtifactCheck=True,browserTest=False,inGameTest=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
