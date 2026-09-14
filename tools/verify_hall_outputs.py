"""Read back the shipped NBT files and compare every placed block/state."""
import argparse
import json
import zipfile
from collections import Counter
from build_music_hall import OUTPUT
from nbt_structure_to_json import read_nbt


def canonical(root,offset=(0,0,0)):
    result={}
    for item in root['blocks']:
        p=tuple(item['pos'][i]+offset[i] for i in range(3))
        assert p not in result, f'duplicate position {p}'
        state=root['palette'][item['state']]
        result[p]=(state['Name'],tuple(sorted(state.get('Properties',{}).items())))
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--jar');args=parser.parse_args()
    report=json.loads((OUTPUT/'build_report.json').read_text(encoding='utf-8'))
    root=read_nbt(OUTPUT/'music_hall_reference.nbt');whole=canonical(root)
    assert root['size']==report['size']
    assert len(whole)==report['totalBlocks']
    counts=Counter(n.removeprefix('minecraft:') for n,_ in whole.values())
    assert dict(counts)==report['materials']
    assert counts['note_block']==2307
    for p,state in whole.items():
        assert all(0<=p[i]<root['size'][i] for i in range(3))
        if state[0]=='minecraft:note_block':assert (p[0],p[1]+1,p[2]) not in whole
    manifest=json.loads((OUTPUT/'tile_manifest.json').read_text(encoding='utf-8'))
    assembled={}
    for entry in manifest:
        tile=read_nbt(OUTPUT/'structure_tiles_church'/entry['file'])
        assert all(1<=v<=32 for v in tile['size'])
        for item in tile['blocks']:
            assert all(0<=item['pos'][i]<tile['size'][i] for i in range(3))
        placed=canonical(tile,entry['offset'])
        assert len(placed)==entry['blocks']
        assert not set(placed)&set(assembled)
        assembled.update(placed)
    assert assembled==whole,'Tile assembly differs from full reference'
    if args.jar:
        with zipfile.ZipFile(args.jar) as jar:
            valid=set(jar.namelist())
            missing=[n for n in counts if f'assets/minecraft/blockstates/{n}.json' not in valid]
            assert not missing, f'Unknown block IDs: {missing}'
            version=json.loads(jar.read('version.json'))
            assert version['world_version']==root['DataVersion']
        print(f'Target IDs verified: {len(counts)} types, {version["id"]}, DataVersion={root["DataVersion"]}')
    print(f'NBT readback PASS: {len(whole)} blocks; {len(manifest)} tiles; exact positions and properties; 2307 clear note tops')


if __name__=='__main__':main()
