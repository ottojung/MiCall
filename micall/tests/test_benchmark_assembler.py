"""SKESA adapter tests: one fixed, reference-blind command on exact paired reads."""
from pathlib import Path
import gzip
import subprocess

import pytest

from micall.core import benchmark_assembler as adapter
from micall.core.denovo import denovo
from micall.utils.work_dir import WorkDir


TOOL = "/usr/local/bin/skesa"
BANNED = ("--seeds", "--sra_run", "--targets", "--reference", "--ref",
          "--genome", "--use_paired_ends")


def sample_reads(tmp_path):
    first, second = tmp_path / "R1.fastq", tmp_path / "R2.fastq"
    for path, mate in ((first, 1), (second, 2)):
        path.write_text(f"@sample/{mate}\n" + "ACGT" * 40
                        + "\n+\n" + "I" * 160 + "\n")
    return first, second


def fake_skesa(calls, content=">contig\nACGT\n"):
    def run(argv, **kwargs):
        calls.append((list(map(str, argv)), kwargs))
        output = Path(kwargs["cwd"]) / adapter.CONTIGS_FASTA
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content)
        return subprocess.CompletedProcess(argv, 0)
    return run


def test_only_fixed_skesa_command_is_invoked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_skesa(calls))
    with WorkDir.using(tmp_path):
        output = adapter.assemble(first, second, None)
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv == [TOOL, "--reads", f"{first},{second}",
                    "--contigs_out", str(output), "--cores", "2",
                    "--memory", "4"]
    assert kwargs["check"] is True
    assert kwargs["env"] is None
    assert kwargs["stdout"] is not None
    assert output.read_text() == ">contig\nACGT\n"
    assert (Path(kwargs["cwd"]) / "assembler.log").is_file()


def test_seeded_contigs_never_reach_the_command(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    seeds = tmp_path / "merged.csv"
    seeds.write_text("contig\nSECRET_TRUTH_CONTIG\n")
    plain, seeded = [], []
    monkeypatch.setattr(adapter.subprocess, "run", fake_skesa(plain))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    monkeypatch.setattr(adapter.subprocess, "run", fake_skesa(seeded))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, seeds)
    def without_workdir(argv):
        return argv[:3] + ["<work>/skesa-contigs.fa"] + argv[5:]

    assert without_workdir(seeded[0][0]) == without_workdir(plain[0][0])
    command = " ".join(seeded[0][0]).lower()
    assert not any(banned in command for banned in BANNED)
    assert "SECRET_TRUTH_CONTIG" not in command


def test_zero_contig_assembly_is_a_valid_empty_fasta(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    monkeypatch.setattr(adapter.subprocess, "run", fake_skesa([], content=""))
    with WorkDir.using(tmp_path):
        output = adapter.assemble(first, second, None)
    assert output.is_file()
    assert output.read_text() == ""


def test_native_no_contig_exit_one_is_valid_empty_fasta(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def run(argv, **kwargs):
        kwargs["stdout"].write(b"Contigs out: 0\nWas not able to assemble anything\n")
        raise subprocess.CalledProcessError(1, argv)

    monkeypatch.setattr(adapter.subprocess, "run", run)
    destination = tmp_path / "clinical-contigs.fasta"
    with WorkDir.using(tmp_path):
        denovo(first, second, destination)
    assert destination.is_file()
    assert destination.read_bytes() == b""


@pytest.mark.parametrize(("returncode", "diagnostic", "preexisting"), [
    (2, b"Was not able to assemble anything\n", False),
    (1, b"Other assembler error\n", False),
    (1, b"Was not able to assemble anything\nAdditional failure\n", False),
    (1, b"Was not able to assemble anything\n", True),
])
def test_noncanonical_native_failures_are_not_masked(
        tmp_path, monkeypatch, returncode, diagnostic, preexisting):
    first, second = sample_reads(tmp_path)

    def run(argv, **kwargs):
        kwargs["stdout"].write(diagnostic)
        if preexisting:
            (Path(kwargs["cwd"]) / adapter.CONTIGS_FASTA).write_text("invalid")
        raise subprocess.CalledProcessError(returncode, argv)

    monkeypatch.setattr(adapter.subprocess, "run", run)
    with WorkDir.using(tmp_path), pytest.raises(subprocess.CalledProcessError):
        adapter.assemble(first, second, None)


def test_missing_fasta_fails_closed(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(adapter.subprocess, "run", run)
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


def test_gzipped_mates_are_passed_verbatim(tmp_path, monkeypatch):
    first, second = tmp_path / "R1.fastq.gz", tmp_path / "R2.fastq.gz"
    with gzip.open(first, "wt") as out:
        out.write("@r1/1\nACGT\n+\nIIII\n")
    with gzip.open(second, "wt") as out:
        out.write("@r1/2\nACGT\n+\nIIII\n")
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_skesa(calls))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    assert calls[0][0][2] == f"{first},{second}"


def test_clinical_denovo_uses_the_fixed_adapter(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_skesa(calls))
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
