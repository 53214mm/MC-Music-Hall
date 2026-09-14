"""Read exported NBT tiles back, including every air cell, and compare states."""
import json
import zipfile
from pathlib import Path
from castle_sample import build_sample,validate_route
from nbt_structure_to_json import read_nbt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'castle_v3'/'west_wing_sample'
JAR=Path(r'E:\PCL\PCL 正式版 2.8.12\.minecraft\versions\26.3-snapshot-9\26.3-snapshot-9.jar')


def main():
    payload=json.loads((OUT/'sample.json').read_text(encoding='utf-8'))
    expected={tuple(b[:3]):(payload['palette'][b[3]][0],payload['palette'][b[3]][1]) for b in payload['blocks']}
    manifest=json.loads((OUT/'tile_manifest.json').read_text(encoding='utf-8'))
    seen=set();placed={}
    for m in manifest:
        nbt=read_nbt(OUT/'structure_tiles'/m['file'])
        assert nbt['DataVersion']==5011
        assert nbt['size']==m['size'] and all(1<=n<=32 for n in nbt['size'])
        assert len(nbt['blocks'])==m['size'][0]*m['size'][1]*m['size'][2]
        for b in nbt['blocks']:
            p=tuple(b['pos'][i]+m['offset'][i] for i in range(3))
            assert p not in seen;seen.add(p)
            assert all(0<=p[i]<payload['size'][i] for i in range(3))
            s=nbt['palette'][b['state']];n=s['Name'].removeprefix('minecraft:');props=s.get('Properties',{})
            assert (n,props)==expected.get(p,('air',{})),(p,n)
            if n!='air':placed[p]=(n,props)
    assert placed==expected
    assert len(seen)==payload['size'][0]*payload['size'][1]*payload['size'][2]
    sample=build_sample()
    for r in sample['routes']:assert not validate_route(sample['blocks'],r['points'])
    with zipfile.ZipFile(JAR) as jar:
        valid=set(jar.namelist());v=json.loads(jar.read('version.json'))
        assert v['world_version']==5011
        for name in {n for n,_ in expected.values()}:
            assert f'assets/minecraft/blockstates/{name}.json' in valid,name
    report={'nonAirBlocks':len(placed),'checkedCellsIncludingAir':len(seen),'tiles':len(manifest),'targetVersion':v['id'],'dataVersion':5011,
            'routes':len(sample['routes']),'result':'分块坐标/属性/空气精确回读一致；目标版本方块ID存在；未进行游戏内行走或自动状态更新验证。'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
