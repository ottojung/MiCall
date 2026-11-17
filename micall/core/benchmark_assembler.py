"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir

def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run velvet with fixed CLI options and the current paired reads."""
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / "velvet" / "contigs.fa"
    compressed = str(first).endswith(".gz")
    if compressed != str(second).endswith(".gz"):
        raise ValueError("Velvet requires equally compressed FASTQs")
    encoding = "-fastq.gz" if compressed else "-fastq"
    steps = [
        ["velveth", str(work / "velvet"), "31", encoding,
         "-shortPaired", "-separate", str(first), str(second)],
        ["velvetg", str(work / "velvet"), "-ins_length", "270",
         "-exp_cov", "auto"],
    ]
    with (work / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=work,
                           env=None,
                           stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("velvet completed without the expected FASTA")
    return output
