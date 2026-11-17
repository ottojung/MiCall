"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir

from csv import DictReader
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

def sample_seeds(source: Path, output: Path) -> bool:
    """Same-sample consensus input only; not a reference."""
    with source.open() as rows, output.open("x") as fasta:
        count = SeqIO.write(
            (SeqRecord(Seq(row["contig"]), id=f"seed-{i}", description="")
             for i, row in enumerate(DictReader(rows)) if row["contig"]),
            fasta, "fasta",
        )
    return count > 0

def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run ivanka with fixed CLI options and the current paired reads."""
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / "contigs.fasta"
    argv = ["/usr/local/bin/ivanka", "--reads1", str(first),
            "--reads2", str(second), "--output", str(output)]
    if seeds is not None and sample_seeds(seeds, work / "seeds.fasta"):
        argv.extend(["--seeds", str(work / "seeds.fasta")])
    steps = [argv]
    with (work / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=work,
                           env={},
                           stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("ivanka completed without the expected FASTA")
    return output
