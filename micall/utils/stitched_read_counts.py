"""Carry original remap counts to stitched sequences without positional aliasing.

The referenceless stitcher can reorder, merge, or omit its input contigs.
Original remap-count row numbers are therefore NOT stitched row numbers.
"""
import csv
from collections import defaultdict
from io import StringIO
from typing import TextIO

from Bio.Seq import Seq
from micall.utils.referencefull_contig_stitcher import read_remap_counts


def molecule_key(sequence: str) -> str:
    """Identify a complete molecule regardless of its reported strand."""
    dna = sequence.upper()
    reverse = str(Seq(dna).reverse_complement())
    return min(dna, reverse)


def project_stitched_counts(
    unstitched_csv: TextIO,
    stitched_csv: TextIO,
    original_counts_csv: TextIO,
) -> StringIO:
    """Transfer counts only when stitched sequence identity is demonstrated.

    Repeated identical unstitched records may split one sequence's remap
    assignments: sum their source counts before projection. A merged or
    altered stitched sequence has no authenticated count, not a borrowed
    count or an invented zero. The downstream stitcher handles unknowns.
    """
    counts = read_remap_counts(original_counts_csv)
    supported = defaultdict(int)
    unknown = set()
    for index, record in enumerate(csv.DictReader(unstitched_csv), start=1):
        seq = molecule_key(record["contig"])
        name = f'{index}-{record["ref"]}'
        if name in counts:
            supported[seq] += counts[name]
        else:
            unknown.add(seq)
    stream = StringIO()
    writer = csv.DictWriter(stream, fieldnames=("type", "count"))
    writer.writeheader()
    for index, record in enumerate(csv.DictReader(stitched_csv), start=1):
        seq = molecule_key(record["contig"])
        if seq not in supported or seq in unknown:
            continue
        writer.writerow({
            "type": f'remap {index}-{record["ref"]}',
            "count": supported[seq],
        })
    stream.seek(0)
    return stream
