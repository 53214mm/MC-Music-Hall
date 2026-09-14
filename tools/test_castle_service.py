"""V15 contracts first: an actual stair route plus persistent moving stone latch."""
import unittest
from castle_service import service_castle,service_variant,evaluate_latch,latch_collisions,validate_service_routes
from castle_finish import protected,EMISSION,spread_light


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=service_castle()

    def test_old_music_routes_furniture_and_shortcuts_preserved(self):
        m=self.m
        self.assertTrue(m['changed']);self.assertFalse(m['changed']&m['frozen'])
        self.assertTrue(all(not protected(p) for p in m['changed']))
        for p,s in m['before'].items():
            if p not in m['replaceable']:self.assertEqual(m['after'].get(p),s,p)
        self.assertEqual(sum(s[0]=='note_block' for s in m['after'].values()),2307)

    def test_genuine_stair_and_both_old_route_endpoints(self):
        self.assertEqual(validate_service_routes(self.m['after']),[])
        m=self.m;oldpoints={tuple(p) for r in m['data']['routes'] for p in r['points']}
        self.assertIn(tuple(m['shortcut']['points'][0]),oldpoints)
        self.assertIn(tuple(m['shortcut']['points'][-1]),oldpoints)
        self.assertLess(m['shortcut']['shortcutGraphSteps'],m['shortcut']['ordinaryGraphSteps'])
        self.assertEqual(m['after'][55,16,54][1]['facing'],'south')

    def test_default_closed_open_close_hold_states(self):
        m=self.m;c=m['shortcut'];a=m['after']
        opened=service_variant(a,c,True)
        self.assertEqual(a[55,4,32][0],'piston_head');self.assertEqual(a[55,3,32][0],'chiseled_sandstone')
        self.assertNotIn((55,3,32),opened);self.assertEqual(opened[55,4,32][0],'chiseled_sandstone')
        self.assertEqual(opened[55,5,32][1]['extended'],'false')
        self.assertEqual(service_variant(opened,c,True),opened)
        self.assertEqual(service_variant(opened,c,False),a)
        for on in(False,True,True,False):
            r=evaluate_latch(a,c,on)
            self.assertEqual(r['pistonExtended'],not on);self.assertEqual(r['torchLit'],not on)

    def test_real_latch_sweep_and_side_jambs(self):
        m=self.m;c=m['shortcut'];a=m['after']
        self.assertIn((55,3,32),latch_collisions(a))
        self.assertEqual(latch_collisions(service_variant(a,c,True)),[])
        for x in(54,56):
            for y in(2,3):self.assertIn((x,y,32),a)

    def test_missing_moving_block_wrong_repeater_or_qc_power_rejected(self):
        m=self.m;c=m['shortcut'];a=dict(m['after']);a.pop((55,3,32))
        with self.assertRaises(ValueError):evaluate_latch(a,c,True)
        a=dict(m['after']);n,p,g=a[58,5,32];a[58,5,32]=(n,{**p,'facing':'west'},g)
        with self.assertRaises(ValueError):evaluate_latch(a,c,True)
        a=dict(m['after']);a[55,7,32]=('redstone_block',{},'shell')
        with self.assertRaises(ValueError):evaluate_latch(a,c,True)

    def test_missing_stair_headroom_support_and_dust_step_rejected(self):
        a=dict(self.m['after']);a[55,16,53]=('stone',{},'shell')
        self.assertTrue(validate_service_routes(a))
        a=dict(self.m['after']);a.pop((55,10,48))
        self.assertTrue(validate_service_routes(a))
        a=dict(self.m['after']);a[59,4,26]=('stone',{},'shell')
        with self.assertRaises(ValueError):evaluate_latch(a,self.m['shortcut'],True)

    def test_entry_rails_open_only_after_same_height_floor_exists(self):
        a=self.m['after']
        for x in(54,55,56):
            self.assertNotIn((x,2,6),a);self.assertIn((x,1,6),a);self.assertIn((x,1,7),a)
            self.assertNotIn((x,17,56),a);self.assertIn((x,16,56),a)
        for x in(53,57):
            self.assertIn((x,2,6),a);self.assertIn((x,17,56),a)

    def test_last_dust_connects_to_real_repeater_and_manifest_is_bound(self):
        a=self.m['after'];c=self.m['shortcut']
        self.assertEqual(a[59,5,32][1]['west'],'side')
        self.assertEqual(a[59,5,32][1]['south'],'none')
        c={**c,'piston':(55,6,32)}
        with self.assertRaises(ValueError):evaluate_latch(a,c,True)

    def test_inconsistent_saved_states_and_side_locking_are_rejected(self):
        c=self.m['shortcut']
        for pos,property,value in [((57,3,26),'powered','true'),((56,5,32),'lit','false'),((59,5,32),'power','9')]:
            a=dict(self.m['after']);n,pr,g=a[pos];a[pos]=(n,{**pr,property:value},g)
            with self.assertRaises(ValueError):evaluate_latch(a,c,True)
        a=dict(self.m['after']);a[58,5,31]=('repeater',{'facing':'north','powered':'true','locked':'false','delay':'1'},'shell')
        with self.assertRaises(ValueError):evaluate_latch(a,c,True)

    def test_structural_isolation_stair_profile_and_lighting(self):
        from castle_service import service_isolation,stair_profile
        m=self.m;iso=service_isolation(m['before'],m['after'])
        self.assertEqual(iso['foreignResponsive'],[])
        self.assertGreater(iso['minimumMusicChebyshev'],2)
        self.assertEqual(stair_profile(m['after'])['maxRiser'],0.5)
        a=dict(m['after']);a[60,5,32]=('redstone_block',{},'shell')
        with self.assertRaises(ValueError):service_isolation(m['before'],a)
        field=spread_light(m['after'],{p:EMISSION[s[0]] for p,s in m['after'].items() if s[0] in EMISSION})
        samples={(x,y+1,z) for x,y,z in m['floorCells'] if (x,y+1,z) not in m['after']}
        self.assertGreaterEqual(min(field.get(p,0) for p in samples),5)

    def test_reviewed_foreign_inputs_cannot_bypass_inversion(self):
        c=self.m['shortcut']
        cases=[{(57,5,31):('lever',{'face':'wall','facing':'north','powered':'true'},'shell')},
               {(55,7,32):('cobblestone',{},'shell'),(55,8,32):('lever',{'face':'floor','facing':'north','powered':'true'},'shell')},
               {(60,5,32):('redstone_block',{},'shell')},
               {(55,7,32):('detector_rail',{'powered':'true','shape':'north_south','waterlogged':'false'},'shell')}]
        for changes in cases:
            a={**self.m['after'],**changes}
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):evaluate_latch(a,c,True)


if __name__=='__main__':unittest.main()
