"""V13 bounded interior transformations and real access contracts."""
import unittest
from castle_interior import RoomEditor,interior_castle,interior_lighting,BRANCHES
from castle_sample import validate_route
from castle_front import route_cells
from castle_finish import protected,EMISSION
from vanilla_mesh import VanillaAssets


class EditTests(unittest.TestCase):
    def test_rejects_entire_patch_on_unapproved_replace_or_frozen_air(self):
        old={(0,0,0):('spruce_planks',{},'shell')}
        e=RoomEditor(old,{(2,0,0)},set())
        for edits in [{(1,0,0):('oak_planks',{},'shell'),(0,0,0):None},
                      {(1,0,0):('oak_planks',{},'shell'),(2,0,0):('oak_planks',{},'shell')}]:
            with self.assertRaises(ValueError):e.apply('fixture',edits,(-1,3,-1,1,-1,1))
            self.assertEqual(e.blocks,old)

    def test_region_cannot_unlock_music_or_outside_cell(self):
        e=RoomEditor({},set(),set())
        for p in [(20,10,10),(-90,0,0)]:
            with self.assertRaises(ValueError):e.apply('fixture',{p:('oak_planks',{},'shell')},(-80,-50,0,5,40,70))


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=interior_castle()

    def test_music_terrain_envelope_and_old_routes(self):
        m=self.m;b=m['before'];a=m['after']
        self.assertTrue(m['changed']);self.assertGreater(len(m['changed']),150)
        self.assertFalse(m['changed']&m['frozen'])
        self.assertTrue(all(not protected(p) for p in m['changed']))
        for p,s in b.items():
            if p not in m['replaceable']:self.assertEqual(a.get(p),s,p)
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)
        for r in m['data']['routes']:
            for x,y,z in route_cells(r['points'],r['width']):
                for k in range(4):self.assertEqual(a.get((x,y+k,z)),b.get((x,y+k,z)))

    def test_new_routes_are_supported_clear_and_connected(self):
        m=self.m;oldpoints={tuple(p) for r in m['data']['routes'] for p in r['points']}
        self.assertEqual(len(m['routes']),len(BRANCHES))
        for r in m['routes']:
            self.assertIn(tuple(r['points'][0]),oldpoints)
            self.assertEqual(validate_route(m['after'],r['points']),[],r['name'])
        loop=next(r for r in m['routes'] if r['kind']=='interior_loop')
        self.assertEqual(loop['points'][0],loop['points'][-1]);self.assertGreater(len(set(map(tuple,loop['points']))),25)
        for x,y,z in m['openings']:
            for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]:
                self.assertIn((x+dx,y-1,z+dz),m['before'])
            self.assertNotIn((x,y,z),m['after'])

    def test_furniture_has_real_support_and_all_states_resolve(self):
        m=self.m;assets=VanillaAssets()
        for f in m['features']:
            self.assertTrue(f['anchors'],f['name'])
            for p in map(tuple,f['anchors']):self.assertIn(p,m['before'])
        self.assertEqual(m['supportErrors'],[])
        states={(s[0],tuple(sorted(s[1].items()))) for p,s in m['after'].items() if p in m['changed']}
        for n,props in states:assets.elements(n,props)
        for (x,y,z),s in m['after'].items():
            if (x,y,z) not in m['changed'] or not s[0].endswith('_carpet'):continue
            below=m['after'].get((x,y-1,z));self.assertIsNotNone(below)
            self.assertTrue(below[0].endswith('_planks') or below[0].endswith('_slab') and below[1].get('type')=='top')

    def test_story_is_distinct_and_no_fake_mechanisms_or_content(self):
        m=self.m
        self.assertEqual({f['zone'] for f in m['features']},{'shelter','kitchen','archive','upper'})
        self.assertGreaterEqual(len(m['features']),10)
        a=m['after'];c={a[p][0] for p in m['changed'] if p in a}
        self.assertTrue({'furnace','crafting_table','bookshelf','spruce_trapdoor','oak_slab'}<=c)
        self.assertGreaterEqual(len([n for n in c if n.endswith('_carpet')]),3)
        self.assertFalse(c&{'redstone_wire','repeater','piston','sticky_piston','note_block','chest'})
        for p,s in m['before'].items():
            if s[0] in EMISSION:self.assertEqual(a[p],s)

    def test_open_void_and_new_route_lighting(self):
        a=self.m['after']
        # A vertical view from the upper void to the actual desk, not a plan arrow through a floor.
        self.assertEqual(a[-37,17,7][0],'oak_slab')
        self.assertTrue(all((-37,y,7) not in a for y in range(18,34)))
        report=interior_lighting()
        self.assertEqual(report['dimmerSamples'],[])
        self.assertEqual(report['after']['zero'],0)
        self.assertEqual(len(report['newRoutes']),5)
        self.assertTrue(all(r['after']['zero']==0 for r in report['newRoutes']))
        self.assertEqual(sum(s[0] in EMISSION for s in a.values()),510)


if __name__=='__main__':unittest.main()
