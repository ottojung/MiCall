"""Source-blind unique FASTA merge protects read-count attribution."""
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from Bio import SeqIO
from micall.utils.stitched_read_counts import molecule_key
from micall.utils.unique_contigs import concatenate_unique_contigs


def merge(native, g2p):
    with TemporaryDirectory() as tmp:
        paths = [Path(tmp) / "native.fa", Path(tmp) / "g2p.fa"]
        output = Path(tmp) / "combined.fa"
        for path, text in zip(paths, (native, g2p)):
            path.write_text(text)
        concatenate_unique_contigs(paths, output)
        fasta = output.read_text()
        records = list(SeqIO.parse(StringIO(fasta), "fasta"))
        return fasta, [(r.id, str(r.seq)) for r in records]


def test_no_source_contigs_writes_empty_fasta():
    assert merge("", "") == ("", [])


def test_all_unique_retain_order_and_headers():
    _, items = merge(">native allele\nAACGT\n>minority\nGCCCC\n",
                     ">g2p third\nTATAT\n")
    assert items == [("native", "AACGT"), ("minority", "GCCCC"),
                     ("g2p", "TATAT")]


def test_duplicate_native_and_g2p_copy_keeps_native_only():
    _, items = merge(">native\nAACGT\n>other\nGGGGCC\n",
                     ">g2p\nAACGT\n>alt\nTTTTGC\n")
    assert items == [("native", "AACGT"), ("other", "GGGGCC"),
                     ("alt", "TTTTGC")]


def test_opposite_strand_copy_does_not_double_count():
    _, items = merge(">native\nAAACTG\n",
                     ">g2p\nCAGTTT\n")
    assert items == [("native", "AAACTG")]
    assert molecule_key("AAACTG") == molecule_key("CAGTTT")


def test_lowercase_multiline_and_repeated_native_copies():
    _, items = merge(">first\naaac\ntg\n>repeat\nAAACTG\n",
                     ">g2p\nCAGTTT\n>distinct\nAGGGCC\n")
    assert items == [("first", "aaactg"), ("distinct", "AGGGCC")]


def test_distinct_minority_never_suppressed():
    _, items = merge(">major\nAATCTG\n>minor\nAATCCG\n",
                     ">g2p\nCAGATT\n")
    assert items == [("major", "AATCTG"), ("minor", "AATCCG")]


def test_distinct_sequences_may_share_header_without_being_removed():
    _, items = merge(">x same name\nAATCTG\n",
                     ">x same name\nAATCCG\n")
    assert items == [("x", "AATCTG"), ("x", "AATCCG")]


def test_no_duplicates_preserves_original_bytes_including_wrapping():
    left = ">first extra words\naaac\ntg\n>minority\nTTTGC\n"
    right = ">third retained\nGGA\nCAT\n"
    fasta, _ = merge(left, right)
    assert fasta == left + right


def test_empty_native_and_single_g2p_are_byte_identical():
    right = ">G2P named 1\nAACGT\n"
    fasta, _ = merge("", right)
    assert fasta == right
