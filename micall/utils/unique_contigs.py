"""Assemble a single strand-unique FASTA without altering source files.

A downstream read mapper cannot assign unambiguous molecule support when the
same complete DNA sequence is represented twice (e.g. both native and G2P).
Collapse those representations before the FIRST remap, rather than guessing
read counts for already-duplicated contigs after mapping.
"""
from pathlib import Path

from Bio import SeqIO
from micall.utils.cat import cat
from micall.utils.stitched_read_counts import molecule_key


def concatenate_unique_contigs(inputs, output):
    """Keep the first FASTA record for each complete double-stranded molecule.

    Header, order and original contig sequence are preserved; no evaluated
    reference, score, inferred genotype, or sample identity enters the decision.
    The native assembler takes precedence over later read-derived G2P copies.
    Zero contigs produces an empty FASTA, which is valid.
    """
    inputs = tuple(map(Path, inputs))
    seen = set()
    duplicates = False
    for path in inputs:
        with path.open() as source:
            for record in SeqIO.parse(source, "fasta"):
                key = molecule_key(str(record.seq))
                if key in seen:
                    duplicates = True
                seen.add(key)
    if not duplicates:
        # This is the common case for other assembler outputs. Preserve the
        # old pipeline byte-for-byte, including headers and line wrapping,
        # allowing its frozen results to be reused without recomputation.
        cat(inputs, Path(output))
        return

    seen.clear()
    with Path(output).open("w") as target:
        for path in inputs:
            with path.open() as source:
                for record in SeqIO.parse(source, "fasta"):
                    key = molecule_key(str(record.seq))
                    if key in seen:
                        continue
                    seen.add(key)
                    SeqIO.write(record, target, "fasta")
