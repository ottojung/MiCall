"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir


def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run pinned tadpole contig mode with fixed CLI and paired reads.

    The pinned BBTools source accepts contig/graph/extend/correct/insert/discard;
    The legacy word assemble is rejected with Unknown mode.
    """
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / "tadpole-contigs.fa"
    # BBTools twin-file syntax in=R1,R2; fixed contig mode never takes ref=.
    steps = [[
        "tadpole.sh", f"in={first},{second}", f"out={output}",
        "mode=contig", "k=62",
    ]]
    with (work / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=work,
                           env=None,
                           stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("tadpole completed without the expected FASTA")
    return output
