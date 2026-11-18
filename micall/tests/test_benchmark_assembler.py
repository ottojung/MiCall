"""Assembler branch tests: fixed command, paired input and failure behavior."""
from pathlib import Path
import subprocess
import pytest

from micall.core.benchmark_assembler import assemble
from micall.utils.work_dir import WorkDir


def sample_reads(tmp_path):
    first, second = tmp_path / "R1.fastq", tmp_path / "R2.fastq"
    for p, mate in [(first, 1), (second, 2)]:
        p.write_text(f"@sample/{mate}\n" + "ACGT" * 40
                     + "\n+\n" + "I" * 160 + "\n")
    return first, second


def expected_output(work):
    return work / ['assembly-contigs.fa'][0] if len(['assembly-contigs.fa']) == 1 else work.joinpath(*['assembly-contigs.fa'])


def test_only_fixed_assembler_is_invoked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((list(map(str, argv)), kwargs))
        output = expected_output(Path(kwargs["cwd"]))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(">contig\nACGT\n")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        output = assemble(first, second, None)
    assert output.read_text() == ">contig\nACGT\n"
    assert calls
    assert [c[0][0] for c in calls] == ['abyss-pe']
    assert all(c[1]["check"] is True for c in calls)
    assert all(c[1]["stdout"] is not None for c in calls)


def test_missing_fasta_is_rejected(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path), pytest.raises(
        RuntimeError, match="without the expected FASTA"
    ):
        assemble(first, second, None)

def test_empty_unitigs_pipeline_failure_becomes_no_contigs(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        work = Path(kwargs["cwd"])
        (work / "assembly-1.fa").write_text("")
        (work / "assembler.log").write_text(
            "abyss-rresolver-short: ../Graph/DotIO.h:307: Assertion `num_vertices(g) > 0' failed.\n")
        raise subprocess.CalledProcessError(2, argv)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        output = assemble(first, second, None)
    assert output.is_file()
    assert output.read_text() == ""


def test_nonempty_unitigs_failure_is_not_masked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        work = Path(kwargs["cwd"])
        (work / "assembly-1.fa").write_text(">contig\nACGT\n")
        raise subprocess.CalledProcessError(2, argv)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path), pytest.raises(subprocess.CalledProcessError):
        assemble(first, second, None)


def test_failure_without_empty_unitigs_is_not_masked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        raise subprocess.CalledProcessError(1, argv)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path), pytest.raises(subprocess.CalledProcessError):
        assemble(first, second, None)
