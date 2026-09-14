import unittest
from vanilla_mesh import VanillaAssets


class MeshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.assets=VanillaAssets()

    def boxes(self,n,**props):return self.assets.elements(n,tuple(sorted(props.items())))

    def test_cube_and_trapdoor_thickness(self):
        cube=self.boxes('bricks');self.assertEqual(len(cube),1)
        trap=self.boxes('spruce_trapdoor',facing='north',half='bottom',open='true',powered='false',waterlogged='false')
        points=[v for e in trap for f in e['faces'] for v in f['vertices']]
        self.assertAlmostEqual(max(p[2] for p in points)-min(p[2] for p in points),3/16)
        self.assertEqual(max(p[1] for p in points)-min(p[1] for p in points),1)

    def test_stair_half_and_rotation(self):
        east=self.boxes('smooth_sandstone_stairs',facing='east',half='bottom',shape='straight')
        south=self.boxes('smooth_sandstone_stairs',facing='south',half='bottom',shape='straight')
        self.assertEqual(len(east),2)
        ep=[v for f in east[1]['faces'] for v in f['vertices']];sp=[v for f in south[1]['faces'] for v in f['vertices']]
        self.assertAlmostEqual(min(p[0] for p in ep),.5)
        self.assertAlmostEqual(min(p[2] for p in sp),.5)
        top=self.boxes('smooth_sandstone_stairs',facing='east',half='top',shape='straight')
        self.assertAlmostEqual(min(v[1] for f in top[0]['faces'] for v in f['vertices']),.5)

    def test_multipart_and_missing_state(self):
        p=dict(north='true',south='false',east='false',west='false',waterlogged='false')
        self.assertEqual(len(self.boxes('spruce_fence',**p)),3)
        with self.assertRaises(ValueError):self.boxes('spruce_trapdoor',facing='up')
        with self.assertRaises(KeyError):self.boxes('imaginary_building_block')

    def test_snapshot_sprite_object_resolves(self):
        elements=self.boxes('gray_stained_glass_pane',north='false',south='false',east='true',west='true',waterlogged='false')
        self.assertTrue(all(isinstance(f['texture'],str) for e in elements for f in e['faces']))

    def test_render_keeps_sample_pixels_when_caching_opaque_shapes(self):
        import hashlib
        from castle_craft_samples import samples
        from vanilla_mesh import render
        s=samples()[0]
        digest=hashlib.sha256(render(self.assets,s.blocks,s.region,920,1150,24).tobytes()).hexdigest()
        self.assertEqual(digest,'14a4c019be4baf1b02ed0858f84cd567de45c8855f1580078d5fd7a4893384dc')


if __name__=='__main__':unittest.main()
