"""Execute external de novo assemblers through MiCall's normal downstream path."""
from pathlib import Path
from shutil import rmtree
import subprocess
from tempfile import mkdtemp

from micall.core.assembler_commands import command_steps
from micall.core.assembler_inputs import interleave_pairs
from micall.utils.work_dir import WorkDir


def run_external_assembler(name: str, first: Path, second: Path) -> Path:
    """Run a fixed command, rejecting unsuccessful or missing FASTA output."""
    if name not in ("ivanka", "haploflow", "megahit",
                    "abyss", "spades", "velvet"):
        raise ValueError(f"unsupported MiCall denovo assembler: {name}")
    work_dir = WorkDir.get()
    for old in work_dir.glob("assembly_*"):
        rmtree(old, ignore_errors=True)
    workspace = Path(mkdtemp(prefix="assembly_", dir=work_dir))
    if name == "haploflow":
        interleave_pairs(first, second, workspace / "both_mates.fastq")
    steps, output = command_steps(name, first, second, workspace)
    with (workspace / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=workspace,
                           env={} if name == "ivanka" else None,
                           stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError(f"{name} succeeded but produced no contigs FASTA")
    return output
