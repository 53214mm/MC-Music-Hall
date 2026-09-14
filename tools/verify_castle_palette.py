"""Read back V8 outputs and verify the delivered artifact set; no browser/game."""
import hashlib
import json
from html.parser import HTMLParser
from urllib.parse import unquote
from PIL import Image
from castle_palette import ROOT
from castle_detail import read_model
from castle_finish import EMISSION

OUT=ROOT/'castle_v3/palette_v8'
IMAGES=['01_整堡南东配色对照.png','02_整堡西南配色对照.png','03_主堡窗墙配色近景.png','04_长墙塔身配色近景.png']


class References(HTMLParser):
    def __init__(self):
        super().__init__();self.refs=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and a.get('href'):self.refs.append(a['href'])
        if tag=='img' and a.get('src'):self.refs.append(a['src'])


def main():
    olddata,old=read_model(ROOT/'castle_v3/integration_v7/castle_v7.json')
    data,now=read_model(OUT/'castle_v8.json')
    report=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
    diff=json.loads((OUT/'v8_changes.json').read_text(encoding='utf-8'))
    changed={p for p in old if old[p]!=now[p]}
    assert old.keys()==now.keys()
    assert all(old[p][1:]==now[p][1:] for p in old)
    assert len(changed)==len(diff)==report['changedCoordinates']==83733
    assert {tuple(d['pos']) for d in diff}==changed
    for d in diff:
        p=tuple(d['pos']);assert tuple(d['before'])==old[p] and tuple(d['after'])==now[p]
    assert len(now)==518511
    for key in ('routes','connections','fixtures','features'):
        assert data[key]==olddata[key],key
    assert {p:s for p,s in old.items() if s[2]!='shell' or s[0] in EMISSION}=={p:s for p,s in now.items() if s[2]!='shell' or s[0] in EMISSION}
    for path,sha in report['sourceHashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
    assert sum(report['zoneSurfaceReplacements'].values())==len(changed)
    images=[]
    for i,n in enumerate(IMAGES):
        p=OUT/n
        with Image.open(p) as im:
            im.load();assert im.size==((2400,1560) if i<2 else (2000,1360))
            assert len(set(im.resize((100,100)).getdata()))>100
            size=list(im.size)
        assert p.stat().st_mtime>(OUT/'castle_v8.json').stat().st_mtime
        images.append(dict(file=n,size=size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    html=(OUT/'余响堡_V8整堡配色对照.html').read_text(encoding='utf-8');assert '__DATA__' not in html
    parser=References();parser.feed(html);assert len(parser.ids)==len(set(parser.ids))
    for ref in parser.refs:
        if not ref.startswith(('https://','http://','#')):assert (OUT/unquote(ref)).exists(),ref
    # Check dynamically built control targets without claiming browser interaction.
    for k in ('east','west','window','curtain'):assert k in parser.ids and k+'Image' in parser.ids
    audit=dict(fullModelBlocks=len(now),exactChangedCoordinates=len(changed),coordinateAndPropertiesUnchanged=True,sourceHashesVerified=len(report['sourceHashes']),
               localReferencesChecked=len(parser.refs),uniqueDOMIds=len(parser.ids),images=images,staticArtifactCheck=True,browserTest=False,inGameTest=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
