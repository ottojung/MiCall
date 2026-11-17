"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir

def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run spades with fixed CLI options and the current paired reads."""
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / "spades" / "contigs.fasta"
    steps = [["spades.py", "-1", str(first), "-2", str(second),
              "--phred-offset", "33", "-t", "2",
              "-o", str(work / "spades")]]
    with (work / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=work,
                           env=None,
                           stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("spades completed without the expected FASTA")
    return output
