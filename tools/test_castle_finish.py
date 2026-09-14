import unittest
from castle_finish import finish_castle, protected, spread_light
from castle_front import route_cells
from castle_sample import validate_route


class LightTests(unittest.TestCase):
    def test_light_drops_and_opaque_wall_blocks(self):
        # A conservative air-only model, not Minecraft's partial-shape engine.
        bs={(1,y,z):('stone_bricks',{},'shell') for y in range(-16,17) for z in range(-16,17)}
        light=spread_light(bs,{(0,0,0):15})
        self.assertEqual(light[-1,0,0],14)
        self.assertEqual(light.get((2,0,0),0),0)
        self.assertNotIn((-15,0,0),light)

    def test_light_uses_the_brighter_overlapping_source(self):
        field=spread_light({}, {(0,0,0):10,(4,0,0):15})
        self.assertEqual(field[1,0,0],12)
        self.assertEqual(field[4,1,0],14)


class FinishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=finish_castle()

    def test_materials_preserve_music_volume_and_geometry(self):
        m=self.m;a=m['after'];b=m['before']
        self.assertTrue(set(b)<=set(a))
        for p,s in b.items():
            if p in m['frozen'] or protected(p):self.assertEqual(s,a[p],p)
            elif s[0].endswith(('_stairs','_slab','_wall')):self.assertEqual(s[1],a[p][1],p)
        for p,s in a.items():
            if p in m['frozen'] or protected(p):self.assertEqual(b.get(p),s,p)
        self.assertEqual(sum(s[0]=='note_block' for s in a.values()),2307)
        self.assertGreater(len(m['changed']),10000)
        self.assertGreater(len({a[p][0] for p in m['changed']}),8)

    def test_routes_and_supported_lights(self):
        m=self.m
        for r in m['data']['routes']:
            ps=list(map(tuple,r['points']))
            self.assertEqual(validate_route(m['after'],ps),[],r['name'])
            for p in route_cells(ps,r['width']):self.assertEqual(validate_route(m['after'],[p]),[],(r['name'],p))
        self.assertGreater(len(m['fixtures']),180)
        for f in m['fixtures']:
            self.assertTrue(all(tuple(p) in m['after'] for p in f['supports']),f)
            self.assertIn(tuple(f['pos']),m['after'])
        self.assertTrue({'路边灯座','悬灯','立面灯龛','吊灯'}<={f['kind'] for f in m['fixtures']})


if __name__=='__main__':unittest.main()
