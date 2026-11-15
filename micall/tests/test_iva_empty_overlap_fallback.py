"""An empty merge-mates stream must not discard valid original paired FASTQs."""
from pathlib import Path
from unittest.mock import patch
import subprocess

import pytest

from micall.core.denovo import run_iva_subprocess
from micall.utils.work_dir import WorkDir


def _reads(tmp_path):
    left, right = tmp_path / "read1.fastq", tmp_path / "read2.fastq"
    left.write_text("@a 1:N:0:1\nACGT\n+\nIIII\n")
    right.write_text("@a 2:N:0:1\nTGCA\n+\nIIII\n")
    return left, right


def test_zero_merged_reads_preserve_the_paired_inputs(tmp_path):
    left, right = _reads(tmp_path)
    invocations = []

    def subprocess_run(argv, **kwargs):
        invocations.append(argv)
        if argv[0] == "merge-mates":
            Path(argv[-1]).write_bytes(b"")
        else:
            output = Path(argv[-1])
            output.mkdir()
            (output / "contigs.fasta").write_text(">original-mate-assembly\nACGT\n")
        return subprocess.CompletedProcess(argv, 0)

    with WorkDir.using(tmp_path), patch(
        "micall.core.denovo.subprocess.run", side_effect=subprocess_run
    ):
        fasta = run_iva_subprocess.__wrapped__(left, right, None)
    assert fasta.read_text().startswith(">original-mate")
    assert invocations[0][:2] == ["merge-mates", left]
    assert invocations[1][:5] == ["iva", "-f", str(left), "-r", str(right)]
    assert "--reference" not in invocations[1]
    assert "--fr" not in invocations[1]


def test_overlapping_reads_keep_the_unchanged_iva_invocation(tmp_path):
    left, right = _reads(tmp_path)
    invocations = []

    def subprocess_run(argv, **kwargs):
        invocations.append(argv)
        if argv[0] == "merge-mates":
            Path(argv[-1]).write_bytes(b"@r\nACGT\n+\nIIII\n")
        else:
            output = Path(argv[-1])
            output.mkdir()
            (output / "contigs.fasta").write_text(">overlap\nACGT\n")
        return subprocess.CompletedProcess(argv, 0)

    with WorkDir.using(tmp_path), patch(
        "micall.core.denovo.subprocess.run", side_effect=subprocess_run
    ):
        fasta = run_iva_subprocess.__wrapped__(left, right, None)
    assert fasta.read_text().startswith(">overlap")
    assert invocations[1][1] == "--fr"


def test_missing_mate_does_not_trigger_paired_fallback(tmp_path):
    left, right = _reads(tmp_path)
    right.write_text("")
    invocations = []

    def subprocess_run(argv, **kwargs):
        invocations.append(argv)
        if argv[0] == "merge-mates":
            Path(argv[-1]).touch()
        else:
            raise subprocess.CalledProcessError(1, argv, output=b"empty")
        return subprocess.CompletedProcess(argv, 0)

    with WorkDir.using(tmp_path), patch(
        "micall.core.denovo.subprocess.run", side_effect=subprocess_run
    ):
        result = run_iva_subprocess.__wrapped__(left, right, None)
    assert result.read_bytes() == b""
    assert invocations[1][1] == "--fr"
