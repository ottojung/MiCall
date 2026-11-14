"""Bounded concurrent second-pass remapping of independently assigned pairs.

The initial mapping has already assigned each original read pair to one contig.
The second pass must not allow other contigs to steal those assigned pairs.
"""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory

MAX_WORKERS = 4


def remap_splits(
    groups,
    conseqs,
    work_path,
    bowtie2,
    bowtie2_build,
    raw_count,
    rdgopen,
    rfgopen,
    stderr,
    unmapped1,
    unmapped2,
    new_counts,
    remap_writer,
    mapper=None,
):
    """Run isolated single-contig remaps concurrently, commit results in order."""
    from micall.core.remap import (
        MixedReferenceSplitter,
        map_to_reference,
        write_remap_row,
    )

    mapper = mapper or map_to_reference
    items = list(groups.items())
    if not items:
        return 0

    with TemporaryDirectory(prefix="micall_splits_", dir=work_path or None) as tmp:
        root = Path(tmp)

        def execute(index, rname, fastqs):
            own = root / str(index)
            own.mkdir()
            reffile, samfile = own / "temp.fasta", own / "temp.sam"
            first, second = own / "unmapped1.fastq", own / "unmapped2.fastq"
            log = own / "bowtie2.stderr"
            counts = Counter()
            with (
                first.open("w") as out1,
                second.open("w") as out2,
                log.open("w") as err,
            ):
                missed = mapper(
                    fastqs[0].name,
                    fastqs[1].name,
                    {rname: conseqs[rname]},
                    str(reffile),
                    str(samfile),
                    out1,
                    out2,
                    bowtie2,
                    bowtie2_build,
                    raw_count,
                    rdgopen,
                    rfgopen,
                    counts,
                    err,
                    None,
                )
            return missed, counts, first, second, samfile, log

        total_unmapped = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            # A batch limits both concurrent Bowtie2 processes and pending SAMs.
            for offset in range(0, len(items), MAX_WORKERS):
                batch = items[offset : offset + MAX_WORKERS]
                futures = [
                    pool.submit(execute, offset + i, name, reads)
                    for i, (name, reads) in enumerate(batch)
                ]
                for task in futures:
                    missed, counts, first, second, sam, log = task.result()
                    total_unmapped += missed
                    new_counts.update(counts)
                    for source, target in (
                        (first, unmapped1),
                        (second, unmapped2),
                        (log, stderr),
                    ):
                        with source.open() as content:
                            copyfileobj(content, target)
                    with sam.open() as content:
                        for fields in MixedReferenceSplitter.walk(content):
                            write_remap_row(remap_writer, fields)
                    for path in (first, second, sam, log):
                        path.unlink()
    return total_unmapped
