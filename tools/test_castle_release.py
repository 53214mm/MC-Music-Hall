"""Fail-closed release transformations, independent of the large full model."""
import unittest
from collections import Counter
from nbt_structure_to_json import NBTReader
from build_music_hall import encode_structure
from castle_release import item_cost, tile_manifest, tile_blocks, design_to_world


class ReleaseTests(unittest.TestCase):
    def test_material_aliases(self):
        self.assertEqual(item_cost('redstone_wire', {}), {'redstone': 1})
        self.assertEqual(item_cost('redstone_wall_torch', {}), {'redstone_torch': 1})
        self.assertEqual(item_cost('potted_oxeye_daisy', {}), {'flower_pot': 1, 'oxeye_daisy': 1})
        self.assertEqual(item_cost('piston_head', {}), {})

    def test_door_and_slab(self):
        self.assertEqual(item_cost('iron_door', {'half': 'lower'}), {'iron_door': 1})
        self.assertEqual(item_cost('iron_door', {'half': 'upper'}), {})
        self.assertEqual(item_cost('spruce_slab', {'type': 'double'}), {'spruce_slab': 2})
        self.assertEqual(item_cost('spruce_slab', {'type': 'top'}), {'spruce_slab': 1})
        with self.assertRaises(ValueError): item_cost('iron_door', {})
        with self.assertRaises(ValueError): item_cost('spruce_slab', {})
        with self.assertRaises(ValueError): item_cost('moving_piston', {})

    def test_partition_edge_and_air(self):
        low=(-3,-4,-5); size=(33,2,35)
        manifest=tile_manifest(low,size)
        self.assertEqual(len(manifest),4)
        expected={(x,y,z) for x in range(-3,30) for y in range(-4,-2) for z in range(-5,30)}
        cover=Counter()
        b={low:('stone',{},'shell'), (29,-3,29):('spruce_slab',{'type':'top'},'shell')}
        nonair={}
        for m in manifest:
            t=tile_blocks(b,m);n=NBTReader(encode_structure(t,5011)).root()
            self.assertEqual(n['size'],m['size'])
            self.assertEqual(len(n['blocks']),len(t))
            for q,s in t.items():
                p=tuple(q[i]+m['designMin'][i] for i in range(3));cover[p]+=1
                if s[0]!='air':nonair[p]=s
        self.assertEqual(set(cover),expected)
        self.assertTrue(all(c==1 for c in cover.values()))
        self.assertEqual(nonair,b)
        self.assertTrue(any(all(s[0]=='air' for s in tile_blocks(b,m).values()) for m in manifest))

    def test_y_first_order_and_origin(self):
        ms=tile_manifest((-90,-48,-84),(189,170,267))
        self.assertEqual(len(ms),324)
        self.assertEqual([m['designMin'][1] for m in ms],sorted(m['designMin'][1] for m in ms))
        self.assertEqual(ms[-1]['designMin'],[70,112,172])
        self.assertEqual(ms[-1]['size'],[29,10,11])
        self.assertEqual(design_to_world((-90,-48,-84),(100,80,200)),[10,32,116])

    def test_invalid_bounds(self):
        with self.assertRaises(ValueError):tile_manifest((0,0,0),(0,32,32))
        with self.assertRaises(ValueError):tile_manifest((0,0,0),(2.5,32,32))


if __name__=='__main__':unittest.main()
