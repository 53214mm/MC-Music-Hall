import unittest
from collections import Counter
from castle_pathlight import pathlight_castle, AirOnlyLightingEditor, approved_music_parts, pathlight_audit
from castle_finish import EMISSION,protected
from castle_front import route_cells
from vanilla_mesh import VanillaAssets


class AdditiveGuardTests(unittest.TestCase):
    def test_rejects_overwrite_frozen_and_unapproved_inside_atomically(self):
        before={(60,0,0):('stone_bricks',{},'shell')}
        light=('lantern',{'hanging':'true','waterlogged':'false'},'shell')
        for bad in ((60,0,0),(61,0,0),(20,1,5)):
            editor=AirOnlyLightingEditor(before,{(61,0,0)},approved_music_parts())
            with self.assertRaises(ValueError):editor.apply('bad',{(70,0,0):light,bad:light})
            self.assertEqual(editor.blocks,before)

    def test_music_exception_checks_exact_state_not_only_position(self):
        approved=approved_music_parts();p=(20,1,4)
        editor=AirOnlyLightingEditor({},set(),approved)
        with self.assertRaises(ValueError):editor.apply('wrong',{p:('redstone_wire',{},'shell')})
        self.assertEqual(editor.blocks,{})
        editor.apply('approved',{p:approved[p]})
        self.assertEqual(editor.blocks[p],approved[p])


class PathLightingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=pathlight_castle()

    def test_all_old_blocks_and_music_halo_are_unchanged(self):
        m=self.m
        self.assertTrue(set(m['before'])<=set(m['after']))
        self.assertTrue(all(m['after'][p]==s for p,s in m['before'].items()))
        self.assertFalse(m['added'] & m['frozen'])
        inside={p:m['after'][p] for p in m['added'] if protected(p)}
        self.assertEqual(inside,approved_music_parts())
        self.assertEqual(sum(s[0]=='note_block' for s in m['after'].values()),2307)

    def test_all_routes_keep_floor_and_three_air_cells(self):
        m=self.m
        for r in m['data']['routes']:
            for x,y,z in route_cells(r['points'],r['width']):
                for dy in range(4):
                    p=(x,y+dy,z);self.assertEqual(m['after'].get(p),m['before'].get(p),p)

    def test_seven_supported_fixtures_and_exact_materials(self):
        m=self.m;a=m['after'];b=m['before']
        self.assertEqual(len(m['fixtures']),7)
        self.assertEqual(Counter(a[p][0] for p in m['added']),{'lantern':7,'iron_chain':19,'chiseled_tuff_bricks':4})
        self.assertEqual(sum(s[0] in EMISSION for s in a.values()),508)
        for f in m['fixtures']:
            x,y,z=f['pos'];anchor=tuple(f['supports'][0]);self.assertEqual(a[anchor],b[anchor])
            if f['kind']=='梁下悬灯':
                self.assertEqual(a[x,y,z][1]['hanging'],'true')
                for yy in range(y+1,anchor[1]):self.assertEqual(a[x,yy,z][0],'iron_chain')
            else:
                self.assertEqual(a[x,y,z][1]['hanging'],'false')
                self.assertEqual(a[x,y-1,z][0],'chiseled_tuff_bricks')
            self.assertTrue(all(tuple(p) in a for p in f['parts']))

    def test_real_states_resolve_and_note_headroom_not_changed(self):
        m=self.m;assets=VanillaAssets()
        for p in m['added']:
            n,props,_=m['after'][p];self.assertTrue(assets.elements(n,tuple(sorted(props.items()))))
        for (x,y,z),s in m['before'].items():
            if s[0]=='note_block':
                p=(x,y+1,z);self.assertEqual(m['after'].get(p),m['before'].get(p),p)

    def test_previous_zero_samples_reach_five_without_any_dimmer_route(self):
        report,_=pathlight_audit()
        self.assertEqual(report['dimmerSamples'],[])
        self.assertEqual(report['after']['zero'],0)
        self.assertEqual(len(report['formerZeros']),28)
        self.assertTrue(all(d['after']>=5 for d in report['formerZeros']))
        self.assertEqual(report['after']['samples'],6331)


if __name__=='__main__':unittest.main()
