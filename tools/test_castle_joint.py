import unittest
from collections import deque
from castle_joint import joint_castle
from castle_finish import EMISSION, protected
from castle_front import route_cells
from castle_sample import validate_route
from vanilla_mesh import VanillaAssets
from castle_joint_lighting import lighting_audit


class JointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=joint_castle()

    def test_music_terrain_sources_and_frozen_cells_unchanged(self):
        m=self.m;a=m['after'];b=m['before']
        for p in set(a)|set(b):
            if p in m['frozen'] or protected(p) or b.get(p,('',{},''))[2] not in ('','shell'):
                self.assertEqual(a.get(p),b.get(p),p)
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)
        for p,s in b.items():
            if s[0] in EMISSION:self.assertEqual(a[p],s)

    def test_routes_keep_every_floor_and_three_clearance_cells(self):
        m=self.m
        for r in m['data']['routes']:
            for x,y,z in route_cells(r['points'],r['width']):
                for dy in range(4):
                    p=(x,y+dy,z);self.assertEqual(m['after'].get(p),m['before'].get(p),(r['name'],p))
                self.assertEqual(validate_route(m['after'],[(x,y,z)]),[],(r['name'],x,y,z))

    def test_both_deferred_bays_actually_change_and_other_old_solids_stay(self):
        m=self.m;regions=m['bayRegions']
        def inside(p,r):return all(r[i*2]<=p[i]<=r[i*2+1] for i in range(3))
        self.assertEqual(len(m['resolved']),2)
        for r in regions:self.assertGreater(sum(inside(p,r) for p in m['changed']),40)
        for p,s in m['before'].items():
            if not any(inside(p,r) for r in regions):self.assertEqual(s,m['after'].get(p),p)
        for f in m['features'][:2]:
            for p in f['opening']:
                p=tuple(p);self.assertEqual(m['after'].get(p),m['before'].get(p),p)

    def test_platform_layers_and_existing_rails_stay(self):
        m=self.m
        for p in m['platformPreserved']:
            self.assertEqual(m['after'].get(p),m['before'].get(p),p)
        self.assertEqual(m['after'][-55,66,-31],m['before'][-55,66,-31])
        self.assertEqual(m['after'][66,56,14],m['before'][66,56,14])
        service=m['features'][1]
        self.assertLessEqual(max(p[1] for p in service['newArch']),53)
        fire=m['features'][0]
        self.assertLessEqual(max(p[1] for p in fire['newArch']),75)
        # The route cuts below this old mullion: do not leave a dangling rod.
        for y in (68,69,70):self.assertIsNone(m['after'].get((-51,y,-33)))

    def test_thirty_real_hanging_lights_have_unbroken_supports(self):
        m=self.m;a=m['after'];b=m['before']
        self.assertEqual(len(m['fixtures']),30)
        self.assertEqual(sum(s[0] in EMISSION for s in a.values()),501)
        for f in m['fixtures']:
            p=tuple(f['pos']);self.assertNotIn(p,b);self.assertEqual(a[p][0],'lantern')
            self.assertEqual(a[p][1]['hanging'],'true')
            x,y,z=p;self.assertEqual(a[x,y+1,z][0],'iron_chain')
            self.assertIn((x,y+2,z),a)
            self.assertTrue(all(tuple(p) in a for p in f['supports']))
            parts=set(map(tuple,f['parts']));reachable=set(map(tuple,f['supports']));q=deque(reachable)
            while q:
                p=q.popleft()
                for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                    n=tuple(p[i]+d[i] for i in range(3))
                    if n in parts and n not in reachable:reachable.add(n);q.append(n)
            self.assertFalse(parts-reachable,f['name'])

    def test_new_lights_do_not_add_redstone_and_states_resolve(self):
        m=self.m;assets=VanillaAssets();states=set()
        for p in m['changed']:
            s=m['after'].get(p)
            if s:states.add((s[0],tuple(sorted(s[1].items()))))
        self.assertTrue(any(n.endswith('_wall') for n,_ in states))
        self.assertTrue(any(n.endswith('_stairs') for n,_ in states))
        for n,props in states:
            self.assertNotIn(n,{'redstone_wire','repeater','redstone_lamp','note_block'})
            self.assertTrue(assets.elements(n,props),(n,props))

    def test_niche_light_reaches_front_air_without_dimming_routes(self):
        report,fields=lighting_audit()
        self.assertEqual(report['dimmerSamples'],[])
        self.assertEqual(report['before']['samples'],report['after']['samples'])
        self.assertEqual(len(report['routes']),35)
        for f in self.m['fixtures']:
            if f['kind']!='拱龛顶挂灯':continue
            x,y,z=f['pos']
            q=(x-1,y,z) if f['name'].startswith('西') else (x+1,y,z) if f['name'].startswith('东') else (x,y,z-1)
            self.assertNotIn(q,self.m['after'])
            self.assertGreater(fields['after'].get(q,0),fields['before'].get(q,0),f['name'])
            self.assertEqual(fields['after'][q],14)


if __name__=='__main__':unittest.main()
