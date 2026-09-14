import unittest
from castle_front import grid_route, route_cells, build_front, combined_model
from castle_sample import validate_route,build_sample


class FrontTests(unittest.TestCase):
    def test_grid_routes_reject_teleports_and_expand_width(self):
        self.assertEqual(grid_route([(0,0,0),(0,2,-2)]),[(0,0,0),(0,1,-1),(0,2,-2)])
        with self.assertRaises(ValueError):grid_route([(0,0,0),(2,1,-1)])
        cells=route_cells([(0,0,0),(0,0,1)],5)
        self.assertIn((2,0,0),cells);self.assertIn((-2,0,1),cells)
        self.assertEqual(len(cells),10)

    def test_front_paths_and_west_join_preserve_existing_blocks(self):
        old=build_sample();whole=combined_model()
        self.assertGreaterEqual(len(whole['routes']),14)
        for p,state in old['blocks'].items():self.assertEqual(whole['blocks'].get(p),state,str(p))
        for r in whole['routes']:
            self.assertEqual(validate_route(whole['blocks'],r['points']),[],r['name'])
            for p in route_cells(r['points'],r['width']):
                self.assertEqual(validate_route(whole['blocks'],[p]),[],f'{r["name"]} {p}')
        self.assertEqual(whole['routes'][0]['points'][-1],(-43,-12,102))
        self.assertEqual(whole['routes'][1]['points'][-1],(-38,0,74))
        self.assertFalse((-43,-32,132) in whole['blocks'],'拱桥下的裂隙不能被岩体填死')
        self.assertTrue((-43,-12,132) in whole['blocks'],'裂隙上必须有真实桥面')


if __name__=='__main__':unittest.main()
