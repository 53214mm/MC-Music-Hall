import unittest
from castle_palette import recolor_castle, material_for, zone_for
from castle_finish import protected, EMISSION
from castle_sample import validate_route
from castle_front import route_cells
from vanilla_mesh import VanillaAssets


class PaletteRulesTests(unittest.TestCase):
    def test_body_zones_share_a_controlled_palette(self):
        self.assertEqual(material_for('stone_bricks',(57,30,25)), 'mud_bricks')
        self.assertEqual(material_for('stone_bricks',(-31,28,5)), 'bricks')
        self.assertEqual(material_for('stone_bricks',(83,5,35)), 'mud_bricks')
        self.assertEqual(material_for('stone_bricks',(-70,15,70)), 'calcite')
        self.assertEqual(material_for('polished_andesite',(-31,28,5)), 'cut_sandstone')

    def test_deep_bases_roofs_and_existing_warm_materials_are_not_repainted(self):
        for n in ('deepslate_tiles','deepslate_tile_stairs','bricks','calcite','waxed_weathered_cut_copper_slab','smooth_sandstone'):
            self.assertEqual(material_for(n,(57,30,25)),n)
        self.assertEqual(material_for('stone_bricks',(57,-15,25)), 'stone_bricks')


class WholePaletteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=recolor_castle()

    def test_no_coordinate_or_state_changes_and_protected_content_matches(self):
        m=self.m;a=m['after'];b=m['before']
        self.assertEqual(len(a),518511)
        self.assertTrue(set(a)==set(b))
        for p,s in b.items():
            self.assertEqual(s[1:],a[p][1:],p)
            if protected(p) or p in m['frozen'] or s[2]!='shell':self.assertEqual(s,a[p],p)
        self.assertEqual({p:s for p,s in a.items() if s[0] in EMISSION},{p:s for p,s in b.items() if s[0] in EMISSION})
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)
        self.assertGreater(len(m['changed']),25000)
        for zone in ('主堡','冠塔','西翼藏谱馆','外围长墙','南门楼','东侧维修翼'):
            self.assertGreater(m['zone_counts'][zone],200,zone)

    def test_every_material_replacement_has_identical_vanilla_shape(self):
        m=self.m;assets=VanillaAssets()
        def geometry(name,props):
            return sorted(tuple(sorted(tuple(sorted(f['vertices'])) for f in el['faces'])) for el in assets.elements(name,props))
        transitions={(m['before'][p][0],m['after'][p][0],tuple(sorted(m['after'][p][1].items()))) for p in m['changed']}
        for old,new,props in transitions:self.assertEqual(geometry(old,props),geometry(new,props),(old,new,props))

    def test_routes_and_v7_openings_survive(self):
        m=self.m
        for r in m['data']['routes']:
            self.assertEqual(validate_route(m['after'],list(map(tuple,r['points']))),[],r['name'])
            for p in route_cells(r['points'],r['width']):self.assertEqual(validate_route(m['after'],[p]),[],(r['name'],p))
        for p in [(8,20,46),(-52,10,61)]:self.assertFalse(p in m['after'],p)
        self.assertEqual(m['after'][6,24,44],m['before'][6,24,44])


if __name__=='__main__':unittest.main()
