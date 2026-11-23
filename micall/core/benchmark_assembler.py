"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir


ASSEMBLER = "/usr/local/bin/skesa"
CONTIGS_FASTA = "skesa-contigs.fa"


def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run the pinned skesa CLI on the current paired reads.

    ``seeds`` is accepted only for the common denovo bridge signature: skesa
    has no seed, reference, truth or evaluator argument, and none is passed.
    The comma-separated --reads value preserves the two mates in order.
    """
    # ``seeds`` is deliberately ignored: the assembly must not depend on
    # contigs derived from any reference or prior/truth information.
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / CONTIGS_FASTA
    argv = [ASSEMBLER, "--reads", f"{first},{second}",
            "--contigs_out", str(output), "--cores", "2", "--memory", "4"]
    with (work / "assembler.log").open("wb") as log:
        subprocess.run(argv, check=True, cwd=work, env=None,
                       stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("skesa completed without the expected FASTA")
    return output
