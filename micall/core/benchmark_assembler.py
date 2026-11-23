"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir


ASSEMBLER = "savage"
OUTPUT_NAME = "contigs_stage_c.fasta"


def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run SAVAGE in de-novo-only mode with both paired FASTQs.

    ``seeds`` is accepted only for the common denovo bridge signature:
    SAVAGE is invoked without ``--ref`` or ``--count_strains``, and receives
    no seed, reference, truth or evaluator argument.
    """
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / OUTPUT_NAME
    argv = [ASSEMBLER, "-p1", str(first), "-p2", str(second),
            "--split", "1", "-t", "2", "-o", str(work)]
    with (work / "assembler.log").open("wb") as log:
        subprocess.run(argv, check=True, cwd=work, env=None,
                       stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("savage completed without the expected FASTA")
    return output
