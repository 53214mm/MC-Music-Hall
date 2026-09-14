import unittest
from castle_sample import validate_route, build_sample


class RouteValidationTests(unittest.TestCase):
    def test_low_slab_is_not_treated_as_full_height_floor(self):
        blocks={(0,0,0):('spruce_slab',{'type':'bottom'},'sample'),(0,1,-1):('stone_brick_stairs',{'facing':'north','half':'bottom'},'sample')}
        self.assertTrue(validate_route(blocks,[(0,0,0),(0,1,-1)]))

    def test_ladder_has_direct_lower_approach_and_upper_exit(self):
        blocks=build_sample()['blocks']
        for y in range(17,23):self.assertFalse((-45,y,2) in blocks,str((-45,y,2)))
        for y in range(23,34):
            self.assertEqual(blocks[-46,y,2][0],'ladder')
            self.assertEqual(blocks[-47,y,2][0],'spruce_planks')
        self.assertIn((-45,32,2),blocks)
        self.assertEqual(validate_route(blocks,[(-45,32,2)]),[])

    def test_detects_missing_support_and_blocked_headroom(self):
        route=[(0,0,0),(1,0,0)]
        floor={(0,0,0):('stone_bricks',{},'sample'),(1,0,0):('stone_bricks',{},'sample')}
        self.assertEqual(validate_route(floor,route),[])
        self.assertTrue(validate_route({(0,0,0):floor[(0,0,0)]},route))
        blocked=dict(floor);blocked[(1,3,0)]=('stone_bricks',{},'sample')
        self.assertTrue(validate_route(blocked,route))

    def test_rejects_gap_and_wrong_stair_but_accepts_reverse_walk(self):
        route=[(0,0,0),(0,1,-1),(0,2,-2),(0,2,-3)]
        blocks={p:('stone_bricks',{},'sample') for p in route}
        stair=('stone_brick_stairs',{'facing':'north','half':'bottom','shape':'straight','waterlogged':'false'},'sample')
        blocks[(0,1,-1)]=stair;blocks[(0,2,-2)]=stair
        self.assertEqual(validate_route(blocks,route),[])
        self.assertEqual(validate_route(blocks,route[::-1]),[])
        wrong=dict(blocks);wrong[(0,1,-1)]=(stair[0],dict(stair[1],facing='south'),'sample')
        self.assertTrue(validate_route(wrong,route))
        self.assertTrue(validate_route(blocks,[route[0],route[2]]))

    def test_sample_routes_preserve_three_block_headroom_and_music_clearance(self):
        sample=build_sample()
        self.assertGreater(len(sample['routes']),5)
        for route in sample['routes']:
            self.assertEqual(validate_route(sample['blocks'],route['points']),[],route['name'])
        for x,y,z in sample['blocks']:
            self.assertFalse(-7<=x<=49 and -34<=y<=45 and -36<=z<=37)
        self.assertNotIn((-28,0,42),sample['blocks'],'井口应是真洞')
        self.assertIn((-28,-12,42),sample['blocks'],'井底必须有实体地板')
        self.assertIn((-28,16,42),sample['blocks'],'同位置上方必须有实际悬桥')

    def test_all_three_lanes_and_manual_gate_are_clear(self):
        sample=build_sample();blocks=sample['blocks']
        for route in sample['routes']:
            for a,b in zip(route['points'],route['points'][1:]):
                along_x=b[0]!=a[0]
                for x,y,z in(a,b):
                    for j in(-1,0,1):
                        p=(x if along_x else x+j,y,z+j if along_x else z)
                        self.assertEqual(validate_route(blocks,[p]),[],f'{route["name"]} {p}')
        gate=sample['shortcuts'][0]
        self.assertTrue(validate_route(blocks,gate['points']))
        opened={p:s for p,s in blocks.items() if p not in gate['remove']}
        self.assertEqual(validate_route(opened,gate['points']),[])


if __name__=='__main__':unittest.main()
