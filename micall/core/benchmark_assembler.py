"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir


ASSEMBLER = "penguin"
OUTPUT_NAME = "penguin-contigs.fa"
TMP_NAME = "penguin-tmp"


def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run penguin nuclassemble with fixed CLI options and both paired reads.

    ``seeds`` is accepted only for the common denovo bridge signature:
    nuclassemble has no seed, reference, truth or evaluator argument.
    """
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / OUTPUT_NAME
    argv = [ASSEMBLER, "nuclassemble", str(first), str(second),
            str(output), str(work / TMP_NAME)]
    with (work / "assembler.log").open("wb") as log:
        subprocess.run(argv, check=True, cwd=work, env=None,
                       stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("penguin completed without the expected FASTA")
    return output
