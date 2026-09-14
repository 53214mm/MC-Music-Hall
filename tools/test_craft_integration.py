import unittest
from castle_craft_integration import rotate_position, rotate_state, ProtectedEditor, integrate_castle
from castle_finish import protected, EMISSION
from castle_front import route_cells
from castle_sample import validate_route
from vanilla_mesh import VanillaAssets


class PlacementTests(unittest.TestCase):
    def test_rotation_moves_directions_axes_and_connections(self):
        self.assertEqual(rotate_position((2,3,5),1),(-5,3,2))
        self.assertEqual(rotate_position((2,3,5),3),(5,3,-2))
        state=('spruce_fence',dict(north='false',south='true',east='false',west='false'),'shell')
        rotated=rotate_state(state,1)
        self.assertEqual(rotated[1]['west'],'true')
        self.assertEqual(rotated[1]['south'],'false')
        self.assertEqual(rotate_state(('stripped_spruce_log',dict(axis='x'),'shell'),1)[1]['axis'],'z')
        stair=('spruce_stairs',dict(facing='east',half='top',shape='inner_left'),'shell')
        self.assertEqual(rotate_state(stair,3)[1],dict(facing='north',half='top',shape='inner_left'))
        self.assertEqual(state[1]['south'],'true')
        self.assertEqual(rotate_state(state,4),state)

    def test_protected_edit_rejected_atomically_including_air(self):
        original={(61,2,3):('stone_bricks',{},'shell')}
        editor=ProtectedEditor(original,{(62,2,3)},set())
        with self.assertRaises(ValueError):
            editor.apply('conflict',{(61,2,3):('bricks',{},'shell'),(62,2,3):('bricks',{},'shell')})
        self.assertEqual(editor.blocks,original)
        with self.assertRaises(ValueError):editor.apply('delete',{(61,2,3):None,(0,0,0):('bricks',{},'shell')})
        self.assertEqual(editor.blocks,original)
        editor.apply('safe',{(61,2,3):('bricks',{},'shell')})
        self.assertEqual(editor.blocks[61,2,3][0],'bricks')


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=integrate_castle()

    def test_frozen_music_routes_lights_and_terrain(self):
        m=self.m;a=m['after'];b=m['before']
        for p in set(a)|set(b):
            if protected(p) or p in m['frozen'] or b.get(p,('',{},''))[2]!='shell' and p in b:
                self.assertEqual(a.get(p),b.get(p),p)
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)
        self.assertEqual({p:s for p,s in b.items() if s[0] in EMISSION},{p:s for p,s in a.items() if s[0] in EMISSION})
        for r in m['data']['routes']:
            self.assertEqual(validate_route(a,list(map(tuple,r['points']))),[],r['name'])
            for p in route_cells(r['points'],r['width']):self.assertEqual(validate_route(a,[p]),[],(r['name'],p))

    def test_actual_features_have_geometry_and_all_new_states_resolve(self):
        m=self.m;assets=VanillaAssets()
        self.assertEqual({f['family'] for f in m['features']},{'window','dormer','timber'})
        self.assertEqual(len(m['features']),12)
        for f in m['features']:
            self.assertGreater(f['changed'],20,f)
            self.assertTrue(all(p in m['after'] for p in f['anchors']),f)
        states={(m['after'][p][0],tuple(sorted(m['after'][p][1].items()))) for p in m['changed'] if p in m['after']}
        for name,props in states:self.assertTrue(assets.elements(name,props),(name,props))
        self.assertTrue(any(p not in m['after'] for p in m['changed']))
        self.assertTrue(any(m['after'][p][0]=='spruce_trapdoor' for p in m['changed'] if p in m['after']))
        self.assertGreater(m['zone_counts']['唱诗堂'],200)

    def test_window_jamb_returns_meet_the_existing_backing(self):
        a=self.m['after']
        for x in(-4,6,36,46):
            for y in range(9,23):
                for z in(42,43,44):self.assertTrue((x,y,z) in a,('south jamb return',x,y,z))

    def test_steep_arch_risers_do_not_leave_gaps_between_steps(self):
        a=self.m['after']
        for x in(-4,6,36,46):
            for y in(23,24,25):self.assertEqual(a.get((x,y,44),('',{},''))[0],'smooth_sandstone',(x,y,44))

    def test_bay_window_cuts_the_existing_second_wall_course(self):
        for z in range(58,65):
            for y in range(9,13):self.assertFalse((-52,y,z) in self.m['after'],('bay backing blocked',-52,y,z))

    def test_old_outer_surround_is_removed_after_palette_conversion(self):
        self.assertIsNone(self.m['after'].get((8,20,46)))


if __name__=='__main__':unittest.main()
