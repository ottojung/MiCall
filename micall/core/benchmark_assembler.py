"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import gzip
import subprocess
from micall.utils.work_dir import WorkDir


ASSEMBLER = "/usr/local/bin/minia"
BOTH_MATES = "both_mates.fastq"
CONTIGS_FASTA = "minia.contigs.fa"


def _reader(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt")
    return path.open(encoding="utf-8")


def _record(source):
    header = source.readline()
    if not header:
        return None
    seq, plus, quality = (source.readline() for _ in range(3))
    if (not header.startswith("@") or not plus.startswith("+")
            or not seq or not quality
            or len(seq.rstrip("\r\n")) != len(quality.rstrip("\r\n"))):
        raise ValueError("invalid or truncated paired FASTQ")
    return header, seq, plus, quality


def interleave_pairs(left: Path, right: Path, dest: Path) -> None:
    """Interleave both source mates in original order; refuse truncation."""
    with _reader(left) as first, _reader(right) as second, dest.open("x") as out:
        while True:
            mate1, mate2 = _record(first), _record(second)
            if mate1 is None and mate2 is None:
                return
            if mate1 is None or mate2 is None:
                raise ValueError("unequal FASTQ mate counts")
            out.writelines(mate1)
            out.writelines(mate2)


def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run the pinned minia CLI on both original paired reads.

    ``seeds`` is accepted only for the common denovo bridge signature: minia
    has no seed, reference, truth or evaluator argument, and none is passed.
    The two mates are interleaved losslessly because minia consumes one FASTQ.
    """
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    reads = work / BOTH_MATES
    interleave_pairs(first, second, reads)
    output = work / CONTIGS_FASTA
    argv = [ASSEMBLER, "-in", str(reads), "-kmer-size", "31",
            "-abundance-min", "3", "-out", str(work / "minia")]
    with (work / "assembler.log").open("wb") as log:
        subprocess.run(argv, check=True, cwd=work, env=None,
                       stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("minia completed without the expected FASTA")
    return output
