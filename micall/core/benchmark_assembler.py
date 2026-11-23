"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import subprocess
from micall.utils.work_dir import WorkDir


SOAPDENOVO2_CONFIG = "soapdenovo2.config"
SOAPDENOVO2_PREFIX = "soapdenovo2_graph"


def soapdenovo2_config_text(first: Path, second: Path) -> str:
    """Exact upstream [LIB] grammar: paired FASTQ via q1/q2, no reference data."""
    return (
        "max_rd_len=100\n"
        "[LIB]\n"
        "avg_ins=200\n"
        "reverse_seq=0\n"
        "asm_flags=3\n"
        "rd_len_cutoff=100\n"
        "rank=1\n"
        "pair_num_cutoff=3\n"
        "map_len=32\n"
        f"q1={first}\n"
        f"q2={second}\n"
    )


def write_soapdenovo2_config(first: Path, second: Path, work: Path) -> Path:
    config = work / SOAPDENOVO2_CONFIG
    config.write_text(soapdenovo2_config_text(first, second))
    return config


def assemble(first: Path, second: Path, seeds: Path | None) -> Path:
    """Run SOAPdenovo2 all with fixed CLI options and the paired reads."""
    parent = WorkDir.get()
    for leftover in parent.glob("assembly_*"):
        rmtree(leftover, ignore_errors=True)
    work = Path(mkdtemp(dir=parent, prefix="assembly_"))
    config = write_soapdenovo2_config(first, second, work)
    prefix = work / SOAPDENOVO2_PREFIX
    output = work / (SOAPDENOVO2_PREFIX + ".contig")
    # Native output is graph_prefix.contig, itself FASTA-formatted. Zero
    # contigs on true success leaves an empty, still-valid FASTA; never
    # fabricate a record.
    steps = [[
        "SOAPdenovo-63mer", "all", "-s", str(config), "-K", "63", "-R",
        "-o", str(prefix),
    ]]
    with (work / "assembler.log").open("wb") as log:
        for argv in steps:
            subprocess.run(argv, check=True, cwd=work,
                           env=None,
                           stdout=log, stderr=subprocess.STDOUT)
    if not output.is_file():
        raise RuntimeError("soapdenovo2 completed without the expected FASTA")
    return output
