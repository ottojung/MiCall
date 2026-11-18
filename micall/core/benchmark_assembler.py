"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir


def _abyss_produced_no_unitigs(work: Path) -> bool:
    unitigs = work / "assembly-1.fa"
    if not unitigs.is_file():
        return False
    try:
        text = unitigs.read_text()
    except OSError:
        return False
    return '>' not in text


def _empty_abyss_assembly(work: Path, output: Path, exc: subprocess.CalledProcessError) -> bool:
    if output.is_file():
        return False
    if not _abyss_produced_no_unitigs(work):
        return False
    log_path = work / "assembler.log"
    try:
        log_text = log_path.read_text(errors="replace")
    except OSError:
        log_text = ""
    # abyss-rresolver-short asserts on an empty graph when bloom-dbg produced
    # no unitigs; treat this as a valid no-contig assembly outcome.
    if "num_vertices(g) > 0" in log_text:
        return True
    # Fallback: empty unitigs and failed pipeline before final output.
    return exc.returncode != 0


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
