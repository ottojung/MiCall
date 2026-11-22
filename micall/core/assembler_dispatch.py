"""Execute external de novo assemblers through MiCall's normal downstream path."""
from pathlib import Path
from shutil import rmtree
import subprocess
from tempfile import mkdtemp

from micall.core.assembler_commands import (
    BOTH_MATES,
    command_steps,
    fermi_lite_unitig_fastq,
)
from micall.core.assembler_inputs import interleave_pairs
from micall.utils.work_dir import WorkDir


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


def run_external_assembler(name: str, first: Path, second: Path) -> Path:
    """Run a fixed command, rejecting unsuccessful or missing FASTA output."""
    if name != "fermi-lite":
        raise ValueError(f"unsupported MiCall denovo assembler: {name}")
    work_dir = WorkDir.get()
    for old in work_dir.glob("assembly_*"):
        rmtree(old, ignore_errors=True)
    workspace = Path(mkdtemp(prefix="assembly_", dir=work_dir))
    # The Fermi-lite CLI consumes a single FASTQ. Interleave both source mates
    # (original order preserved, no reference/seed/evaluator input) first.
    interleave_pairs(first, second, workspace / BOTH_MATES)
    steps, output = command_steps(name, first, second, workspace)
    unitigs = fermi_lite_unitig_fastq(workspace)
    with unitigs.open("wb") as captured, \
            (workspace / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=workspace, env=None,
                           stdout=captured, stderr=log)
    convert_unitigs_to_fasta(unitigs, output)
    if not output.is_file():
        raise RuntimeError("fermi-lite produced no contigs FASTA")
    return output
