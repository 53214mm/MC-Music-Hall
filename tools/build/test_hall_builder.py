import tempfile
import unittest
from pathlib import Path

from build_music_hall import rotate_properties, transform, encode_structure, make_shell, read_nbt


class HallTests(unittest.TestCase):
    def test_rotation_turns_facing_and_wire_connections(self):
        self.assertEqual(rotate_properties({'facing':'north', 'east':'up', 'west':'side', 'note':'12'}),
                         {'facing':'south', 'west':'up', 'east':'side', 'note':'12'})

    def test_snake_positions(self):
        self.assertEqual(transform(1, (19,9,1)), (23,9,-2))
        self.assertEqual(transform(2, (19,9,1)), (19,9,9))
        self.assertEqual(transform(3, (19,9,1)), (19,21,9))
        self.assertEqual(transform(11, (19,6,1)), (19,66,9))

    def test_nbt_roundtrip(self):
        blob = encode_structure({(42,0,0):('note_block',{'note':'12','instrument':'harp','powered':'false'},'01')}, 1519)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'roundtrip.nbt'
            path.write_bytes(blob)
            data = read_nbt(path)
        self.assertEqual(data['size'], [43,1,1])
        self.assertEqual(data['blocks'][0]['pos'], [42,0,0])
        self.assertEqual(data['palette'][0]['Properties']['note'], '12')

    def test_shell_leaves_module_envelopes_clear(self):
        shell = make_shell()
        sizes = [(43,10,20),(43,10,23),(43,10,23),(43,10,26),(43,10,26),(43,10,26),(43,10,20),(43,10,32),(43,10,26),(43,10,17),(43,7,8)]
        for i,(sx,sy,sz) in enumerate(sizes,1):
            for x in range(sx):
                for y in range(sy+1):
                    for z in range(sz):
                        self.assertNotIn(transform(i,(x,y,z)),shell)

    def test_all_modules_receive_correct_timing(self):
        from build_music_hall import load_modules,is_north
        from hall_connections import generate_connections,verify_rising_signal
        modules,_=load_modules()
        control,report=generate_connections(modules,transform,is_north)
        actual=verify_rising_signal(modules,control,transform)
        self.assertEqual(len(report['connections']),10)
        self.assertEqual(actual['musicZeroTicks'],{i:7+320*(i-1) for i in range(1,12)})


if __name__ == '__main__': unittest.main()
