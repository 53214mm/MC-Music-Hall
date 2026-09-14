"""Stream-verify merged NBT tiles, original west-wing states and target IDs."""
import json
import zipfile
from pathlib import Path
from collections import Counter
from nbt_structure_to_json import read_nbt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'castle_v3'/'gate_west_combined'
JAR=Path(r'E:\PCL\PCL 正式版 2.8.12\.minecraft\versions\26.3-snapshot-9\26.3-snapshot-9.jar')


def main():
    d=json.loads((OUT/'combined.json').read_text(encoding='utf-8'))
    expected={tuple(b[:3]):(d['palette'][b[3]][0],d['palette'][b[3]][1]) for b in d['blocks']}
    manifest=json.loads((OUT/'tile_manifest.json').read_text(encoding='utf-8'))
    origins={(x,y,z) for x in range(0,d['size'][0],32) for y in range(0,d['size'][1],32) for z in range(0,d['size'][2],32)}
    assert {tuple(m['offset']) for m in manifest}==origins
    assert len(manifest)==len(origins)
    checked=0;non_air={};counts=Counter()
    for m in manifest:
        nbt=read_nbt(OUT/'structure_tiles'/m['file'])
        size=[min(32,d['size'][i]-m['offset'][i]) for i in range(3)]
        assert nbt['size']==size==m['size'] and nbt['DataVersion']==5011
        assert len(nbt['blocks'])==size[0]*size[1]*size[2]
        seen=set();solids=0
        for b in nbt['blocks']:
            q=tuple(b['pos']);assert q not in seen;seen.add(q)
            assert all(0<=q[i]<size[i] for i in range(3))
            p=tuple(q[i]+m['offset'][i] for i in range(3))
            s=nbt['palette'][b['state']];name=s['Name'].removeprefix('minecraft:');props=s.get('Properties',{})
            assert (name,props)==expected.get(p,('air',{})),(m['file'],p,name)
            if name!='air':
                assert p not in non_air;non_air[p]=(name,props);solids+=1;counts[name]+=1
        assert solids==m['solidBlocks'];checked+=len(seen)
    assert non_air==expected and dict(counts)==d['report']['materials']
    assert checked==d['size'][0]*d['size'][1]*d['size'][2]
    old=json.loads((ROOT/'castle_v3'/'west_wing_sample'/'sample.json').read_text(encoding='utf-8'))
    for b in old['blocks']:
        p=tuple(b[i]-old['offset'][i]+d['offset'][i] for i in range(3))
        state=old['palette'][b[3]]
        assert expected[p]==(state[0],state[1]),('Old west wing changed',p)
    with zipfile.ZipFile(JAR) as jar:
        valid=set(jar.namelist());v=json.loads(jar.read('version.json'))
        assert v['world_version']==5011
        for n in counts:assert f'assets/minecraft/blockstates/{n}.json' in valid,n
    report=dict(nonAirBlocks=len(non_air),airInclusiveCells=checked,tiles=len(manifest),preservedOldWestBlocks=len(old['blocks']),targetVersion=v['id'],dataVersion=5011,
                status='NBT坐标、状态与空气精确回读一致；原西翼全部实体保留。网页只做脚本/数据检查，自动浏览器预览被本地URL安全策略阻止；未进行游戏内实测。')
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
