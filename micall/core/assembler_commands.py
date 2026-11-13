"""Committed MiCall integration commands, requiring no reference information."""
from pathlib import Path

ASSEMBLERS = ("iva", "ivanka", "haploflow", "megahit",
              "abyss", "spades", "velvet")


def command_steps(name: str, first: Path, second: Path, work: Path):
    """Return exact CLI steps and expected output; never run a shell."""
    first, second = str(first), str(second)
    if name == "ivanka":
        result = work / "ivanka_contigs.fasta"
        return [["/usr/local/bin/ivanka", "--reads1", first, "--reads2",
                 second, "--output", str(result)]], result
    if name == "haploflow":
        result = work / "haploflow/contigs.fa"
        return [["haploflow", "--read-file", str(work / "both_mates.fastq"),
                 "--out", str(work / "haploflow"), "--filter", "100",
                 "--strict", "0"]], result
    if name == "megahit":
        result = work / "megahit/final.contigs.fa"
        return [["megahit", "-1", first, "-2", second, "-t", "2",
                 "-o", str(work / "megahit")]], result
    if name == "abyss":
        result = work / "assembly-contigs.fa"
        # Build exactly the contig target consumed by MiCall. Subsequent
        # distance-estimation/scaffolding stages are not used as input here.
        return [["abyss-pe", "k=41", "B=128M", "j=2",
                 "name=assembly", f"in={first} {second}",
                 "assembly-contigs.fa"]], result
    if name == "spades":
        result = work / "spades/contigs.fasta"
        return [["spades.py", "-1", first, "-2", second,
                 "--phred-offset", "33", "-t", "2",
                 "-o", str(work / "spades")]], result
    if name == "velvet":
        result = work / "velvet/contigs.fa"
        return [["velveth", str(work / "velvet"), "31", "-fastq.gz",
                 "-shortPaired", "-separate", first, second],
                ["velvetg", str(work / "velvet"), "-ins_length", "270",
                 "-exp_cov", "auto"]], result
    raise ValueError(f"unsupported MiCall denovo assembler: {name}")
