"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir

import gzip

def read_fastq(path: Path):
    opener = gzip.open if str(path).endswith(".gz") else open
    return opener(path, "rt")

def interleave(first: Path, second: Path, destination: Path):
    with read_fastq(first) as a, read_fastq(second) as b, destination.open("x") as out:
        while True:
            pairs: list[list[str] | None] = []
            for src in (a, b):
                lines = [src.readline() for _ in range(4)]
                if not lines[0]:
                    pairs.append(None)
                    continue
                if (not all(lines) or not lines[0].startswith("@")
                        or not lines[2].startswith("+")
                        or len(lines[1].rstrip("\r\n"))
                        != len(lines[3].rstrip("\r\n"))):
                    raise ValueError("invalid or truncated paired FASTQ")
                pairs.append(lines)
            if pairs == [None, None]:
                return
            if any(pair is None for pair in pairs):
                raise ValueError("unequal FASTQ mate counts")
            for pair in pairs:
                assert pair is not None
                out.writelines(pair)

def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run haploflow with fixed CLI options and the current paired reads."""
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    output = work / "haploflow" / "contigs.fa"
    paired = work / "paired.fastq"
    interleave(first, second, paired)
    steps = [["haploflow", "--read-file", str(paired),
              "--out", str(work / "haploflow"),
              "--filter", "100", "--strict", "0"]]
    with (work / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=work,
                           env=None,
                           stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("haploflow completed without the expected FASTA")
    return output
