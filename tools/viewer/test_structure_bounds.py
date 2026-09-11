import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nbt_structure_to_json import structure_payload


class BoundsTests(unittest.TestCase):
    def test_exporter_size_does_not_hide_blocks(self):
        root = {'size': [32, 10, 20], 'palette': [{'Name': 'minecraft:note_block'}],
                'blocks': [{'state': 0, 'pos': [42, 1, 19]}]}
        with patch('nbt_structure_to_json.read_nbt', return_value=root):
            result = structure_payload(Path('example.nbt'))
        self.assertEqual(result['size'], [43, 10, 20])
        self.assertEqual(result['declaredSize'], [32, 10, 20])


if __name__ == '__main__':
    unittest.main()
