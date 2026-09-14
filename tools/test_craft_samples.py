import unittest
from collections import Counter
from castle_craft_samples import samples
from vanilla_mesh import VanillaAssets


class CraftSamplesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.samples=samples();cls.assets=VanillaAssets()

    def test_bounds_and_all_states_have_vanilla_geometry(self):
        for sample in self.samples:
            for p,(n,props,g) in sample.blocks.items():
                self.assertTrue(all(sample.region[2*i]<=p[i]<=sample.region[2*i+1] for i in range(3)),(sample.id,p))
                self.assertTrue(self.assets.elements(n,tuple(sorted(props.items()))),(sample.id,p,n))

    def test_non_cubic_families_and_no_redstone(self):
        for s in self.samples:
            names={n for n,p,g in s.blocks.values()}
            for suffix in('_stairs','_slab','_fence','_trapdoor'):self.assertTrue(any(n.endswith(suffix) for n in names),(s.id,suffix))
            self.assertFalse({'redstone_wire','repeater','note_block','iron_trapdoor'}&names)
            for p,(n,props,g) in s.blocks.items():
                if n=='lantern' and props.get('hanging')=='true':self.assertIn((p[0],p[1]+1,p[2]),s.blocks,(s.id,p))

    def test_three_samples_have_different_roof_roles(self):
        a,b,c=self.samples
        self.assertIn('sandstone_wall',{n for n,p,g in a.blocks.values()})
        self.assertTrue(any(n=='deepslate_tile_stairs' for n,p,g in b.blocks.values()))
        self.assertTrue(any(n=='waxed_weathered_cut_copper_slab' and props['type']=='top' for n,props,g in c.blocks.values()))
        # Bay window opening remains open through the old wall plane.
        self.assertNotIn((5,10,3),c.blocks)


if __name__=='__main__':unittest.main()
