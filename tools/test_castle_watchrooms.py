"""V17 contracts: dry cistern, distinct towers, supported real access."""
import unittest
from castle_detail import ROOT,read_model
from castle_front import route_cells
from castle_sample import validate_route
from castle_finish import protected,EMISSION
from castle_interior import support_errors
from castle_story_rooms import frozen_cells
from castle_watchrooms import watchrooms,watch_lighting,sight_trace
from vanilla_mesh import VanillaAssets


class SightTests(unittest.TestCase):
    def test_blocked_and_clear_voxel_sight(self):
        b={(2,1,0):('stone_bricks',{},'shell')}
        self.assertEqual(sight_trace(b,(.5,1.5,.5),(4.5,1.5,.5)),(2,1,0))
        self.assertIsNone(sight_trace(b,(.5,2.5,.5),(4.5,2.5,.5)))

    def test_tiny_corner_intersection_cannot_be_skipped(self):
        b={(2,1,0):('stone_bricks',{},'shell')}
        self.assertEqual(sight_trace(b,(.5,-1.499,.5),(4.5,2.501,.5)),(2,1,0))

    def test_nearest_hit_and_wall_above_containing_voxel(self):
        b={(2,1,0):('stone_bricks',{},'shell'),(3,1,0):('stone_bricks',{},'shell')}
        self.assertEqual(sight_trace(b,(4.5,1.5,.5),(.5,1.5,.5)),(3,1,0))
        self.assertEqual(sight_trace({(2,1,0):('sandstone_wall',{},'shell')},(.5,2.25,.5),(4.5,2.25,.5)),(2,1,0))


class SavedRouteTests(unittest.TestCase):
    def test_saved_json_stair_points_are_accepted(self):
        b={(0,0,0):('stone_bricks',{},'shell'),(1,1,0):('spruce_stairs',dict(facing='east',half='bottom',shape='straight',waterlogged='false'),'shell')}
        self.assertEqual(validate_route(b,[[0,0,0],[1,1,0]]),[])


class WatchroomsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=watchrooms()

    def test_exact_original_protections(self):
        m=self.m;b=m['before'];a=m['after']
        self.assertFalse(m['changed']&frozen_cells(m['data'],b))
        self.assertTrue(all(not protected(p) for p in m['changed']))
        self.assertTrue(all(a.get(p)==s for p,s in b.items() if p not in m['replaceable']))
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)

    def test_connected_real_new_routes_and_same_height_rail_openings(self):
        m=self.m;a=m['after'];connected={tuple(p) for r in m['data']['routes'] for p in r['points']}
        for r in m['routes']:
            self.assertIn(tuple(r['points'][0]),connected,r['name'])
            self.assertEqual(validate_route(a,r['points']),[],r['name'])
            connected.update(map(tuple,r['points']))
        for x,y,z in m['openings']:
            self.assertNotIn((x,y,z),a)
            for dx,dz in((0,0),(1,0),(-1,0),(0,1),(0,-1)):
                self.assertIn((x+dx,y-1,z+dz),a)

    def test_structural_anchors_and_real_models(self):
        m=self.m;a=m['after'];assets=VanillaAssets()
        self.assertEqual(support_errors(a,m['features']),[])
        for f in m['features']:
            for p in f['oldAnchors']:self.assertEqual(a.get(tuple(p)),m['before'][tuple(p)])
        for n,props in {(a[p][0],tuple(sorted(a[p][1].items()))) for p in m['changed'] if p in a}:assets.elements(n,props)

    def test_cistern_stays_dry_and_has_reasoned_water_mark(self):
        m=self.m;a=m['after']
        self.assertTrue(m['watermarks'])
        for p in m['watermarks']:self.assertEqual(a[p][0],'mossy_stone_bricks')
        self.assertFalse({a[p][0] for p in m['changed'] if p in a}&{'water','lava','note_block','redstone_wire','repeater','piston','sticky_piston','lever'})
        self.assertFalse(any(a[p][1].get('has_book')=='true' for p in m['changed'] if p in a))

    def test_maintenance_actual_riser_and_lookout(self):
        m=self.m;a=m['after']
        self.assertEqual(a[65,55,13][0],'spruce_stairs')
        self.assertEqual(a[65,55,13][1]['facing'],'east')
        self.assertGreater(max(p[1] for p in m['lookoutFloor']),76)
        self.assertTrue(m['views'])
        for view in m['views']:self.assertIsNone(sight_trace(a,view['eye'],view['target']))
        self.assertEqual(a[-6,65,-23][1]['facing'],'south')
        self.assertEqual(a[-6,66,-23][1]['facing'],'north')

    def test_lamp_inventory_and_old_lighting(self):
        m=self.m;a=m['after'];light=watch_lighting()
        self.assertEqual({tuple(f['pos']) for f in m['fixtures']},{p for p in m['changed'] if p in a and a[p][0]=='lantern'})
        self.assertEqual(light['dimmerSamples'],[])
        self.assertTrue(all(row['after']['zero']==0 for row in light['newRoutes']))


if __name__=='__main__':unittest.main()
