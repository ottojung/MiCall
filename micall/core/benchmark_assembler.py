"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir

def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run abyss with fixed CLI options and the current paired reads."""
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / "assembly-contigs.fa"
    steps = [["abyss-pe", "k=41", "B=128M", "j=2",
              "name=assembly", f"in={first} {second}", output.name]]
    with (work / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=work,
                           env=None,
                           stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("abyss completed without the expected FASTA")
    return output
