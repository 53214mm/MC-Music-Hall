"""Contracts for V16 two room scenes and their actual access floors."""
import unittest
from castle_story_rooms import story_rooms,story_lighting
from castle_front import route_cells
from castle_sample import validate_route
from castle_finish import protected,EMISSION
from castle_interior import support_errors
from castle_service import service_variant,latch_collisions
from castle_shortcuts import solid
from vanilla_mesh import VanillaAssets


class ExistingFloorTests(unittest.TestCase):
    def test_mud_brick_is_real_full_support(self):
        blocks={(69,16,43):('mud_bricks',{},'shell'),(70,16,43):('spruce_planks',{},'shell')}
        self.assertEqual(validate_route(blocks,[(69,16,43),(70,16,43)]),[])


class StoryRoomsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=story_rooms()

    def test_music_all_old_routes_fixtures_and_features_preserved(self):
        m=self.m;b=m['before'];a=m['after']
        self.assertGreater(len(m['changed']),200);self.assertFalse(m['changed']&m['frozen'])
        self.assertTrue(all(not protected(p) for p in m['changed']))
        for p,s in b.items():
            if p not in m['replaceable']:self.assertEqual(a.get(p),s,p)
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)
        for r in m['data']['routes']:
            for x,y,z in route_cells(r['points'],r['width']):
                for k in range(4):self.assertEqual(a.get((x,y+k,z)),b.get((x,y+k,z)))
        c=m['data']['serviceV15']['shortcut']
        self.assertEqual(latch_collisions(service_variant(a,c,True)),[])

    def test_real_access_and_supported_rail_openings(self):
        m=self.m;a=m['after'];b=m['before'];connected={tuple(p) for r in m['data']['routes'] for p in r['points']}
        for r in m['routes']:
            self.assertIn(tuple(r['points'][0]),connected)
            self.assertEqual(validate_route(a,r['points']),[],r['name'])
            connected.update(map(tuple,r['points']))
        for x,y,z in m['openings']:
            self.assertTrue(b[x,y,z][0].endswith('_wall'))
            self.assertNotIn((x,y,z),a)
            for dx,dz in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
                self.assertTrue(solid(a.get((x+dx,y-1,z+dz))), (x+dx,y-1,z+dz))
        loop=next(r for r in m['routes'] if r['name']=='维修夹廊工作环线')
        self.assertEqual(loop['points'][0],loop['points'][-1])

    def test_mezzanine_floor_and_underneath_void(self):
        a=self.m['after'];b=self.m['before']
        self.assertNotIn((72,16,46),b)
        self.assertEqual(a[72,16,46][0],'spruce_planks')
        self.assertEqual(a[72,15,42][0],'stripped_spruce_log')
        self.assertEqual(a.get((72,10,46)),b.get((72,10,46)))
        for x in range(70,74):
            for z in range(40,53):self.assertIn((x,16,z),a)
        self.assertEqual(a[73,18,46][0],'grindstone')

    def test_old_anchor_manifest_uses_final_unchanged_states(self):
        m=self.m
        for f in m['features']:
            for p in f['oldAnchors']:
                p=tuple(p)
                self.assertEqual(m['after'].get(p),m['before'][p],(f['name'],p))

    def test_non_cube_furniture_support_and_vanilla_models(self):
        m=self.m;a=m['after'];assets=VanillaAssets()
        self.assertEqual(support_errors(a,m['features']),[])
        states={(s[0],tuple(sorted(s[1].items()))) for p,s in a.items() if p in m['changed']}
        self.assertTrue({'lectern','grindstone','spruce_trapdoor','oak_slab','sandstone_wall'}<={n for n,p in states})
        for n,p in states:assets.elements(n,p)
        self.assertFalse({n for n,p in states}&{'note_block','redstone_wire','piston','sticky_piston','repeater'})
        self.assertFalse(any(s[1].get('has_book')=='true' for p,s in a.items() if p in m['changed']))

    def test_new_lamps_supported_and_routes_not_dimmed(self):
        m=self.m;a=m['after'];report=story_lighting()
        self.assertEqual({tuple(f['pos']) for f in m['fixtures']},{p for p in m['changed'] if p in a and a[p][0]=='lantern'})
        self.assertEqual(report['dimmerSamples'],[])
        self.assertTrue(all(r['after']['zero']==0 for r in report['newRoutes']))
        for f in m['fixtures']:
            p=tuple(f['pos']);base=a.get((p[0],p[1]-1,p[2]))
            self.assertTrue(solid(base) or base and (base[0]=='barrel' or base[0].endswith('_slab') and base[1].get('type')=='top'))
            self.assertEqual(a[p][0],'lantern')
        self.assertGreater(sum(s[0] in EMISSION for s in a.values()),518)


if __name__=='__main__':unittest.main()
