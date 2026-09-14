"""Contracts for immutable music relocation and full-castle circulation."""
import unittest
from castle_complete import relocate_music, shift, translate_connections, complete_model, check_source_entities
from castle_front import route_cells
from castle_sample import validate_route


class FullCastleTests(unittest.TestCase):
    def test_required_block_entities_are_not_silently_dropped(self):
        check_source_entities({'palette':[{'Name':'minecraft:oak_wall_sign'}],'blocks':[{'state':0,'nbt':{'Text1':'credit'}}],'entities':[]})
        with self.assertRaises(ValueError):check_source_entities({'palette':[{'Name':'minecraft:barrel'}],'blocks':[{'state':0,'nbt':{'Items':[]}}],'entities':[]})
        with self.assertRaises(ValueError):check_source_entities({'palette':[],'blocks':[],'entities':[{'pos':[1,2,3]}]})

    def test_translation_preserves_states_and_only_coordinate_fields(self):
        source={(1,2,3):('repeater',{'facing':'north','delay':'4'},'control')}
        self.assertEqual(relocate_music(source),{(1,-30,3):source[1,2,3]})
        report={'connections':[{'from':1,'timerSettings':[1,2,3],'timerPositions':[[1,2,3]],'tapPosition':[3,4,5],'nextRelayPosition':[5,6,7],'totalTicks':320}], 'paths':[{'name':'01_timer_input','positions':[[1,2,3]]}]}
        result=translate_connections(report)
        self.assertEqual(result['connections'][0]['timerSettings'],[1,2,3])
        self.assertEqual(result['connections'][0]['timerPositions'],[[1,-30,3]])
        self.assertEqual(result['paths'][0]['positions'],[[1,-30,3]])
        self.assertEqual(report['paths'][0]['positions'],[[1,2,3]])

    def test_full_invariants(self):
        m=complete_model();blocks=m['blocks']
        self.assertEqual(sum(v[0]=='note_block' for v in blocks.values()),2307)
        for p,v in m['originalMusic'].items():
            self.assertEqual(blocks[shift(p)],v)
            if v[0]=='note_block':self.assertNotIn(shift((p[0],p[1]+1,p[2])),blocks)
        for p,v in m['previousBlocks'].items():self.assertEqual(blocks[p],v)
        self.assertEqual(blocks[23,-23,-3][0],'stone_button')
        for y in range(-32,41):
            self.assertEqual(blocks.get((46,y,1),('missing',))[0],'ladder',y)
            self.assertEqual(blocks[46,y,1][1]['facing'],'west')
            self.assertIn((47,y,1),blocks)
        self.assertEqual(m['signal']['musicZeroTicks'],{i:7+320*(i-1) for i in range(1,12)})
        for r in m['routes']:
            self.assertEqual(validate_route(blocks,r['points']),[],r['name'])
            for p in route_cells(r['points'],r['width']):self.assertEqual(validate_route(blocks,[p]),[],(r['name'],p))
        self.assertTrue(any(r['points'][-1]==(21,-3,4) for r in m['routes']))


if __name__=='__main__':unittest.main()
