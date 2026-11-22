"""Committed MiCall integration commands, requiring no reference information."""

from pathlib import Path

ASSEMBLERS = (
    "iva",
    "ivanka",
    "haploflow",
    "megahit",
    "abyss",
    "spades",
    "velvet",
    "soapdenovo2",
)

# Upstream contract attested at SOAPdenovo2 7560c0b9 (README.md / example.config).
SOAPDENOVO2_CONFIG = "soapdenovo2.config"
SOAPDENOVO2_PREFIX = "soapdenovo2_graph"


def soapdenovo2_config_text(first, second):
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
    """Materialise the pinned-source LIB config from both validated mates."""
    config = work / SOAPDENOVO2_CONFIG
    config.write_text(soapdenovo2_config_text(str(first), str(second)))
    return config


def command_steps(name: str, first: Path, second: Path, work: Path):
    """Return exact CLI steps and expected output; never run a shell."""
    first, second = str(first), str(second)
    if name == "ivanka":
        result = work / "ivanka_contigs.fasta"
        return [
            [
                "/usr/local/bin/ivanka",
                "--reads1",
                first,
                "--reads2",
                second,
                "--output",
                str(result),
            ]
        ], result
    if name == "haploflow":
        result = work / "haploflow/contigs.fa"
        return [
            [
                "haploflow",
                "--read-file",
                str(work / "both_mates.fastq"),
                "--out",
                str(work / "haploflow"),
                "--filter",
                "100",
                "--strict",
                "0",
            ]
        ], result
    if name == "megahit":
        result = work / "megahit/final.contigs.fa"
        return [
            [
                "megahit",
                "-1",
                first,
                "-2",
                second,
                "-t",
                "2",
                "-o",
                str(work / "megahit"),
            ]
        ], result
    if name == "abyss":
        result = work / "assembly-contigs.fa"
        # Build only the MiCall-consumed contigs, not unused scaffold stages.
        return [
            [
                "abyss-pe",
                "k=41",
                "B=128M",
                "j=2",
                "name=assembly",
                f"in={first} {second}",
                result.name,
            ]
        ], result
    if name == "spades":
        result = work / "spades/contigs.fasta"
        return [
            [
                "spades.py",
                "-1",
                first,
                "-2",
                second,
                "--phred-offset",
                "33",
                "-t",
                "2",
                "-o",
                str(work / "spades"),
            ]
        ], result
    if name == "velvet":
        result = work / "velvet/contigs.fa"
        return [
            [
                "velveth",
                str(work / "velvet"),
                "31",
                "-fastq.gz",
                "-shortPaired",
                "-separate",
                first,
                second,
            ],
            ["velvetg", str(work / "velvet"), "-ins_length", "270", "-exp_cov", "auto"],
        ], result
    if name == "soapdenovo2":
        # Native output is graph_prefix.contig, itself FASTA-formatted
        # (standardPregraph/output_contig.c:65-88,157). Zero contigs on true
        # success leaves an empty, still-valid FASTA; never fabricate a record.
        prefix = work / SOAPDENOVO2_PREFIX
        result = work / (SOAPDENOVO2_PREFIX + ".contig")
        return [
            [
                "SOAPdenovo-63mer",
                "all",
                "-s",
                str(work / SOAPDENOVO2_CONFIG),
                "-K",
                "63",
                "-R",
                "-o",
                str(prefix),
            ]
        ], result
    raise ValueError(f"unsupported MiCall denovo assembler: {name}")
