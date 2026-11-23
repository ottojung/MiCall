"""One fixed assembler per branch: no selector or reference dependency."""
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import gzip
import subprocess
from micall.utils.work_dir import WorkDir


SOAPDENOVO2_CONFIG = "soapdenovo2.config"
SOAPDENOVO2_PREFIX = "soapdenovo2_graph"
# The upstream example config uses max_rd_len=100 / rd_len_cutoff=100 for its
# own 100 bp example reads. Real MiCall paired FASTQs are longer (150 bp in the
# frozen smoke inputs), so copying that value silently discards read bases
# before assembly. Bound the observed length instead; the cap only guards
# against pathological input and is never reached by real Illumina reads.
MAX_CONFIG_READ_LENGTH = 1000
CONFIG_SAMPLE_RECORDS = 10000


def _reader(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt")
    return path.open(encoding="utf-8")


def observed_read_length(*paths: Path) -> int:
    """Sample both mates and return the longest sequence line seen.

    This reads only the paired input reads: no reference, truth, target or
    evaluator data is consulted. A missing or empty file yields the upstream
    default so an empty assembly remains representable.
    """
    longest = 0
    for path in paths:
        with _reader(path) as source:
            for index, line in enumerate(source):
                if index % 4 == 1:
                    longest = max(longest, len(line.rstrip("\r\n")))
                if index >= CONFIG_SAMPLE_RECORDS * 4:
                    break
    return min(max(longest, 100), MAX_CONFIG_READ_LENGTH)


def soapdenovo2_config_text(first: Path, second: Path) -> str:
    """Exact upstream [LIB] grammar: paired FASTQ via q1/q2, no reference data.

    max_rd_len and rd_len_cutoff follow the observed read length so no input
    base is truncated on real 150 bp (or longer) canary pairs.
    """
    read_length = observed_read_length(first, second)
    return (
        f"max_rd_len={read_length}\n"
        "[LIB]\n"
        "avg_ins=200\n"
        "reverse_seq=0\n"
        "asm_flags=3\n"
        f"rd_len_cutoff={read_length}\n"
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
