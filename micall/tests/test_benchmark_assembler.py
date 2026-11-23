"""Assembler branch tests: fixed command, paired input and failure behavior."""
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from micall.core import benchmark_assembler
from micall.core.benchmark_assembler import (
    ASSEMBLER,
    BOTH_MATES,
    CONTIGS_FASTA,
    UNITIG_FASTQ,
    assemble,
    convert_unitigs_to_fasta,
    interleave_pairs,
)
from micall.core.denovo import run_subprocess
from micall.utils.work_dir import WorkDir


TOOL = "fermi-lite"
# One authentic fml_utg_print record: '@id:id\tnsr\t<ovlp>\t<ovlp>', sequence,
# '+' and coverage-as-quality (all on single lines).
UNITIG_FASTQ_RECORD = b"@0:1\t5\t2:3,41;\t.\nACGTACGTACGT\n+\nIIIIIIIIIIII\n"
UNITIG_FASTA_RECORD = ">0:1\nACGTACGTACGT\n"


def sample_reads(tmp_path):
    first, second = tmp_path / "R1.fastq", tmp_path / "R2.fastq"
    for path, mate in ((first, 1), (second, 2)):
        path.write_text(f"@sample/{mate}\n" + "ACGT" * 40
                        + "\n+\n" + "I" * 160 + "\n")
    return first, second


def expected_output(work):
    return work / CONTIGS_FASTA


def test_only_fixed_assembler_is_invoked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((list(map(str, argv)), kwargs))
        kwargs["stdout"].write(UNITIG_FASTQ_RECORD)
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    # No runtime selector: an inherited env var must not change the tool.
    monkeypatch.setenv("MICALL_DENOVO_ASSEMBLER", "a-different-assembler")
    with WorkDir.using(tmp_path):
        output = assemble(first, second, None)
    assert output.read_text() == UNITIG_FASTA_RECORD
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[0] == ASSEMBLER
    assert argv[1].endswith(BOTH_MATES)
    assert kwargs["check"] is True
    assert kwargs["env"] is None
    assert kwargs["stdout"] is not None


def test_reference_blind_paired_fastq_is_interleaved(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    observed = []

    def fake_run(argv, **kwargs):
        observed.extend(map(str, argv))
        kwargs["stdout"].write(b"")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        output = assemble(first, second, tmp_path / "consensus.csv")
    # Exactly one input FASTQ: no reference, seed, truth or evaluator argument.
    assert observed == [ASSEMBLER, observed[1]]
    assert observed[1].endswith(BOTH_MATES)
    for banned in ("--reference", "--ref", "--seeds", "--targets",
                   "sra_run", "hxb2", "--genome", "truth", "evaluator"):
        assert banned not in " ".join(observed).lower()
    both_mates = Path(observed[1]).read_text()
    assert both_mates.count("@sample/1") == 1
    assert both_mates.count("@sample/2") == 1
    assert both_mates.index("@sample/1") < both_mates.index("@sample/2")
    assert output.read_bytes() == b""


def test_interleave_refuses_unequal_mates(tmp_path):
    first, second = tmp_path / "r1.fastq", tmp_path / "r2.fastq"
    first.write_text("@a\nACGT\n+\nIIII\n@b\nACGT\n+\nIIII\n")
    second.write_text("@c\nACGT\n+\nIIII\n")
    with pytest.raises(ValueError, match="unequal FASTQ mate counts"):
        interleave_pairs(first, second, tmp_path / "both.fastq")


def test_convert_unitigs_to_fasta_preserves_exact_sequences(tmp_path):
    unitigs, contigs = tmp_path / UNITIG_FASTQ, tmp_path / "c.fa"
    unitigs.write_bytes(UNITIG_FASTQ_RECORD)
    convert_unitigs_to_fasta(unitigs, contigs)
    assert contigs.read_bytes() == UNITIG_FASTA_RECORD.encode()


def test_zero_unitig_assembly_is_a_valid_empty_fasta(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        kwargs["stdout"].write(b"")

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        output = assemble(first, second, None)
    assert output.is_file()
    assert output.read_bytes() == b""


@pytest.mark.parametrize("bad", [
    b"@0:1\t5\t.\t.\nACGT\n",                  # missing '+' and quality lines
    b"@0:1\t5\t.\t.\nACGT\n+\n",                # missing quality line
    b"0:1\nACGT\n+\nIIII\n",                    # header lacks '@'
    b"@\nACGT\n+\nIIII\n",                      # empty record id
    b"@0:1\t5\t.\t.\nACGT\n+\nIII\n",          # quality length differs
    b"@0:1\t5\t.\t.\n\n+\n\n",                  # empty sequence
    UNITIG_FASTQ_RECORD + b"@1:0\t2\t.\t.\nACGT\n",  # truncated trailing record
])
def test_invalid_or_truncated_unitigs_never_become_empty_success(tmp_path, bad):
    unitigs, contigs = tmp_path / "bad.fq", tmp_path / "bad.fa"
    unitigs.write_bytes(bad)
    with pytest.raises(ValueError, match="invalid or truncated"):
        convert_unitigs_to_fasta(unitigs, contigs)
    assert not contigs.exists()
    assert not (tmp_path / "bad.fa.partial").exists()


def test_missing_fasta_is_rejected(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        kwargs["stdout"].write(UNITIG_FASTQ_RECORD)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    # Simulate a conversion that creates no FASTA at all.
    monkeypatch.setattr("micall.core.benchmark_assembler.convert_unitigs_to_fasta",
                        lambda unitigs, contigs: None)
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
    assert 'ASSEMBLER = "/usr/local/bin/fml-asm"' in adapter
