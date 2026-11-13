"""Validated paired FASTQ preprocessing for single-input assembler CLIs."""
import gzip
from pathlib import Path


def _reader(path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path, encoding="utf-8")


def _record(source):
    header = source.readline()
    if not header:
        return None
    seq, plus, quality = (source.readline() for _ in range(3))
    if (not header.startswith("@") or not plus.startswith("+")
            or not seq or not quality or len(seq.rstrip("\r\n"))
            != len(quality.rstrip("\r\n"))):
        raise ValueError("invalid or truncated paired FASTQ")
    return (header, seq, plus, quality)


def interleave_pairs(left: Path, right: Path, dest: Path):
    """Interleave both mates; refuse truncation instead of silently dropping."""
    with _reader(left) as first, _reader(right) as second, dest.open("x") as out:
        while True:
            mate1, mate2 = _record(first), _record(second)
            if mate1 is None and mate2 is None:
                return
            if mate1 is None or mate2 is None:
                raise ValueError("unequal FASTQ mate counts")
            out.writelines(mate1)
            out.writelines(mate2)
