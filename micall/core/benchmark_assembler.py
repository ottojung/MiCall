"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import gzip
import subprocess
from micall.utils.work_dir import WorkDir


ASSEMBLER = "/usr/local/bin/fml-asm"
BOTH_MATES = "both_mates.fastq"
UNITIG_FASTQ = "fermi-lite.unitigs.fastq"
CONTIGS_FASTA = "fermi-lite-contigs.fasta"


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


def convert_unitigs_to_fasta(unitigs: Path, contigs: Path) -> None:
    """Convert fml-asm's unitig FASTQ into exact-sequence FASTA.

    Every input record is a strict 4-line FASTQ record as emitted by
    misc.c:fml_utg_print (header, sequence, '+', coverage-as-quality). Each
    valid record becomes exactly one FASTA record with the identical sequence.
    No contig is invented, reversed or trimmed. Zero records produce a valid
    empty FASTA. Any malformed or truncated record fails closed instead of
    being silently treated as an empty assembly.
    """
    partial = contigs.with_name(contigs.name + ".partial")
    try:
        with unitigs.open("r", encoding="ascii") as source, \
                partial.open("w", encoding="ascii") as dest:
            while True:
                header = source.readline()
                if not header:
                    break  # clean EOF: zero or a whole number of records
                seq_line = source.readline()
                plus = source.readline()
                qual_line = source.readline()
                seq = seq_line.rstrip("\r\n")
                qual = qual_line.rstrip("\r\n")
                if (not header.startswith("@") or not header[1:].split()
                        or not seq_line or not seq or not plus.startswith("+")
                        or not qual_line or len(seq) != len(qual)):
                    raise ValueError("invalid or truncated fml-asm unitig FASTQ")
                name = header[1:].split()[0]
                dest.write(">" + name + "\n" + seq + "\n")
        partial.replace(contigs)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run fml-asm with fixed CLI options and the current paired reads.

    ``seeds`` is accepted only for the common denovo bridge signature:
    fml-asm has no seed, reference, truth or evaluator argument.
    """
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / CONTIGS_FASTA
    # fml-asm consumes a single FASTQ, so interleave both source-attested
    # mates in original order before invoking the fixed command.
    interleave_pairs(first, second, work / BOTH_MATES)
    unitigs = work / UNITIG_FASTQ
    argv = [ASSEMBLER, str(work / BOTH_MATES)]
    with unitigs.open("wb") as captured, (work / "assembler.log").open("wb") as log:
        subprocess.run(argv, check=True, cwd=work, env=None,
                       stdout=captured, stderr=log)
    convert_unitigs_to_fasta(unitigs, output)
    if not output.is_file():
        raise RuntimeError("fermi-lite completed without the expected FASTA")
    return output
