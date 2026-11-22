"""Source-committed MiCall adapter tests for exactly one NONQUALIFYING tool."""
import gzip
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from micall.core.assembler_commands import (
    ASSEMBLERS,
    BOTH_MATES,
    command_steps,
    fermi_lite_unitig_fastq,
)
from micall.core.assembler_dispatch import (
    convert_unitigs_to_fasta,
    run_external_assembler,
)
from micall.core.assembler_inputs import interleave_pairs
from micall.core.denovo import run_subprocess
from micall.utils.work_dir import WorkDir

TOOL = "fermi-lite"
# One authentic fml_utg_print record: '@id:id\tnsr\t<ovlp>\t<ovlp>', sequence,
# '+' and coverage-as-quality (all on single lines).
UNITIG_FASTQ = b"@0:1\t5\t2:3,41;\t.\nACGTACGTACGT\n+\nIIIIIIIIIIII\n"
UNITIG_FASTA = ">0:1\nACGTACGTACGT\n"


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
        assert all("--reference" not in a and "--seeds" not in a
                   for argv in steps for a in argv)


def test_fermi_lite_command_is_source_blind(tmp_path):
    first, second = _reads(tmp_path)
    steps, output = command_steps(TOOL, first, second, tmp_path)
    assert len(steps) == 1
    argv = steps[0]
    assert argv[0] == "/usr/local/bin/fml-asm"
    assert argv[1] == str(tmp_path / BOTH_MATES)
    # Exactly one input FASTQ: no reference, seed, truth or evaluator argument.
    assert len(argv) == 2
    flattened = " ".join(arg for step in steps for arg in step).lower()
    for banned in ("--reference", "--ref", "--seeds", "--targets",
                   "sra_run", "hxb2", "--genome", "truth", "evaluator"):
        assert banned not in flattened
    assert output.is_relative_to(tmp_path)
    with pytest.raises(ValueError, match="unsupported"):
        command_steps("benchmark-tuned", first, second, tmp_path)


def test_interleaved_mates_are_not_repeated_or_reordered(tmp_path):
    first, second, dest = (tmp_path / n for n in ("r1.gz", "r2.gz", "both.fq"))
    with gzip.open(first, "wt") as a:
        a.write(_fastq("first"))
        a.write(_fastq("third"))
    with gzip.open(second, "wt") as b:
        b.write(_fastq("second"))
        b.write(_fastq("fourth"))
    interleave_pairs(first, second, dest)
    assert dest.read_text() == "".join(
        _fastq(name) for name in ("first", "second", "third", "fourth")
    )
    assert dest.read_text().count("@first") == 1
    assert dest.read_text().count("@second") == 1


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
    with patch.dict(os.environ, {}, clear=True), patch(
        "micall.core.denovo.run_iva_subprocess",
        return_value=tmp_path / "iva/contigs.fasta",
    ) as old:
        assert run_subprocess(tmp_path / "r1", tmp_path / "r2", None).name == "contigs.fasta"
        old.assert_called_once()


def test_convert_unitigs_to_fasta_preserves_exact_sequences(tmp_path):
    unitigs, contigs = tmp_path / "u.fq", tmp_path / "c.fa"
    unitigs.write_bytes(UNITIG_FASTQ)
    convert_unitigs_to_fasta(unitigs, contigs)
    assert contigs.read_bytes() == UNITIG_FASTA.encode()


def test_convert_unitigs_to_fasta_emits_empty_fasta_for_zero_unitigs(tmp_path):
    unitigs, contigs = tmp_path / "empty.fq", tmp_path / "empty.fa"
    unitigs.write_bytes(b"")
    convert_unitigs_to_fasta(unitigs, contigs)
    assert contigs.is_file()
    assert contigs.read_bytes() == b""


@pytest.mark.parametrize("bad", [
    b"@0:1\t5\t.\t.\nACGT\n",                 # missing '+' and quality lines
    b"@0:1\t5\t.\t.\nACGT\n+\n",               # missing quality line
    b"0:1\nACGT\n+\nIIII\n",                    # header lacks '@'
    b"@\nACGT\n+\nIIII\n",                      # empty record id
    b"@0:1\t5\t.\t.\nACGT\n+\nIII\n",          # quality length differs
    b"@0:1\t5\t.\t.\n\n+\n\n",                  # empty sequence
    UNITIG_FASTQ + b"@1:0\t2\t.\t.\nACGT\n",   # trailing truncated record
])
def test_invalid_or_truncated_unitigs_never_become_empty_success(tmp_path, bad):
    unitigs, contigs = tmp_path / "bad.fq", tmp_path / "bad.fa"
    unitigs.write_bytes(bad)
    with pytest.raises(ValueError, match="invalid or truncated"):
        convert_unitigs_to_fasta(unitigs, contigs)
    assert not contigs.exists()
    assert not (tmp_path / "bad.fa.partial").exists()


def test_external_execution_converts_captured_unitigs_exactly(tmp_path):
    first, second = _reads(tmp_path)
    seen = []

    def fake_run(argv, **kwargs):
        seen.append((argv, kwargs))
        kwargs["stdout"].write(UNITIG_FASTQ)

    with WorkDir.using(tmp_path), patch(
        "micall.core.assembler_dispatch.subprocess.run", side_effect=fake_run
    ):
        output = run_external_assembler(TOOL, first, second)
    steps, expected = command_steps(TOOL, first, second, Path(seen[0][1]["cwd"]))
    assert output == expected
    assert output.read_bytes() == UNITIG_FASTA.encode()
    assert (output.parent / BOTH_MATES).read_text() == (
        _fastq("a") + _fastq("b")
    )
    assert fermi_lite_unitig_fastq(output.parent).is_file()
    assert len(seen) == len(steps)
    for (argv, kwargs), declared in zip(seen, steps):
        assert argv == declared
        assert kwargs["check"] is True
        assert kwargs["cwd"].is_dir()
        assert kwargs["env"] is None


def test_zero_unitig_assembly_is_a_valid_empty_fasta(tmp_path):
    first, second = _reads(tmp_path)

    def fake_run(argv, **kwargs):
        kwargs["stdout"].write(b"")

    with WorkDir.using(tmp_path), patch(
        "micall.core.assembler_dispatch.subprocess.run", side_effect=fake_run
    ):
        output = run_external_assembler(TOOL, first, second)
    assert output.is_file()
    assert output.read_bytes() == b""


def test_truncated_capture_fails_instead_of_fabricating_output(tmp_path):
    first, second = _reads(tmp_path)

    def fake_run(argv, **kwargs):
        kwargs["stdout"].write(b"@0:1\t5\t.\t.\nACGT\n")

    with WorkDir.using(tmp_path), patch(
        "micall.core.assembler_dispatch.subprocess.run", side_effect=fake_run
    ), pytest.raises(ValueError, match="invalid or truncated"):
        run_external_assembler(TOOL, first, second)


def test_failed_assembler_does_not_fabricate_success(tmp_path):
    from subprocess import CalledProcessError
    first, second = _reads(tmp_path)
    with WorkDir.using(tmp_path), patch(
        "micall.core.assembler_dispatch.subprocess.run",
        side_effect=CalledProcessError(7, [TOOL]),
    ), pytest.raises(CalledProcessError):
        run_external_assembler(TOOL, first, second)


def test_invalid_choice_never_executes_any_program(tmp_path):
    with patch.dict(os.environ, {"MICALL_DENOVO_ASSEMBLER": "unknown"}), \
            pytest.raises(ValueError, match="unsupported"):
        run_subprocess(tmp_path / "r1", tmp_path / "r2", None)


def test_dedicated_container_source_guards_are_consistent():
    """Prevent malformed image labels and impossible clinical-tree guard."""
    root = Path(__file__).resolve().parents[2]
    docker = (root / "Dockerfile.assembler-bench").read_text()
    builder = (root / "scripts/build_dedicated_assembler.sh").read_text()
    for var in ("MICALL_DENOVO_ASSEMBLER", "MICALL_FORK_SOURCE_COMMIT",
                "FORK_BASE_IMAGE", "MICALL_FORK_BASE_COMMIT",
                "TOOL_SOURCE_REPO", "TOOL_SOURCE_COMMIT",
                "TOOL_BINARY_SHA256", "TOOL_LICENSE_SHA256"):
        assert chr(36) + "{" + var + "}}" not in docker
    assert 'git diff --name-only "$baseline" HEAD' in builder
    assert '$baseline:micall' not in builder
    assert "downstream-changed: $path" in builder


def test_image_contains_exact_fork_adapter_modules_and_labels():
    root = Path(__file__).resolve().parents[2]
    docker = (root / "Dockerfile.assembler-bench").read_text()
    builder = (root / "scripts/build_dedicated_assembler.sh").read_text()
    for module in ("assembler_commands.py", "assembler_dispatch.py"):
        assert "COPY micall/core/" + module in docker
    for variable in ("MICALL_ADAPTER_COMMANDS_SHA256",
                     "MICALL_ADAPTER_DISPATCH_SHA256"):
        assert variable in docker and variable in builder
    assert "adapter-commands-sha256|$commands_sha" in builder
    assert "adapter-dispatch-sha256|$dispatch_sha" in builder
    assert "from micall.core.assembler_commands import ASSEMBLERS" in docker
    assert "tool-license|MIT" in builder
    assert "nonqualifying|true" in builder


def test_dedicated_source_and_license_pins_are_exact():
    root = Path(__file__).resolve().parents[2]
    docker = (root / "Dockerfile.assembler-bench").read_text()
    builder = (root / "scripts/build_dedicated_assembler.sh").read_text()
    assert (root / "assembler-bench/selected").read_text().strip() == TOOL
    assert (root / "assembler-bench/baseline-commit").read_text().strip() == (
        "eeca0381808a6e9ba5ef791c80238a0e2940abb0"
    )
    source_pin = "85f159e5a2e15a4c4fb41cdfce91ba0c9b68d2e1"
    license_pin = "e8051edd873472ad73df648dc7bf74d917d90057ae46bf6f3b021c4fff8069e8"
    # The guarded launcher pins both values; the Dockerfile consumes them as
    # build args rather than burying an uninspectable literal.
    assert source_pin in builder and license_pin in builder
    assert "ARG TOOL_SOURCE_COMMIT" in docker
    assert "ARG TOOL_LICENSE_SHA256" in docker
    assert "ARG TOOL_SOURCE_REPO" in docker
    assert "https://github.com/lh3/fermi-lite" in builder


def test_dedicated_image_packages_no_frozen_seven_tool():
    root = Path(__file__).resolve().parents[2]
    docker = (root / "Dockerfile.assembler-bench").read_text()
    for frozen in ("megahit", "abyss-pe", "spades.py", "velvetg",
                   "haploflow", "/usr/local/bin/ivanka"):
        assert frozen not in docker


def test_native_artifact_sha256_is_verified_inside_image():
    docker = (Path(__file__).resolve().parents[2] /
              "Dockerfile.assembler-bench").read_text()
    assert "sha256sum /usr/local/bin/fml-asm | cut" in docker
    assert "TOOL_BINARY_SHA256" in docker
