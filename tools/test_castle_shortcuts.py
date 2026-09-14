"""Tests before V14 implementation: state, direction, geometry, protection."""
import unittest
from castle_shortcuts import shortcut_castle,evaluate_circuit,variant,player_collisions,interaction_lower_bound,isolation_audit
from castle_front import route_cells
from castle_finish import protected


class CircuitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=shortcut_castle()

    def test_off_on_off_and_real_repeater_input_direction(self):
        for c in self.m['shortcuts']:
            for on in (False,True,False):
                r=evaluate_circuit(self.m['after'],c,on)
                self.assertEqual(r['open'],on)
                self.assertTrue(all(v>0 if on else v==0 for v in r['wirePower']))
        c=self.m['shortcuts'][0];bad=dict(self.m['after']);p=tuple(c['repeater'])
        n,props,g=bad[p];bad[p]=(n,{**props,'facing':'south'},g)
        with self.assertRaises(ValueError):evaluate_circuit(bad,c,True)

    def test_broken_line_and_step_headroom_fail_closed(self):
        c=self.m['shortcuts'][0];a=dict(self.m['after']);a.pop(tuple(c['wire'][2]))
        with self.assertRaises(ValueError):evaluate_circuit(a,c,True)
        a=dict(self.m['after']);a[-35,5,58]=('stone',{},'shell')
        with self.assertRaises(ValueError):evaluate_circuit(a,c,True)

    def test_missing_gate_wrong_ladder_and_backing_rejected(self):
        for c in self.m['shortcuts']:
            a=dict(self.m['after']);a.pop(tuple(c['gate']))
            with self.assertRaises(ValueError):evaluate_circuit(a,c,True)
        c=self.m['shortcuts'][1];a=dict(self.m['after']);n,p,g=a[-46,25,2]
        a[-46,25,2]=(n,{**p,'facing':'west'},g)
        with self.assertRaises(ValueError):evaluate_circuit(a,c,True)
        a=dict(self.m['after']);a.pop((-47,25,2))
        with self.assertRaises(ValueError):evaluate_circuit(a,c,True)

    def test_moved_lever_changes_distance_and_wrong_wire_shape_fails(self):
        c=self.m['shortcuts'][1]
        self.assertLess(interaction_lower_bound({**c,'lever':(-45,34,0)}),4.5)
        c=self.m['shortcuts'][0];a=dict(self.m['after']);p=tuple(c['wire'][1]);n,q,g=a[p]
        a[p]=(n,{**q,'south':'none'},g)
        with self.assertRaises(ValueError):evaluate_circuit(a,c,True)

    def test_continuous_collision_catches_closed_thin_portals(self):
        for c in self.m['shortcuts']:
            closed=self.m['after'];opened=variant(closed,c,True)
            self.assertTrue(player_collisions(closed,c['track']),c['name'])
            self.assertEqual(player_collisions(opened,c['track']),[],c['name'])
            self.assertTrue(player_collisions(variant(opened,c,False),c['track']))

    def test_music_old_routes_and_old_furniture_preserved(self):
        m=self.m;b=m['before'];a=m['after']
        self.assertTrue(m['changed']);self.assertFalse(m['changed']&m['frozen'])
        self.assertTrue(all(not protected(p) for p in m['changed']))
        for p,s in b.items():
            if p not in m['replaceable']:self.assertEqual(a.get(p),s,p)
        for r in m['data']['routes']:
            for x,y,z in route_cells(r['points'],r['width']):
                for k in range(4):self.assertEqual(a.get((x,y+k,z)),b.get((x,y+k,z)))
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)

    def test_ladder_is_complete_and_gate_matches_direction(self):
        a=self.m['after']
        for y in range(17,33):self.assertEqual(a[-46,y,2],('ladder',{'facing':'east','waterlogged':'false'},'shell'))
        self.assertEqual(a[-46,33,2][0],'iron_trapdoor')
        self.assertEqual(a[-46,33,2][1]['facing'],'east')
        for z in range(-4,3):
            self.assertEqual(a[-48,34,z],self.m['before'][-48,34,z])
            self.assertEqual(a[-47,33,z],self.m['before'][-47,33,z])

    def test_both_endpoints_connect_and_shorten_registered_graph(self):
        for c in self.m['shortcuts']:
            self.assertGreater(c['ordinaryGraphSteps'],c['shortcutGraphSteps'])
            self.assertGreater(c['outsideLeverDistanceLowerBound'],4.5)
        self.assertEqual(len(self.m['shortcuts']),2)

    def test_no_power_coupling_to_old_responsive_parts(self):
        r=isolation_audit(self.m['before'],self.m['shortcuts'],self.m['changed'])
        self.assertEqual(r['oldResponsiveWithinTwo'],[])
        self.assertGreater(r['minimumMusicChebyshev'],2)
        b=dict(self.m['before']);b[-34,5,55]=('note_block',{},'test')
        with self.assertRaises(ValueError):isolation_audit(b,self.m['shortcuts'],self.m['changed'])

    def test_new_shortcut_sampling_and_light_support(self):
        from castle_finish import spread_light,EMISSION
        a=self.m['after'];f=spread_light(a,{p:EMISSION[s[0]] for p,s in a.items() if s[0] in EMISSION})
        for c in self.m['shortcuts']:
            gate=set(map(tuple,c['gateParts']))
            points={(x,y+1,z) for x,y,z in c['points']}-gate
            self.assertGreater(min(f.get(p,0) for p in points),0,c['id'])
        self.assertEqual(a[-30,2,65][0],'lantern')
        self.assertEqual(a[-30,1,65][0],'chiseled_tuff_bricks')
        self.assertEqual(a[-46,26,3][0],'lantern')
        self.assertEqual(a[-46,25,3][0],'cut_sandstone')
        self.assertEqual(a[-47,25,3],self.m['before'][-47,25,3])

    def test_upper_control_post_is_not_floating(self):
        from castle_shortcuts import solid
        a=self.m['after']
        self.assertTrue(solid(a.get((-46,33,-4))))
        self.assertTrue(solid(a.get((-46,32,-4))))


if __name__=='__main__':unittest.main()
