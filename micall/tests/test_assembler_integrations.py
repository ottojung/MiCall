"""Source-committed MiCall assembler choices, never runtime code patches."""
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


def _fastq(name):
    return f"@{name}\nACGT\n+\nIIII\n"


def test_every_supported_external_has_explicit_known_output(tmp_path):
    left, right = tmp_path/"r1.fastq.gz", tmp_path/"r2.fastq.gz"
    for name in ASSEMBLERS:
        if name == "iva":
            continue
        steps, output = command_steps(name, left, right, tmp_path)
        assert steps and output.is_relative_to(tmp_path)
        assert all(isinstance(argv, list) and argv for argv in steps)
        assert all("--reference" not in a and "--seeds" not in a
                   for argv in steps for a in argv)
    steps, out = command_steps("ivanka", left, right, tmp_path)
    assert steps == [["/usr/local/bin/ivanka", "--reads1", str(left),
                      "--reads2", str(right), "--output", str(out)]]
    with pytest.raises(ValueError, match="unsupported"):
        command_steps("benchmark-tuned", left, right, tmp_path)


def test_abyss_builds_only_consumed_contig_target(tmp_path):
    first, second = tmp_path/"r1.fastq", tmp_path/"r2.fastq"
    steps, output = command_steps("abyss", first, second, tmp_path)
    assert output == tmp_path/"assembly-contigs.fa"
    assert len(steps) == 1
    assert steps[0][0] == "abyss-pe"
    assert steps[0][-1] == output.name
    assert "scaffolds" not in " ".join(steps[0])


def test_haploflow_consumes_both_mates_in_order(tmp_path):
    first, second, dest = (tmp_path/name for name in ("r1.gz", "r2.gz", "both.fq"))
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
    left, right = tmp_path/"r1.fastq", tmp_path/"r2.fastq"
    left.write_text(_fastq("a"))
    right.write_text(_fastq("b"))
    seen = []
    def fake_run(argv, **kwargs):
        seen.append((argv, kwargs))
        Path(argv[-1]).write_text(">contig\nACGT\n")
    with WorkDir.using(tmp_path), patch(
        "micall.core.assembler_dispatch.subprocess.run", side_effect=fake_run
    ):
        output = run_external_assembler("ivanka", left, right)
    assert output.read_text().startswith(">contig")
    assert len(seen) == 1
    argv, kwargs = seen[0]
    assert argv == ["/usr/local/bin/ivanka", "--reads1", str(left),
                    "--reads2", str(right), "--output", str(output)]
    assert kwargs["env"] == {}
    assert kwargs["check"] is True
    assert kwargs["cwd"].is_dir()


def test_failed_assembler_does_not_fabricate_success(tmp_path):
    from subprocess import CalledProcessError
    left, right = tmp_path/"r1", tmp_path/"r2"
    with WorkDir.using(tmp_path):
        with patch("micall.core.assembler_dispatch.subprocess.run",
                   side_effect=CalledProcessError(7, ["megahit"])):
            with pytest.raises(CalledProcessError):
                run_external_assembler("megahit", left, right)


def test_invalid_choice_never_executes_any_program(tmp_path):
    with patch.dict(os.environ, {"MICALL_DENOVO_ASSEMBLER": "unknown"}):
        with pytest.raises(ValueError, match="unsupported"):
            run_subprocess(tmp_path/"r1", tmp_path/"r2", None)
