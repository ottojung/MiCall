"""Mixed-reference pair assignment respects numeric SAM mapping qualities."""
import unittest
from io import StringIO

from micall.core.remap import MixedReferenceSplitter


class InMemorySplit(MixedReferenceSplitter):
    def create_split_file(self, refname, direction):
        return StringIO()

    def close_split_file(self, split_file):
        pass


class NumericMappingQualityTests(unittest.TestCase):
    def check_pair(self, a, b, expected):
        line = ('@SQ\tSN:RX\n'
                f'pair\t99\tRX\t1\t{a}\t3M\tRY\t1\t3\tACG\tJJJ\tAS:i:200\n'
                f'pair\t147\tRY\t1\t{b}\t3M\tRX\t1\t-3\tACC\tJJK\tAS:i:100\n')
        splitter = InMemorySplit('')
        self.assertEqual(list(splitter.split(StringIO(line))), [])
        self.assertEqual(list(splitter.splits), [expected])
        first, second = splitter.splits[expected]
        self.assertIn('@pair', first.getvalue())
        self.assertIn('@pair', second.getvalue())

    def test_crossing_decimal_width_respects_higher_mapq(self):
        self.check_pair(9, 10, 'RY')
        self.check_pair(10, 9, 'RX')
        self.check_pair(2, 30, 'RY')
        self.check_pair(30, 2, 'RX')

    def test_equal_mapq_defers_to_alignment_score(self):
        self.check_pair(9, 9, 'RX')
        self.check_pair(44, 44, 'RX')


if __name__ == '__main__':
    unittest.main()
