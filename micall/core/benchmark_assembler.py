"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir


FQ2FA = "/usr/local/bin/fq2fa"
ASSEMBLER = "/usr/local/bin/idba_ud"


def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run the pinned idba-ud CLI on the current paired reads.

    ``seeds`` is accepted only for the common denovo bridge signature:
    idba-ud has no seed, reference, truth or evaluator argument, and none is
    passed. fq2fa derives the interleaved FASTA that idba_ud consumes from
    both original mates in order.
    """
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    merged = work / "idba-reads.fa"
    outdir = work / "idba-out"
    output = outdir / "contig.fa"
    steps = [
        [FQ2FA, "--merge", "--filter", str(first), str(second), str(merged)],
        [ASSEMBLER, "-r", str(merged), "-o", str(outdir)],
    ]
    with (work / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=work, env=None,
                           stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("idba-ud completed without the expected FASTA")
    return output
