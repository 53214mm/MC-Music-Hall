"""Read back V10 model, exact edits and static review artifacts; no game/browser."""
import hashlib
import json
from collections import Counter
from urllib.parse import unquote
from PIL import Image
from castle_detail import ROOT, read_model
from castle_finish import EMISSION, protected
from castle_front import route_cells
from verify_castle_palette import References

OUT = ROOT / 'castle_v3/detail_v10'
IMAGES = ['01_整堡南东形状对照.png', '02_整堡西南形状对照.png',
          '03_长墙拱龛近景.png', '04_塔窗薄框近景.png',
          '05_维修翼檐口近景.png', '06_西翼山墙收边近景.png']


def cells(region, margin=0):
    return ((x, y, z) for x in range(region[0]-margin, region[1]+margin+1)
            for y in range(region[2]-margin, region[3]+margin+1)
            for z in range(region[4]-margin, region[5]+margin+1))


def main():
    olddata, old = read_model(ROOT / 'castle_v3/ground_v9/castle_v9.json')
    data, now = read_model(OUT / 'castle_v10.json')
    report = json.loads((OUT / 'validation.json').read_text(encoding='utf-8'))
    diff = json.loads((OUT / 'v10_changes.json').read_text(encoding='utf-8'))
    manifest = json.loads((OUT / '构件定位与保留项.json').read_text(encoding='utf-8'))
    changed = {p for p in set(old) | set(now) if old.get(p) != now.get(p)}
    assert len(now) == report['totalBlocks'] == 520522
    assert len(changed) == len(diff) == report['changedCoordinates'] == 5782
    assert len(set(now)-set(old)) == report['added'] == 3687
    assert len(set(old)-set(now)) == report['removed'] == 1676
    assert len(changed & set(old) & set(now)) == report['replaced'] == 419
    assert {tuple(d['pos']) for d in diff} == changed
    for d in diff:
        p = tuple(d['pos'])
        assert (tuple(d['before']) if d['before'] else None) == old.get(p)
        assert (tuple(d['after']) if d['after'] else None) == now.get(p)
    for key in ('routes', 'connections', 'fixtures'):
        assert data[key] == olddata[key], key
    assert data['features'][:12] == olddata['features']
    assert data['features'][12:] == manifest['features']
    assert len(manifest['features']) == report['features'] == 46
    assert Counter(f['family'] for f in manifest['features']) == report['featureFamilies']
    assert data['deferredFeatures'] == manifest['deferred'] == report['deferredFeatures']
    assert len(manifest['deferred']) == 2
    for f in olddata['features'] + manifest['deferred']:
        for p in cells(f['region']):
            assert old.get(p) == now.get(p), (f['name'], p)
    for p in set(old) | set(now):
        if protected(p):
            assert old.get(p) == now.get(p), p
    assert {p:s for p,s in old.items() if s[2] != 'shell' or s[0] in EMISSION} == {
        p:s for p,s in now.items() if s[2] != 'shell' or s[0] in EMISSION}
    assert sum(s[0] == 'note_block' for s in now.values()) == 2307
    assert sum(s[0] in EMISSION for s in now.values()) == 471
    assert sum(s[2] == 'control' or s[2].isdigit() for s in now.values()) == 32260
    for r in data['routes']:
        for x,y,z in route_cells(r['points'], r['width']):
            for dy in range(4):
                p = (x,y+dy,z)
                assert old.get(p) == now.get(p), (r['name'], p)
    previous = json.loads((ROOT / 'castle_v3/ground_v9/v9_changes.json').read_text(encoding='utf-8'))
    for d in previous:
        assert tuple(d['after']) == now[tuple(d['pos'])]
    for path, sha in report['sourceHashes'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == sha, path
    html = (OUT / '余响堡_V10外墙形状精修.html').read_text(encoding='utf-8')
    assert '__DATA__' not in html
    parser = References(); parser.feed(html)
    assert len(parser.ids) == len(set(parser.ids))
    for ref in parser.refs:
        if not ref.startswith(('https://', 'http://', '#')):
            assert (OUT/unquote(ref)).exists(), ref
    for key in ('east', 'west', 'window', 'dormer', 'timber', 'verge'):
        assert key in parser.ids and key+'Image' in parser.ids
    payload = json.loads(html.split('const P=', 1)[1].split(',$=id=>', 1)[0])
    assert payload['features'] == manifest['features']
    assert payload['changes'] == diff and payload['report'] == report
    selected = {tuple(b[i]-payload['offset'][i] for i in range(3)): tuple(payload['palette'][b[3]])
                for b in payload['blocks']}
    wanted = {p for f in manifest['features'] for p in cells(f['region'], 2)}
    assert selected == {p:now[p] for p in wanted if p in now}
    images = []
    for i, name in enumerate(IMAGES):
        path = OUT/name
        with Image.open(path) as im:
            im.load()
            assert im.size == ((2400,1560) if i < 2 else (2200,1360))
            assert len(set(im.resize((100,100)).getdata())) > 100
            size = list(im.size)
        assert path.stat().st_mtime > (OUT/'castle_v10.json').stat().st_mtime
        images.append(dict(file=name, size=size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    audit = dict(fullModelBlocks=len(now), exactChangedCoordinates=len(changed),
                 featuresVerified=len(manifest['features']), deferredRegionsUnchanged=2,
                 terrainAndMusicUnchanged=True, V9GroundEditsPreserved=len(previous),
                 routesVerified=len(data['routes']), lightSourcesUnchanged=471,
                 sourceHashesVerified=len(report['sourceHashes']),
                 exactViewerNeighborhoodBlocks=len(selected), localReferencesChecked=len(parser.refs),
                 uniqueDOMIds=len(parser.ids), images=images,
                 staticArtifactCheck=True, browserTest=False, inGameTest=False)
    (OUT/'artifact_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(audit, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
