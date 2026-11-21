"""Source-committed MiCall adapter tests for exactly one NONQUALIFYING tool."""
import gzip
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from micall.core.assembler_commands import ASSEMBLERS, command_steps
from micall.core.assembler_dispatch import run_external_assembler
from micall.core.assembler_inputs import interleave_pairs
from micall.core.denovo import run_subprocess
from micall.utils.work_dir import WorkDir

TOOL = "unicycler"
INTERLEAVE = False


def _fastq(name):
    return f"@{name}\nACGT\n+\nIIII\n"


def _reads(tmp_path):
    first, second = tmp_path/"r1.fastq", tmp_path/"r2.fastq"
    first.write_text(_fastq("a"))
    second.write_text(_fastq("b"))
    return first, second


def test_every_supported_external_has_explicit_known_output(tmp_path):
    first, second = _reads(tmp_path)
    for name in ASSEMBLERS:
        if name == "iva":
            continue
        steps, output = command_steps(name, first, second, tmp_path)
        assert steps and output.is_relative_to(tmp_path)
        assert all(isinstance(argv, list) and argv for argv in steps)
        assert all("--reference" not in a and "--seeds" not in a
                   for argv in steps for a in argv)
    steps, out = command_steps(TOOL, first, second, tmp_path)
    assert out.name == "assembly.fasta"
    with pytest.raises(ValueError, match="unsupported"):
        command_steps("benchmark-tuned", first, second, tmp_path)


def test_tool_command_is_reference_blind(tmp_path):
    first, second = _reads(tmp_path)
    steps, output = command_steps(TOOL, first, second, tmp_path)
    argv = " ".join(arg for step in steps for arg in step).lower()
    for banned in ("--reference", "--ref", "--seeds", "--targets",
                   "sra_run", "hxb2", "--genome"):
        assert banned not in argv
    if INTERLEAVE:
        assert "both_mates.fastq" in argv
    else:
        assert str(first) in argv and str(second) in argv
    assert output.is_relative_to(tmp_path)
    with pytest.raises(ValueError, match="unsupported"):
        command_steps("benchmark-tuned", first, second, tmp_path)


def test_interleave_refuses_truncation(tmp_path):
    first, second, dest = (tmp_path/n for n in ("r1.gz", "r2.gz", "both.fq"))
    with gzip.open(first, "wt") as a:
        a.write(_fastq("first"))
    with gzip.open(second, "wt") as b:
        b.write(_fastq("second"))
    interleave_pairs(first, second, dest)
    assert dest.read_text() == _fastq("first") + _fastq("second")
    with gzip.open(second, "wt") as b:
        b.write("")
    with pytest.raises(ValueError, match="unequal"):
        interleave_pairs(first, second, tmp_path/"bad.fq")


def test_default_iva_uses_original_subprocess(tmp_path):
    with patch.dict(os.environ, {}, clear=True), patch(
        "micall.core.denovo.run_iva_subprocess",
        return_value=tmp_path/"iva/contigs.fasta",
    ) as old:
        assert run_subprocess(tmp_path/"r1", tmp_path/"r2", None).name == "contigs.fasta"
        old.assert_called_once()


def test_external_execution_respects_invariant_argv_and_env(tmp_path):
    first, second = _reads(tmp_path)
    steps, expected = command_steps(TOOL, first, second, tmp_path)
    seen = []

    def fake_run(argv, **kwargs):
        seen.append((argv, kwargs))
        _, real_output = command_steps(TOOL, first, second, Path(kwargs["cwd"]))
        real_output.parent.mkdir(parents=True, exist_ok=True)
        real_output.write_text(">contig\nACGT\n")

    with WorkDir.using(tmp_path), patch(
        "micall.core.assembler_dispatch.subprocess.run", side_effect=fake_run
    ):
        output = run_external_assembler(TOOL, first, second)
    assert output.read_text().startswith(">contig")
    assert len(seen) == len(steps)
    for (argv, kwargs), declared in zip(seen, steps):
        assert argv[0] == declared[0]
        assert kwargs["check"] is True
        assert kwargs["cwd"].is_dir()
        assert kwargs["env"] is None

    # Upstream writes assembly.fasta even when zero contigs pass its minimum
    # length; a present empty FASTA is a legitimate zero-contig result.
    def fake_zero_contigs(argv, **kwargs):
        _, real_output = command_steps(TOOL, first, second, Path(kwargs["cwd"]))
        real_output.parent.mkdir(parents=True, exist_ok=True)
        real_output.write_text("")

    zero_dir = tmp_path/"zero"
    zero_dir.mkdir()
    with WorkDir.using(zero_dir), patch(
        "micall.core.assembler_dispatch.subprocess.run",
        side_effect=fake_zero_contigs,
    ):
        zero_output = run_external_assembler(TOOL, first, second)
    assert zero_output.is_file()
    assert zero_output.read_text() == ""


def test_failed_assembler_does_not_fabricate_success(tmp_path):
    from subprocess import CalledProcessError
    first, second = _reads(tmp_path)
    with WorkDir.using(tmp_path), patch(
        "micall.core.assembler_dispatch.subprocess.run",
        side_effect=CalledProcessError(7, [TOOL]),
    ):
        with pytest.raises(CalledProcessError):
            run_external_assembler(TOOL, first, second)


def test_invalid_choice_never_executes_any_program(tmp_path):
    with patch.dict(os.environ, {"MICALL_DENOVO_ASSEMBLER": "unknown"}):
        with pytest.raises(ValueError, match="unsupported"):
            run_subprocess(tmp_path/"r1", tmp_path/"r2", None)
