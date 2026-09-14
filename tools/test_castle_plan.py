import heapq
import unittest
from castle_plan import plan


def distance(p,a,b,shortcuts=False):
    graph={n['id']:[] for n in p['nodes']}
    for e in p['edges']:
        if e['kind']=='shortcut' and not shortcuts:continue
        graph[e['a']].append((e['b'],e['length']));graph[e['b']].append((e['a'],e['length']))
    heap=[(0,a)];seen=set()
    while heap:
        d,n=heapq.heappop(heap)
        if n==b:return d
        if n in seen:continue
        seen.add(n)
        for other,length in graph[n]:heapq.heappush(heap,(d+length,other))
    return float('inf')


class CastlePlanTests(unittest.TestCase):
    def test_main_route_connected_without_shortcuts(self):
        p=plan()
        for node in p['mainRoute']:
            self.assertLess(distance(p,'approach',node),float('inf'))
        self.assertEqual(p['mainRoute'][-1],'listening')

    def test_dead_ends_have_one_connection_and_story(self):
        p=plan()
        for n in p['nodes']:
            if n['role']!='死路':continue
            self.assertEqual(sum(n['id'] in [e['a'],e['b']] for e in p['edges']),1)
            self.assertGreater(len(n['story']),12)

    def test_shortcuts_actually_reduce_graph_length(self):
        p=plan()
        for a,b in [('bailey','cloister'),('archive','archive_upper'),('eastcourt','service')]:
            self.assertLess(distance(p,a,b,True),distance(p,a,b,False))

    def test_nodes_and_edges_are_unique_and_reference_existing_rooms(self):
        p=plan();ids={n['id'] for n in p['nodes']}
        self.assertEqual(len(ids),len(p['nodes']))
        self.assertEqual(len({tuple(sorted([e['a'],e['b']])) for e in p['edges']}),len(p['edges']))
        for e in p['edges']:
            self.assertIn(e['a'],ids);self.assertIn(e['b'],ids)
            self.assertGreater(e['length'],0)


if __name__=='__main__':unittest.main()
