"""Minia adapter tests: fixed, reference-blind commands on exact paired reads."""
from pathlib import Path
import gzip
import subprocess

import pytest

from micall.core import benchmark_assembler as adapter
from micall.core.denovo import denovo
from micall.utils.work_dir import WorkDir


TOOL = "/usr/local/bin/minia"
BANNED = ("--seeds", "--sra_run", "--targets", "--reference", "--ref",
          "--genome")


def sample_reads(tmp_path):
    first, second = tmp_path / "R1.fastq", tmp_path / "R2.fastq"
    for path, mate in ((first, 1), (second, 2)):
        path.write_text(f"@sample/{mate}\n" + "ACGT" * 40
                        + "\n+\n" + "I" * 160 + "\n")
    return first, second


def fake_minia(calls, content=">contig\nACGT\n", write_output=True):
    def run(argv, **kwargs):
        calls.append((list(map(str, argv)), kwargs))
        if write_output:
            output = Path(kwargs["cwd"]) / adapter.CONTIGS_FASTA
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content)
        return subprocess.CompletedProcess(argv, 0)
    return run


def test_only_fixed_minia_command_is_invoked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_minia(calls))
    with WorkDir.using(tmp_path):
        output = adapter.assemble(first, second, None)
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv == [TOOL, "-in", str(Path(kwargs["cwd"]) / adapter.BOTH_MATES),
                    "-kmer-size", "31", "-abundance-min", "3",
                    "-out", str(Path(kwargs["cwd"]) / "minia")]
    assert output == Path(kwargs["cwd"]) / adapter.CONTIGS_FASTA
    assert output.read_text() == ">contig\nACGT\n"
    assert kwargs["check"] is True
    assert kwargs["env"] is None
    assert kwargs["stdout"] is not None
    assert (Path(kwargs["cwd"]) / "assembler.log").is_file()


def test_both_mates_are_interleaved_in_original_order(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    monkeypatch.setattr(adapter.subprocess, "run", fake_minia([]))
    with WorkDir.using(tmp_path):
        output = adapter.assemble(first, second, None)
    reads = (output.parent / adapter.BOTH_MATES).read_text().splitlines()
    assert [line for line in reads if line.startswith("@")] == [
        "@sample/1", "@sample/2"]


def test_gzipped_mates_are_read_without_truncation(tmp_path, monkeypatch):
    first, second = tmp_path / "R1.fastq.gz", tmp_path / "R2.fastq.gz"
    with gzip.open(first, "wt") as out:
        out.write("@r1/1\nACGT\n+\nIIII\n")
    with gzip.open(second, "wt") as out:
        out.write("@r1/2\nACGT\n+\nIIII\n")
    monkeypatch.setattr(adapter.subprocess, "run", fake_minia([]))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    work = max(tmp_path.glob("assembly_*"))
    assert (work / adapter.BOTH_MATES).read_text().count("@") == 2


def test_unequal_mate_counts_fail_closed(tmp_path):
    first, second = sample_reads(tmp_path)
    with second.open("a") as out:
        out.write("@extra/2\nACGT\n+\nIIII\n")
    with WorkDir.using(tmp_path), pytest.raises(
        ValueError, match="unequal FASTQ mate counts"
    ):
        adapter.interleave_pairs(first, second, tmp_path / "joined.fastq")


def test_seeded_contigs_never_reach_the_command(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    seeds = tmp_path / "merged.csv"
    seeds.write_text("contig\nSECRET_TRUTH_CONTIG\n")
    plain, seeded = [], []
    monkeypatch.setattr(adapter.subprocess, "run", fake_minia(plain))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    monkeypatch.setattr(adapter.subprocess, "run", fake_minia(seeded))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, seeds)
    def without_workdir(argv):
        return [arg.replace(str(Path(argv[2]).parent), "<work>") for arg in argv]

    assert without_workdir(seeded[0][0]) == without_workdir(plain[0][0])
    command = " ".join(seeded[0][0]).lower()
    assert not any(banned in command for banned in BANNED)
    assert "SECRET_TRUTH_CONTIG" not in command


def test_zero_contig_assembly_is_a_valid_empty_fasta(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    monkeypatch.setattr(adapter.subprocess, "run", fake_minia([], content=""))
    with WorkDir.using(tmp_path):
        output = adapter.assemble(first, second, None)
    assert output.is_file()
    assert output.read_text() == ""


def test_missing_fasta_fails_closed(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    monkeypatch.setattr(adapter.subprocess, "run",
                        fake_minia([], write_output=False))
    with WorkDir.using(tmp_path), pytest.raises(
        RuntimeError, match="without the expected FASTA"
    ):
        adapter.assemble(first, second, None)


def test_failed_program_is_not_masked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def run(argv, **kwargs):
        raise subprocess.CalledProcessError(7, [TOOL])

    monkeypatch.setattr(adapter.subprocess, "run", run)
    with WorkDir.using(tmp_path), pytest.raises(subprocess.CalledProcessError):
        adapter.assemble(first, second, None)


def test_clinical_denovo_uses_the_fixed_adapter(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_minia(calls))
    destination = tmp_path / "clinical-contigs.fasta"
    with WorkDir.using(tmp_path):
        denovo(first, second, destination)
    assert destination.read_text() == ">contig\nACGT\n"
    assert len(calls) == 1
    assert calls[0][0][0] == TOOL


def test_source_has_no_runtime_assembler_selector():
    root = Path(__file__).resolve().parents[2]
    for relative in ("micall/core/denovo.py", "micall/core/benchmark_assembler.py"):
        source = (root / relative).read_text()
        assert "MICALL_DENOVO_ASSEMBLER" not in source
        assert "os.environ" not in source
        assert "assembler_dispatch" not in source
