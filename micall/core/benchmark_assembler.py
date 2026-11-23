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
    log_path = work / "assembler.log"
    try:
        with log_path.open("wb") as log:
            subprocess.run(argv, check=True, cwd=work, env=None,
                           stdout=log, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        # The pinned SKESA source throws this exact error for zero contigs.
        # Its CLI exits 1 without producing the requested FASTA in that case.
        # Any other failure, output collision or truncated diagnostic is fatal.
        with log_path.open("rb") as log:
            log.seek(max(0, log.seek(0, 2) - 512))
            lines = log.read().splitlines()
        if (exc.returncode != 1 or output.exists() or not lines
                or lines[-1].strip() != b"Was not able to assemble anything"):
            raise
        output.touch()
    if not output.is_file():
        raise RuntimeError("skesa completed without the expected FASTA")
    return output
