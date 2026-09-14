"""V19 exterior edits must preserve the signed-off castle behind them."""
import unittest
from castle_facade_v19 import facade_v19,REGION,roof_height
from castle_finish import protected,EMISSION
from castle_interior import support_errors
from castle_sample import validate_route
from castle_front import route_cells
from vanilla_mesh import VanillaAssets
from build_castle_facade_v19 import viewer_neighborhood

class FacadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=facade_v19()

    def test_frozen_music_routes_features_and_terrain(self):
        m=self.m;b=m['before'];a=m['after']
        self.assertGreater(len(m['changed']),1500)
        for p in m['frozen']:self.assertEqual(a.get(p),b.get(p),p)
        for p in m['changed']:
            self.assertFalse(protected(p));self.assertTrue(any(all(r[2*i]<=p[i]<=r[2*i+1] for i in range(3)) for r in REGION.values()),p)
            self.assertTrue(a.get(p) is None or a[p][2]=='shell')
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)
        for p,s in b.items():
            if s[0] in EMISSION:self.assertEqual(a[p],s)
        self.assertEqual(sum(s[0] in EMISSION for s in a.values()),541)

    def test_support_and_no_old_window_damage(self):
        m=self.m;self.assertEqual(support_errors(m['after'],m['features']),[])
        for f in m['data']['features']:
            r=f['region']
            self.assertFalse(any(all(r[2*i]<=p[i]<=r[2*i+1] for i in range(3)) for p in m['changed']),f['name'])

    def test_gable_joins_roof_and_keeps_backing(self):
        a=self.m['after'];b=self.m['before']
        self.assertGreater(max(p[1] for p in self.m['changed'] if p[2]<-42),60)
        self.assertTrue(self.m['roofJoins'])
        for p in self.m['roofJoins']:self.assertIsNotNone(b.get(p))
        for p in self.m['blindBacks']:self.assertIsNotNone(a.get(p))
        self.assertEqual(roof_height(b,26,-30),56)

    def test_non_cube_detail_and_target_states(self):
        a=self.m['after'];c=self.m['changed'];names={a[p][0] for p in c if p in a}
        for suffix in ('_stairs','_slab','_wall'):self.assertTrue(any(n.endswith(suffix) for n in names))
        self.assertIn('bricks',names);self.assertIn('cut_sandstone',names)
        assets=VanillaAssets()
        for n,props in {(a[p][0],tuple(sorted(a[p][1].items()))) for p in c if p in a}:assets.elements(n,props)

    def test_all_old_routes(self):
        for r in self.m['data']['routes']:
            self.assertEqual(validate_route(self.m['after'],r['points']),[],r['name'])
            for p in route_cells(r['points'],r['width']):self.assertEqual(validate_route(self.m['after'],[p]),[])

    def test_viewer_includes_feature_beyond_overview(self):
        # The small dormer roof tails are outside the three overview slices.
        blocks={(2,54,-36):('deepslate_tiles',{},'shell'),(200,0,0):('stone',{},'shell')}
        views=[dict(region=[0,51,-9,74,-49,-38])]
        features=[dict(region=[2,10,51,60,-44,-18])]
        self.assertEqual(viewer_neighborhood(blocks,views,features),{(2,54,-36):blocks[2,54,-36]})

if __name__=='__main__':unittest.main()
