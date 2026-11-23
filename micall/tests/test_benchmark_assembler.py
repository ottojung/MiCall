"""Assembler branch tests: fixed command, paired input and failure behavior."""
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from micall.core import benchmark_assembler
from micall.core.benchmark_assembler import (
    ASSEMBLER,
    OUTPUT_NAME,
    TMP_NAME,
    assemble,
)
from micall.core.denovo import run_subprocess
from micall.utils.work_dir import WorkDir


TOOL = "penguin"


def sample_reads(tmp_path):
    first, second = tmp_path / "R1.fastq", tmp_path / "R2.fastq"
    for path, mate in ((first, 1), (second, 2)):
        path.write_text(f"@sample/{mate}\n" + "ACGT" * 40
                        + "\n+\n" + "I" * 160 + "\n")
    return first, second


def expected_output(work):
    return work / OUTPUT_NAME


def test_only_fixed_assembler_is_invoked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((list(map(str, argv)), kwargs))
        Path(argv[4]).write_text(">contig\nACGT\n")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    # No runtime selector: an inherited env var must not change the tool.
    monkeypatch.setenv("MICALL_DENOVO_ASSEMBLER", "a-different-assembler")
    with WorkDir.using(tmp_path):
        output = assemble(first, second, None)
    assert output.read_text() == ">contig\nACGT\n"
    assert len(calls) == 1
    argv, kwargs = calls[0]
    work = Path(kwargs["cwd"])
    assert argv == [ASSEMBLER, "nuclassemble", str(first), str(second),
                    str(expected_output(work)), str(work / TMP_NAME)]
    assert kwargs["check"] is True
    assert kwargs["env"] is None
    assert kwargs["stdout"] is not None


def test_reference_blind_paired_fastq_is_passed_directly(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    observed = []

    def fake_run(argv, **kwargs):
        observed.extend(map(str, argv))
        Path(argv[4]).write_text(">contig\nACGT\n")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        assemble(first, second, tmp_path / "consensus.csv")
    assert observed[0] == "penguin"
    assert observed[1] == "nuclassemble"
    assert str(first) in observed and str(second) in observed
    assert observed.index(str(first)) < observed.index(str(second))
    # No seed, reference, truth or evaluator argument is constructed.
    assert all(str(tmp_path / "consensus.csv") != arg for arg in observed)
    for banned in ("--reference", "--ref", "--seeds", "--targets",
                   "sra_run", "hxb2", "--genome", "truth", "evaluator"):
        assert banned not in " ".join(observed).lower()


def test_zero_contig_assembly_is_a_valid_empty_fasta(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        Path(argv[4]).write_text("")

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        output = assemble(first, second, None)
    assert output.is_file()
    assert output.read_text() == ""
    assert sum(1 for line in output.read_text().splitlines()
               if line.startswith(">")) == 0


def test_missing_fasta_is_rejected(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path), pytest.raises(
        RuntimeError, match="without the expected FASTA"
    ):
        assemble(first, second, None)


def test_failed_assembler_does_not_fabricate_success(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        raise subprocess.CalledProcessError(7, argv)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path), pytest.raises(subprocess.CalledProcessError):
        assemble(first, second, None)


def test_denovo_bridge_calls_only_the_fixed_assembler(tmp_path):
    first, second = sample_reads(tmp_path)
    with patch.object(benchmark_assembler, "assemble",
                      return_value=tmp_path / "contigs.fasta") as fixed, \
            patch.dict("os.environ", {"MICALL_DENOVO_ASSEMBLER": "other"}):
        result = run_subprocess(first, second, None)
    assert result == tmp_path / "contigs.fasta"
    fixed.assert_called_once_with(first, second, None)


def test_no_runtime_selector_or_reference_module_in_source():
    root = Path(__file__).resolve().parents[1]
    denovo = (root / "core" / "denovo.py").read_text()
    adapter = (root / "core" / "benchmark_assembler.py").read_text()
    assert "assembler_dispatch" not in denovo
    assert "os.environ" not in denovo
    assert "MICALL_DENOVO_ASSEMBLER" not in denovo
    assert "assembler_dispatch" not in adapter
    assert "os.environ" not in adapter
    assert 'ASSEMBLER = "penguin"' in adapter
