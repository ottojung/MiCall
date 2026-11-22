"""Source-committed MiCall adapter tests for exactly one NONQUALIFYING tool."""

import gzip
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from micall.core.assembler_commands import (
    ASSEMBLERS,
    command_steps,
    soapdenovo2_config_text,
    write_soapdenovo2_config,
)
from micall.core.assembler_dispatch import run_external_assembler
from micall.core.assembler_inputs import interleave_pairs
from micall.core.denovo import run_subprocess
from micall.utils.work_dir import WorkDir

TOOL = "soapdenovo2"


def _fastq(name):
    return f"@{name}\nACGT\n+\nIIII\n"


def _reads(tmp_path):
    first, second = tmp_path / "r1.fastq", tmp_path / "r2.fastq"
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
        assert all(
            "--reference" not in a and "--seeds" not in a
            for argv in steps
            for a in argv
        )


def test_soapdenovo2_command_labels_and_source_blind_argv(tmp_path):
    first, second = _reads(tmp_path)
    steps, output = command_steps(TOOL, first, second, tmp_path)
    assert len(steps) == 1
    argv = steps[0]
    assert argv[0] == "SOAPdenovo-63mer"
    assert argv[1] == "all"
    assert argv[argv.index("-K") + 1] == "63"
    assert "-R" in argv
    assert argv[argv.index("-s") + 1] == str(tmp_path / "soapdenovo2.config")
    assert argv[argv.index("-o") + 1] == str(tmp_path / "soapdenovo2_graph")
    assert output == tmp_path / "soapdenovo2_graph.contig"
    joined = " ".join(argv).lower()
    for banned in (
        "--reference",
        "--ref",
        "--seeds",
        "--targets",
        "sra_run",
        "hxb2",
        "--genome",
        "--contigs",
    ):
        assert banned not in joined
    with pytest.raises(ValueError, match="unsupported"):
        command_steps("benchmark-tuned", first, second, tmp_path)


def test_soapdenovo2_config_generation_uses_both_validated_mates(tmp_path):
    first, second = _reads(tmp_path)
    config = write_soapdenovo2_config(first, second, tmp_path)
    text = config.read_text()
    assert config == tmp_path / "soapdenovo2.config"
    assert text.startswith("max_rd_len=100\n[LIB]\n")
    for key in (
        "avg_ins=200",
        "reverse_seq=0",
        "asm_flags=3",
        "rd_len_cutoff=100",
        "rank=1",
        "pair_num_cutoff=3",
        "map_len=32",
    ):
        assert key + "\n" in text
    assert f"q1={first}\n" in text
    assert f"q2={second}\n" in text
    assert not any(
        line.startswith(("q=", "f1=", "f2=", "p=", "b=")) for line in text.splitlines()
    )
    assert f"q1={first}\n" in soapdenovo2_config_text(str(first), str(second))


def test_interleave_refuses_truncation(tmp_path):
    first, second, dest = (tmp_path / n for n in ("r1.gz", "r2.gz", "both.fq"))
    with gzip.open(first, "wt") as a:
        a.write(_fastq("first"))
    with gzip.open(second, "wt") as b:
        b.write(_fastq("second"))
    interleave_pairs(first, second, dest)
    assert dest.read_text() == _fastq("first") + _fastq("second")
    with gzip.open(second, "wt") as b:
        b.write("")
    with pytest.raises(ValueError, match="unequal"):
        interleave_pairs(first, second, tmp_path / "bad.fq")


def test_default_iva_uses_original_subprocess(tmp_path):
    with (
        patch.dict(os.environ, {}, clear=True),
        patch(
            "micall.core.denovo.run_iva_subprocess",
            return_value=tmp_path / "iva/contigs.fasta",
        ) as old,
    ):
        assert (
            run_subprocess(tmp_path / "r1", tmp_path / "r2", None).name
            == "contigs.fasta"
        )
        old.assert_called_once()


def test_external_execution_respects_invariant_argv_and_env(tmp_path):
    first, second = _reads(tmp_path)
    steps, _ = command_steps(TOOL, first, second, tmp_path)
    seen = []
    configs = []

    def fake_run(argv, **kwargs):
        seen.append((argv, kwargs))
        workspace = Path(kwargs["cwd"])
        configs.append((workspace / "soapdenovo2.config").read_text())
        _, real_output = command_steps(TOOL, first, second, workspace)
        real_output.parent.mkdir(parents=True, exist_ok=True)
        real_output.write_text(">contig\nACGT\n")

    with (
        WorkDir.using(tmp_path),
        patch("micall.core.assembler_dispatch.subprocess.run", side_effect=fake_run),
    ):
        output = run_external_assembler(TOOL, first, second)
    assert output.read_text().startswith(">contig")
    assert len(seen) == len(steps)
    for argv, kwargs in seen:
        workspace = Path(kwargs["cwd"])
        declared, _ = command_steps(TOOL, first, second, workspace)
        assert argv == declared[0]
        assert kwargs["check"] is True
        assert kwargs["cwd"].is_dir()
        assert kwargs["env"] is None
    assert f"q1={first}\n" in configs[0]
    assert f"q2={second}\n" in configs[0]


def test_soapdenovo2_zero_native_contig_is_valid_empty_fasta(tmp_path):
    first, second = _reads(tmp_path)

    def fake_run(argv, **kwargs):
        _, real_output = command_steps(TOOL, first, second, Path(kwargs["cwd"]))
        real_output.parent.mkdir(parents=True, exist_ok=True)
        real_output.write_text("")  # true success, zero native contigs

    with (
        WorkDir.using(tmp_path),
        patch("micall.core.assembler_dispatch.subprocess.run", side_effect=fake_run),
    ):
        output = run_external_assembler(TOOL, first, second)
    assert output.is_file()
    assert output.name.endswith(".contig")
    assert output.read_text() == ""


def test_failed_assembler_does_not_fabricate_success(tmp_path):
    from subprocess import CalledProcessError

    first, second = _reads(tmp_path)
    with (
        WorkDir.using(tmp_path),
        patch(
            "micall.core.assembler_dispatch.subprocess.run",
            side_effect=CalledProcessError(7, [TOOL]),
        ),
        pytest.raises(CalledProcessError),
    ):
        run_external_assembler(TOOL, first, second)


def test_missing_native_contig_on_success_fails_closed(tmp_path):
    first, second = _reads(tmp_path)
    with (
        WorkDir.using(tmp_path),
        patch("micall.core.assembler_dispatch.subprocess.run", return_value=None),
        pytest.raises(RuntimeError, match="no contigs FASTA"),
    ):
        run_external_assembler(TOOL, first, second)


def test_invalid_choice_never_executes_any_program(tmp_path):
    with (
        patch.dict(os.environ, {"MICALL_DENOVO_ASSEMBLER": "unknown"}),
        pytest.raises(ValueError, match="unsupported"),
    ):
        run_subprocess(tmp_path / "r1", tmp_path / "r2", None)


def test_dedicated_container_source_guards_are_consistent():
    """Prevent malformed image labels and impossible clinical-tree guard."""
    root = Path(__file__).resolve().parents[2]
    docker = (root / "Dockerfile.assembler-bench").read_text()
    builder = (root / "scripts/build_dedicated_assembler.sh").read_text()
    for var in (
        "MICALL_DENOVO_ASSEMBLER",
        "MICALL_FORK_SOURCE_COMMIT",
        "FORK_BASE_IMAGE",
        "MICALL_FORK_BASE_COMMIT",
        "TOOL_SOURCE_REPO",
        "TOOL_SOURCE_COMMIT",
        "TOOL_BINARY_SHA256",
    ):
        assert chr(36) + "{" + var + "}}" not in docker
    assert 'git diff --name-only "$baseline" HEAD' in builder
    assert "$baseline:micall" not in builder
    assert "downstream-changed: $path" in builder
    assert "7560c0b9d59e253cb0c819eca40d60f8636b4a11" in builder
    assert "https://github.com/aquaskyline/SOAPdenovo2" in builder


def test_image_contains_exact_fork_adapter_modules_and_labels():
    root = Path(__file__).resolve().parents[2]
    docker = (root / "Dockerfile.assembler-bench").read_text()
    builder = (root / "scripts/build_dedicated_assembler.sh").read_text()
    for module in ("assembler_commands.py", "assembler_dispatch.py"):
        assert "COPY micall/core/" + module in docker
    for variable in (
        "MICALL_ADAPTER_COMMANDS_SHA256",
        "MICALL_ADAPTER_DISPATCH_SHA256",
    ):
        assert variable in docker and variable in builder
    assert "adapter-commands-sha256|$commands_sha" in builder
    assert "adapter-dispatch-sha256|$dispatch_sha" in builder
    assert "from micall.core.assembler_commands import ASSEMBLERS" in docker
    assert "org.ottojung.exploratory.tool-license|GPL-3.0" in builder
