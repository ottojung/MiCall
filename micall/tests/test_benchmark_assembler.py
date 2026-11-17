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
    return work / ['haploflow', 'contigs.fa'][0] if len(['haploflow', 'contigs.fa']) == 1 else work.joinpath(*['haploflow', 'contigs.fa'])


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
    assert [c[0][0] for c in calls] == ['haploflow']
    assert all(c[1]["check"] is True for c in calls)
    assert all(c[1]["stdout"] is not None for c in calls)


def test_missing_fasta_is_rejected(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        with pytest.raises(RuntimeError, match="without the expected FASTA"):
            assemble(first, second, None)



def test_interleaver_keeps_both_mates_and_rejects_truncation(tmp_path):
    from micall.core.benchmark_assembler import interleave
    first, second = sample_reads(tmp_path)
    out = tmp_path / "both.fastq"
    interleave(first, second, out)
    assert out.read_text().count("@sample/") == 2
    second.write_text(second.read_text()[:-2])
    with pytest.raises(ValueError, match="invalid or truncated"):
        interleave(first, second, tmp_path / "broken.fastq")
