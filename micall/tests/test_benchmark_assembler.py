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
    return work / ['contigs.fasta'][0] if len(['contigs.fasta']) == 1 else work.joinpath(*['contigs.fasta'])


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
    assert [c[0][0] for c in calls] == ['/usr/local/bin/ivanka']
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



def test_same_sample_seed_csv_is_supplied(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    seed = tmp_path / "consensus.csv"
    seed.write_text("contig\nACGTACGTACGT\n")
    observed = []

    def fake_run(argv, **kwargs):
        observed.extend(map(str, argv))
        result = expected_output(Path(kwargs["cwd"]))
        result.write_text(">assembled\nACGT\n")
        assert kwargs["env"] == {}
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        assemble(first, second, seed)
    assert "--seeds" in observed
    assert Path(observed[observed.index("--seeds") + 1]).read_text().startswith(">seed-0")
