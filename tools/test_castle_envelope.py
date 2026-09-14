import unittest
from castle_envelope import expand_envelope
from castle_detail import read_model,ROOT
from castle_front import route_cells
from castle_sample import validate_route


class EnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.model=expand_envelope()

    def test_immutable_music_v4_and_previous_units(self):
        m=self.model;before=m['before'];after=m['after']
        for p in m['v4_changes']:self.assertEqual(after.get(p),before.get(p),p)
        _,old=read_model(ROOT/'castle_v3'/'gate_west_combined'/'combined.json')
        for p,s in old.items():self.assertEqual(after[p],s,p)
        music={p:s for p,s in before.items() if s[2]=='control' or s[2].isdigit()}
        self.assertEqual(len(music),32260)
        for p,s in music.items():self.assertEqual(after[p],s,p)
        for p in set(before)|set(after):
            x,y,z=p
            if -8<=x<=50 and -35<=y<=45 and -37<=z<=38:self.assertEqual(after.get(p),before.get(p),p)

    def test_routes_and_eaves(self):
        m=self.model
        for r in m['data']['routes']:
            ps=list(map(tuple,r['points']))
            self.assertEqual(validate_route(m['after'],ps),[],r['name'])
            for p in route_cells(ps,r['width']):self.assertEqual(validate_route(m['after'],[p]),[],(r['name'],p))
        self.assertIn((57,47,12),m['after'])
        self.assertTrue(any(p[1]>=90 for p in m['changes']))
        self.assertTrue(any(p[0]>=58 and p[1]>=25 for p in m['changes']))


if __name__=='__main__':unittest.main()
