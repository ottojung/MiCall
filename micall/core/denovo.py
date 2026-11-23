#! /usr/bin/env python3
import argparse
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
import shutil


from micall.utils.cache import cached
from micall.utils.work_dir import WorkDir


logger = logging.getLogger(__name__)


def count_fasta_sequences(file_path: Path) -> int:
    with file_path.open() as file:
        return sum(1 for line in file if line.startswith(">"))


@cached("denovo[savage]")
def run_subprocess(
    fastq1: Path,
    fastq2: Path,
    merged_contigs_csv: Optional[Path],
) -> Path:
    """Execute the fixed savage assembler, not a runtime selector."""
    from micall.core.benchmark_assembler import assemble
    return assemble(fastq1, fastq2, merged_contigs_csv)


def denovo(
    fastq1: Path,
    fastq2: Path,
    fasta: Path,
    merged_contigs_csv: Optional[Path] = None,
):
    """Use de novo assembly to build contigs from reads.

    :param fastq1: FASTQ file for read 1 reads
    :param fastq2: FASTQ file for read 2 reads
    :param fasta: file to write assembled contigs to
    :param work_dir: path for writing temporary files (optional, uses dynamic scope if not provided)
    :param merged_contigs_csv: open file to read contigs that were merged from
        amplicon reads
    """

    start_time = datetime.now()

    contigs_fasta_path = run_subprocess(fastq1, fastq2, merged_contigs_csv)
    shutil.copy(contigs_fasta_path, fasta)

    duration = datetime.now() - start_time
    contig_count = count_fasta_sequences(contigs_fasta_path)
    logger.info(
        "Assembled %d contigs in %s (%ds) on %s.",
        contig_count,
        duration,
        duration.total_seconds(),
        fastq1,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="A script to perform de novo assembly of reads to build contigs."
    )
    parser.add_argument(
        "fastq1",
        type=Path,
        help="Path to the FASTQ file containing read 1 of paired-end sequencing data.",
    )
    parser.add_argument(
        "fastq2",
        type=Path,
        help="Path to the FASTQ file containing read 2 of paired-end sequencing data.",
    )
    parser.add_argument(
        "fasta",
        type=Path,
        help="Path to the output FASTA file where assembled contigs will be written.",
    )

    args = parser.parse_args()
    with WorkDir.using(Path.cwd()):
        denovo(args.fastq1, args.fastq2, args.fasta)
