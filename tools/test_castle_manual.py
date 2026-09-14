import unittest
from castle_manual import phase_for,make_pages,manual_plan

class ManualTests(unittest.TestCase):
    def test_priority_and_fragile_parts(self):
        gate={(55,3,32)}
        self.assertEqual(phase_for((55,3,32),('chiseled_sandstone',{},'shell'),gate),5)
        self.assertEqual(phase_for((0,40,0),('note_block',{},'01'),gate),2)
        self.assertEqual(phase_for((0,-5,0),('tuff_bricks',{},'terrain'),gate),0)
        self.assertEqual(phase_for((0,20,0),('lantern',{},'shell'),gate),4)
        self.assertEqual(phase_for((0,25,0),('iron_chain',{},'shell'),gate),1)
        self.assertEqual(phase_for((0,55,0),('deepslate_tiles',{},'shell'),gate),3)
    def test_pages_cover_every_cell_once_and_order(self):
        rows=[[0,0,0,0],[17,0,0,1],[0,1,0,0],[0,0,17,2]];phases=[1,0,1,2]
        pages=make_pages(rows,phases,[0,0,0])
        self.assertEqual(sum(p['count'] for p in pages),4)
        self.assertEqual([(p['phase'],p['y'],p['tz'],p['tx']) for p in pages],[(0,0,0,1),(1,0,0,0),(1,1,0,0),(2,0,1,0)])
        self.assertEqual(len({p['id'] for p in pages}),4)
    def test_empty_and_reference_are_not_build_actions(self):
        self.assertEqual(make_pages([],[],[90,48,84]),[])
        self.assertRaises(ValueError,make_pages,[[0,0,0,0]],[],[0,0,0])

    def test_support_pass_precedes_attachment_across_tile_edge(self):
        pages=make_pages([[15,0,0,0],[16,0,0,1]],[2,2],[0,0,0],[1,0])
        self.assertEqual([(p['sub'],p['tx']) for p in pages],[(0,1),(1,0)])
        self.assertEqual(phase_for((0,5,0),('grindstone',{'face':'ceiling'},'shell'),set()),4)

if __name__=='__main__':unittest.main()
