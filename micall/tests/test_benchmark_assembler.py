"""IDBA-UD adapter tests: fixed, reference-blind commands on exact paired reads."""
from pathlib import Path
import gzip
import subprocess

import pytest

from micall.core import benchmark_assembler as adapter
from micall.core.denovo import denovo
from micall.utils.work_dir import WorkDir


FQ2FA = "/usr/local/bin/fq2fa"
TOOL = "/usr/local/bin/idba_ud"
BANNED = ("--seeds", "--sra_run", "--targets", "--reference", "--ref",
          "--genome")


def sample_reads(tmp_path):
    first, second = tmp_path / "R1.fastq", tmp_path / "R2.fastq"
    for path, mate in ((first, 1), (second, 2)):
        path.write_text(f"@sample/{mate}\n" + "ACGT" * 40
                        + "\n+\n" + "I" * 160 + "\n")
    return first, second


def fake_idba(calls, content=">contig\nACGT\n", write_output=True):
    def run(argv, **kwargs):
        calls.append((list(map(str, argv)), kwargs))
        if argv[0] == TOOL and write_output:
            output = Path(kwargs["cwd"]) / "idba-out" / "contig.fa"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content)
        return subprocess.CompletedProcess(argv, 0)
    return run


def test_only_fixed_idba_ud_commands_are_invoked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_idba(calls))
    with WorkDir.using(tmp_path):
        output = adapter.assemble(first, second, None)
    assert len(calls) == 2
    assert calls[0][0] == [FQ2FA, "--merge", "--filter", str(first),
                          str(second), str(Path(calls[0][1]["cwd"]) / "idba-reads.fa")]
    assert calls[1][0] == [TOOL, "-r", calls[0][0][-1], "-o",
                          str(Path(calls[1][1]["cwd"]) / "idba-out")]
    assert output == Path(calls[1][1]["cwd"]) / "idba-out" / "contig.fa"
    assert output.read_text() == ">contig\nACGT\n"
    for _, kwargs in calls:
        assert kwargs["check"] is True
        assert kwargs["env"] is None
        assert kwargs["stdout"] is not None
    assert (Path(calls[0][1]["cwd"]) / "assembler.log").is_file()


def test_seeded_contigs_never_reach_the_command(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    seeds = tmp_path / "merged.csv"
    seeds.write_text("contig\nSECRET_TRUTH_CONTIG\n")
    plain, seeded = [], []
    monkeypatch.setattr(adapter.subprocess, "run", fake_idba(plain))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    monkeypatch.setattr(adapter.subprocess, "run", fake_idba(seeded))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, seeds)
    assert len(seeded) == len(plain) == 2
    command = " ".join(arg for argv, _ in seeded for arg in argv).lower()
    assert not any(banned in command for banned in BANNED)
    assert "SECRET_TRUTH_CONTIG" not in command


def test_zero_contig_assembly_is_a_valid_empty_fasta(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    monkeypatch.setattr(adapter.subprocess, "run", fake_idba([], content=""))
    with WorkDir.using(tmp_path):
        output = adapter.assemble(first, second, None)
    assert output.is_file()
    assert output.read_text() == ""


def test_missing_fasta_fails_closed(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    monkeypatch.setattr(adapter.subprocess, "run",
                        fake_idba([], write_output=False))
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
    monkeypatch.setattr(adapter.subprocess, "run", fake_idba(calls))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    assert calls[0][0][3:5] == [str(first), str(second)]


def test_clinical_denovo_uses_the_fixed_adapter(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_idba(calls))
    destination = tmp_path / "clinical-contigs.fasta"
    with WorkDir.using(tmp_path):
        denovo(first, second, destination)
    assert destination.read_text() == ">contig\nACGT\n"
    assert [argv[0] for argv, _ in calls] == [FQ2FA, TOOL]


def test_source_has_no_runtime_assembler_selector():
    root = Path(__file__).resolve().parents[2]
    for relative in ("micall/core/denovo.py", "micall/core/benchmark_assembler.py"):
        source = (root / relative).read_text()
        assert "MICALL_DENOVO_ASSEMBLER" not in source
        assert "os.environ" not in source
        assert "assembler_dispatch" not in source
