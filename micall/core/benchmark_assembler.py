"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir


def _empty_abyss_assembly(work: Path, output: Path,
                          exc: subprocess.CalledProcessError) -> bool:
    """Recognize the exact ABySS empty-graph assertion, not arbitrary errors."""
    unitigs = work / "assembly-1.fa"
    if (exc.returncode != 2 or output.exists()
            or not unitigs.is_file() or unitigs.stat().st_size != 0):
        return False
    log_path = work / "assembler.log"
    if not log_path.is_file():
        return False
    return "Assertion `num_vertices(g) > 0' failed" in log_path.read_text(
        errors="replace")


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
            try:
                subprocess.run(argv, check=True, cwd=work,
                               env=None,
                               stdout=log, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as exc:
                if _empty_abyss_assembly(work, output, exc):
                    output.write_text("")
                    return output
                raise
    if not output.is_file():
        raise RuntimeError("abyss completed without the expected FASTA")
    return output
