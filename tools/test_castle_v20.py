import unittest
from castle_v20 import model_v20,REGIONS
from castle_interior import support_errors
from castle_sample import validate_route
from castle_finish import protected
from vanilla_mesh import VanillaAssets

class SidewallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=model_v20()
    def test_protected_old_model_and_bounds(self):
        m=self.m
        self.assertGreater(len(m['changed']),200)
        for p in m['frozen']:self.assertEqual(m['before'].get(p),m['after'].get(p),p)
        for p in m['changed']:
            self.assertFalse(protected(p));self.assertTrue(any(all(r[2*i]<=p[i]<=r[2*i+1] for i in range(3)) for r in REGIONS.values()),p)
    def test_projections_and_original_wall_retained(self):
        a=self.m['after'];b=self.m['before']
        for z in(-43,-29,-15,0,17,31,45,59):self.assertIn((88,2,z),a)
        for z in(32,47,62):self.assertEqual(a[76,22,z][0],'gray_stained_glass_pane');self.assertEqual(a[75,22,z],b[75,22,z])
        self.assertEqual(support_errors(a,self.m['features']),[])
    def test_routes_music_and_real_states(self):
        m=self.m;assets=VanillaAssets()
        for r in m['data']['routes']:self.assertEqual(validate_route(m['after'],r['points']),[])
        for p,s in m['before'].items():
            if s[2].isdigit() or s[2]=='control':self.assertEqual(m['after'][p],s)
        for n,pr in {(m['after'][p][0],tuple(sorted(m['after'][p][1].items()))) for p in m['changed'] if p in m['after']}:assets.elements(n,pr)
    def test_new_window_auto_connections(self):
        a=self.m['after']
        self.assertEqual(a[76,22,32][1]['west'],'true');self.assertEqual(a[76,22,32][1]['east'],'true')
        self.assertEqual(a[77,22,32][1]['west'],'tall');self.assertEqual(a[77,22,32][1]['north'],'none')
        self.assertEqual(a[77,27,32][1]['north'],'tall');self.assertEqual(a[77,19,29][1]['south'],'low')

if __name__=='__main__':unittest.main()
