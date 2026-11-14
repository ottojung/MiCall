"""The parallel remapper must retain the original single-contig semantics."""

from collections import Counter
import csv
from io import StringIO
from pathlib import Path
import threading
import time

import tempfile
import unittest

from micall.core.remap_parallel import remap_splits


def fixture(tmp_path, count, mapper):
    groups = {}
    conseqs = {}
    for i in range(count):
        name = f"{i}-contig"
        left, right = tmp_path / f"{i}-R1.fastq", tmp_path / f"{i}-R2.fastq"
        left.write_text("@r\nACGT\n+\nIIII\n")
        right.write_text("@r\nTGCA\n+\nIIII\n")
        groups[name] = (left.open(), right.open())
        conseqs[name] = "ACGTACGT"
    remap, unmapped1, unmapped2, stderr = (StringIO() for _ in range(4))
    writer = csv.DictWriter(
        remap,
        [
            "qname",
            "flag",
            "rname",
            "pos",
            "mapq",
            "cigar",
            "rnext",
            "pnext",
            "tlen",
            "seq",
            "qual",
        ],
    )
    counts = Counter()
    try:
        result = remap_splits(
            groups,
            conseqs,
            str(tmp_path),
            None,
            None,
            5,
            5,
            5,
            stderr,
            unmapped1,
            unmapped2,
            counts,
            writer,
            mapper=mapper,
        )
    finally:
        for pair in groups.values():
            for file in pair:
                file.close()
    return (
        result,
        counts,
        list(
            csv.DictReader(
                StringIO(
                    "qname,flag,rname,pos,mapq,cigar,rnext,pnext,tlen,seq,qual\n"
                    + remap.getvalue()
                )
            )
        ),
        unmapped1.getvalue(),
        unmapped2.getvalue(),
        stderr.getvalue(),
    )


def fake_mapper(*args):
    rname = next(iter(args[2]))
    index = int(rname.split("-")[0])
    Path(args[4]).write_text(
        f"@SQ\tSN:{rname}\tLN:8\n"
        f"read{index}\t99\t{rname}\t1\t40\t4M\t=\t1\t0\tACGT\tIIII\n"
    )
    args[5].write(f"@unmapped{index}\nACGT\n+\nIIII\n")
    args[6].write(f"@unmapped{index}\nTGCA\n+\nIIII\n")
    args[12][rname] = 2
    args[13].write(f"mapped {index}\n")
    return 1


def check_parallel_results_are_deterministically_ordered(tmp_path):
    missed, counts, rows, u1, u2, log = fixture(tmp_path, 9, fake_mapper)
    assert missed == 9
    assert counts == Counter({f"{i}-contig": 2 for i in range(9)})
    assert [x["rname"] for x in rows] == [f"{i}-contig" for i in range(9)]
    assert [line for line in u1.splitlines() if line.startswith("@")] == [
        f"@unmapped{i}" for i in range(9)
    ]
    assert [line for line in u2.splitlines() if line.startswith("@")] == [
        f"@unmapped{i}" for i in range(9)
    ]
    assert log == "".join(f"mapped {i}\n" for i in range(9))
    assert not list(tmp_path.glob("micall_splits_*"))


def check_bounded_workers_and_unique_index_directories(tmp_path):
    lock = threading.Lock()
    active, maximum, paths = 0, 0, set()

    def probe(*args):
        nonlocal active, maximum
        with lock:
            active += 1
            maximum = max(maximum, active)
            paths.add(args[3])
        time.sleep(0.01)
        result = fake_mapper(*args)
        with lock:
            active -= 1
        return result

    missed, _, rows, _, _, _ = fixture(tmp_path, 11, probe)
    assert missed == len(rows) == len(paths) == 11
    assert 1 < maximum <= 4


def check_failed_remap_does_not_leave_partial_temp_artifacts(tmp_path):
    def failing(*args):
        if next(iter(args[2])) == "2-contig":
            raise ValueError("synthetic bowtie2 failure")
        return fake_mapper(*args)

    try:
        fixture(tmp_path, 9, failing)
    except ValueError as error:
        assert "synthetic bowtie2 failure" in str(error)
    else:
        raise AssertionError("mapper failure was suppressed")
    assert not list(tmp_path.glob("micall_splits_*"))


class ParallelRemapTests(unittest.TestCase):
    def test_preserves_order_and_all_pair_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            check_parallel_results_are_deterministically_ordered(Path(directory))

    def test_bounded_working_set(self):
        with tempfile.TemporaryDirectory() as directory:
            check_bounded_workers_and_unique_index_directories(Path(directory))

    def test_cleans_partial_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            check_failed_remap_does_not_leave_partial_temp_artifacts(Path(directory))
