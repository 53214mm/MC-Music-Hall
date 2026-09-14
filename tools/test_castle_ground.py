import unittest
from castle_ground import surface_columns, recolor_ground, paving_material
from castle_finish import protected, EMISSION
from castle_front import route_cells
from castle_sample import validate_route
from vanilla_mesh import VanillaAssets


class SurfaceRuleTests(unittest.TestCase):
    def test_highest_block_only_and_roof_is_not_ground(self):
        rock=('stone',{},'terrain')
        b={(0,-2,0):rock,(0,-1,0):rock,(0,0,0):rock,(1,-1,0):rock,(1,6,0):('deepslate_tiles',{},'shell')}
        top=surface_columns(b)
        self.assertEqual(top,{(0,0):0,(1,0):6})

    def test_paving_keeps_stairs_as_stairs_and_does_not_paint_rails(self):
        self.assertEqual(paving_material('stone_brick_stairs',(0,-12,130)),'smooth_sandstone_stairs')
        self.assertEqual(paving_material('stone_bricks',(0,-12,130)),'smooth_sandstone')
        self.assertEqual(paving_material('stone_brick_wall',(0,-12,130)),'stone_brick_wall')


class GroundIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=recolor_ground()

    def test_only_one_top_cell_per_column_changes_no_new_coordinates_or_states(self):
        m=self.m;b=m['before'];a=m['after'];delta=m['changed']
        self.assertEqual(a.keys(),b.keys());self.assertEqual(len(a),518511)
        self.assertGreater(len(delta),6000)
        self.assertEqual(len({(p[0],p[2]) for p in delta}),len(delta))
        for p,s in b.items():
            self.assertEqual(s[1:],a[p][1:],p)
            if p in delta:
                self.assertEqual(p[1],m['top'][p[0],p[2]],p)
                self.assertGreater(p[1],-40)
                self.assertTrue(s[2]=='terrain' or p in m['paving'],p)
            else:self.assertEqual(s,a[p],p)
        self.assertGreater(m['zones']['自然地表'],1000)
        self.assertGreater(m['zones']['露天铺地'],100)

    def test_music_fixtures_buildings_roofs_and_subsurface_preserved(self):
        m=self.m
        for p,s in m['before'].items():
            if protected(p) or p in m['frozen'] or s[2] not in ('shell','terrain') or s[0] in EMISSION or (s[2]=='shell' and p not in m['paving']) or p[1]<m['top'][p[0],p[2]]:
                self.assertEqual(s,m['after'][p],p)

    def test_real_replacements_have_identical_geometry(self):
        m=self.m;assets=VanillaAssets()
        def geom(n,props):
            return sorted(tuple(sorted(tuple(sorted(f['vertices'])) for f in e['faces'])) for e in assets.elements(n,props))
        states={(m['before'][p][0],m['after'][p][0],tuple(sorted(m['after'][p][1].items()))) for p in m['changed']}
        for n,N,s in states:self.assertEqual(geom(n,s),geom(N,s),(n,N,s))

    def test_all_routes_preserve_support_clearance_and_stair_direction(self):
        m=self.m
        for r in m['data']['routes']:
            self.assertEqual(validate_route(m['after'],list(map(tuple,r['points']))),[],r['name'])
            for p in route_cells(r['points'],r['width']):self.assertEqual(validate_route(m['after'],[p]),[],(r['name'],p))


if __name__=='__main__':unittest.main()
