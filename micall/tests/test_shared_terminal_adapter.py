"""Source-only general paired-mate suffix inference; no reference sequences."""
from pathlib import Path
import random
import tempfile
import unittest

from micall.core.terminal_adapter import shared_terminal_adapter


SUFFIX = "AGATCGGAAGAGCACACG"


def write_fastqs(folder, sequences):
    files = [folder / "R1.fastq", folder / "R2.fastq"]
    for mate, path in enumerate(files):
        with path.open("x") as stream:
            for i, pair in enumerate(sequences):
                seq = pair[mate]
                stream.write(f"@pair:{i} {mate + 1}:N:0:1\n"
                             f"{seq}\n+\n{'I'*len(seq)}\n")
    return files


def pairs(count=200, *, common=True, diverse=True):
    rng = random.Random(17)
    output = []
    for i in range(count):
        before = ["".join(rng.choices("ACGT", k=132)) for _ in range(2)]
        if not diverse:
            before = ["A"*132, "A"*132]
        tails = [SUFFIX, SUFFIX if common else "CTGTCTCTTATACACATC"]
        output.append(tuple(s+tail for s,tail in zip(before,tails)))
    return output


class PairedTerminalSuffixTests(unittest.TestCase):
    def infer(self, data):
        with tempfile.TemporaryDirectory() as temporary:
            first, second = write_fastqs(Path(temporary), data)
            return shared_terminal_adapter(first, second)

    def test_recovers_strongly_shared_technical_suffix_with_diverse_flanks(self):
        self.assertEqual(self.infer(pairs()), SUFFIX)

    def test_avoids_identical_clonal_mate_ends(self):
        self.assertIsNone(self.infer(pairs(diverse=False)))

    def test_avoids_different_mate_suffixes(self):
        self.assertIsNone(self.infer(pairs(common=False)))

    def test_avoids_small_libraries(self):
        self.assertIsNone(self.infer(pairs(count=99)))

    def test_avoids_below_ninety_percent_conservation(self):
        data = pairs()
        data = [("G"*150,"T"*150) if i%4==0 else pair
                for i,pair in enumerate(data)]
        self.assertIsNone(self.infer(data))

    def test_avoids_unpaired_read_id_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            first, second = write_fastqs(Path(temporary), pairs())
            content=second.read_text().splitlines(keepends=True)
            content[0]="@wrong 2:N:0:1\n"
            second.write_text("".join(content))
            self.assertIsNone(shared_terminal_adapter(first,second))


if __name__ == "__main__":
    unittest.main()
