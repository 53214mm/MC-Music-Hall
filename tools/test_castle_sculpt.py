import unittest
from collections import Counter,deque
from castle_sculpt import sculpt_castle
from castle_finish import protected,EMISSION
from castle_front import route_cells
from castle_sample import validate_route
from vanilla_mesh import VanillaAssets

DIRS=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))


class SculptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=sculpt_castle()

    def test_music_ground_existing_samples_and_fixtures_are_frozen(self):
        m=self.m;a=m['after'];b=m['before']
        for p in set(a)|set(b):
            if protected(p) or p in m['frozen'] or b.get(p,('',{},''))[2] not in ('shell',''):
                self.assertEqual(a.get(p),b.get(p),p)
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)
        self.assertEqual({p:s for p,s in a.items() if s[0] in EMISSION},{p:s for p,s in b.items() if s[0] in EMISSION})

    def test_all_routes_have_original_support_state_and_clearance(self):
        m=self.m
        for r in m['data']['routes']:
            self.assertEqual(validate_route(m['after'],list(map(tuple,r['points']))),[],r['name'])
            for p in route_cells(r['points'],r['width']):
                self.assertEqual(m['before'].get(p),m['after'].get(p),p)
                self.assertEqual(validate_route(m['after'],[p]),[],(r['name'],p))

    def test_multiple_facades_and_non_cubic_members_actually_change(self):
        m=self.m;c=Counter(f['family'] for f in m['features'])
        self.assertGreaterEqual(c['curtain'],20)
        self.assertGreaterEqual(c['window'],12)
        self.assertEqual(c['eave'],2);self.assertEqual(c['verge'],2)
        self.assertGreater(len(m['changed']),2000)
        states=[m['after'][p] for p in m['changed'] if p in m['after']]
        partial=[s for s in states if s[0].endswith(('_stairs','_slab','_wall','_fence','_trapdoor'))]
        self.assertGreater(len(partial)/len(states),.30)
        self.assertTrue(any(s[0]=='spruce_trapdoor' for s in states))
        assets=VanillaAssets()
        for name,props in {(s[0],tuple(sorted(s[1].items()))) for s in states}:self.assertTrue(assets.elements(name,props),(name,props))

    def test_blind_recesses_keep_two_backing_courses(self):
        m=self.m
        for f in m['features']:
            if f['family']!='curtain':continue
            self.assertGreater(len(f['recess']),5)
            for p,back1,back2 in f['recess']:
                self.assertNotIn(tuple(p),m['after'],(f['name'],p))
                for q in (back1,back2):self.assertEqual(m['after'].get(tuple(q)),m['before'].get(tuple(q)),(f['name'],q))
                self.assertIn(tuple(back1),m['after']);self.assertIn(tuple(back2),m['after'])

    def test_existing_window_air_and_glass_are_not_blocked(self):
        m=self.m
        for f in m['features']:
            for p in f.get('opening',[]):
                p=tuple(p);self.assertEqual(m['after'].get(p),m['before'].get(p),(f['name'],p))

    def test_shared_lamp_anchor_returns_to_wall_and_two_route_bays_are_unchanged(self):
        m=self.m;a=m['after'];b=m['before']
        self.assertEqual(a[-22,61,-35],b[-22,61,-35])
        self.assertEqual(a[-22,61,-36][0],'cut_sandstone')
        self.assertIn((-22,61,-37),a)
        self.assertEqual({f['name'] for f in m['deferred']},{'烽塔南向上层窗廊','维修塔南向上层窗廊'})
        for f in m['deferred']:
            r=f['region']
            for x in range(r[0],r[1]+1):
                for y in range(r[2],r[3]+1):
                    for z in range(r[4],r[5]+1):self.assertEqual(a.get((x,y,z)),b.get((x,y,z)),(f['name'],x,y,z))

    def test_long_eave_closes_only_the_scoped_wall_to_roof_gap(self):
        a=self.m['after'];b=self.m['before']
        for x,z0 in ((75,21),(59,25)):
            for z in range(z0,70):
                for y in range(30,34):self.assertIn((x,y,z),a)
                self.assertEqual(a[x,34,z],b[x,34,z])
        for z in range(21,25):self.assertEqual(a.get((59,30,z)),b.get((59,30,z)))

    def test_added_members_form_grid_connected_groups_attached_to_old_structure(self):
        m=self.m;a=m['after'];b=m['before'];added=set(a)-set(b)
        reached=set();queue=deque()
        for p in added:
            if any(tuple(p[i]+d[i] for i in range(3)) in a and tuple(p[i]+d[i] for i in range(3)) not in added for d in DIRS):
                reached.add(p);queue.append(p)
        while queue:
            p=queue.popleft()
            for d in DIRS:
                q=tuple(p[i]+d[i] for i in range(3))
                if q in added and q not in reached:reached.add(q);queue.append(q)
        self.assertEqual(added-reached,set())
        for f in m['features']:
            self.assertGreater(f['changed'],0)
            self.assertTrue(all(tuple(p) in a for p in f['anchors']),f['name'])


if __name__=='__main__':unittest.main()
