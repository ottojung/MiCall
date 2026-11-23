"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir


MPIEXEC = "mpiexec"
ASSEMBLER = "Ray"
CONTIGS_FASTA = "Contigs.fasta"


def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run the pinned Ray CLI on the current paired reads.

    ``seeds`` is accepted only for the common denovo bridge signature: Ray
    has no seed, reference, truth or evaluator argument, and none is passed.
    -p consumes both original paired FASTQs in their given order.
    """
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    outdir = work / "ray-out"
    output = outdir / CONTIGS_FASTA
    argv = [MPIEXEC, "-n", "2", ASSEMBLER, "-k31",
            "-p", str(first), str(second), "-o", str(outdir)]
    with (work / "assembler.log").open("wb") as log:
        subprocess.run(argv, check=True, cwd=work, env=None,
                       stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("Ray completed without the expected FASTA")
    return output
