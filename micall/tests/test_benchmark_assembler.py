"""Ray adapter tests: fixed, reference-blind command on exact paired reads."""
from pathlib import Path
import gzip
import subprocess

import pytest

from micall.core import benchmark_assembler as adapter
from micall.core.denovo import denovo
from micall.utils.work_dir import WorkDir


MPIEXEC = "mpiexec"
TOOL = "Ray"
BANNED = ("--seeds", "--sra_run", "--targets", "--reference", "--ref",
          "--genome")


def sample_reads(tmp_path):
    first, second = tmp_path / "R1.fastq", tmp_path / "R2.fastq"
    for path, mate in ((first, 1), (second, 2)):
        path.write_text(f"@sample/{mate}\n" + "ACGT" * 40
                        + "\n+\n" + "I" * 160 + "\n")
    return first, second


def fake_ray(calls, content=">contig\nACGT\n", write_output=True):
    def run(argv, **kwargs):
        calls.append((list(map(str, argv)), kwargs))
        if write_output:
            output = Path(kwargs["cwd"]) / "ray-out" / adapter.CONTIGS_FASTA
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content)
        return subprocess.CompletedProcess(argv, 0)
    return run


def test_only_fixed_ray_command_is_invoked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_ray(calls))
    with WorkDir.using(tmp_path):
        output = adapter.assemble(first, second, None)
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv == [MPIEXEC, "-n", "2", TOOL, "-k31", "-p", str(first),
                    str(second), "-o", str(Path(kwargs["cwd"]) / "ray-out")]
    assert output == Path(kwargs["cwd"]) / "ray-out" / adapter.CONTIGS_FASTA
    assert output.read_text() == ">contig\nACGT\n"
    assert kwargs["check"] is True
    assert kwargs["env"] is None
    assert kwargs["stdout"] is not None
    assert (Path(kwargs["cwd"]) / "assembler.log").is_file()


def test_both_mates_are_consumed_in_order(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_ray(calls))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    assert calls[0][0][6:8] == [str(first), str(second)]


def test_gzipped_mates_are_passed_verbatim(tmp_path, monkeypatch):
    first, second = tmp_path / "R1.fastq.gz", tmp_path / "R2.fastq.gz"
    with gzip.open(first, "wt") as out:
        out.write("@r1/1\nACGT\n+\nIIII\n")
    with gzip.open(second, "wt") as out:
        out.write("@r1/2\nACGT\n+\nIIII\n")
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_ray(calls))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    assert calls[0][0][6:8] == [str(first), str(second)]


def test_seeded_contigs_never_reach_the_command(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    seeds = tmp_path / "merged.csv"
    seeds.write_text("contig\nSECRET_TRUTH_CONTIG\n")
    plain, seeded = [], []
    monkeypatch.setattr(adapter.subprocess, "run", fake_ray(plain))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    monkeypatch.setattr(adapter.subprocess, "run", fake_ray(seeded))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, seeds)

    def without_workdir(argv):
        return [arg.replace(str(Path(argv[-1]).parent), "<work>") for arg in argv]

    assert without_workdir(seeded[0][0]) == without_workdir(plain[0][0])
    command = " ".join(seeded[0][0]).lower()
    assert not any(banned in command for banned in BANNED)
    assert "SECRET_TRUTH_CONTIG" not in command


def test_zero_contig_assembly_is_a_valid_empty_fasta(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    monkeypatch.setattr(adapter.subprocess, "run", fake_ray([], content=""))
    with WorkDir.using(tmp_path):
        output = adapter.assemble(first, second, None)
    assert output.is_file()
    assert output.read_text() == ""


def test_missing_fasta_fails_closed(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    monkeypatch.setattr(adapter.subprocess, "run",
                        fake_ray([], write_output=False))
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
    monkeypatch.setattr(adapter.subprocess, "run", fake_ray(calls))
    destination = tmp_path / "clinical-contigs.fasta"
    with WorkDir.using(tmp_path):
        denovo(first, second, destination)
    assert destination.read_text() == ">contig\nACGT\n"
    assert len(calls) == 1
    assert calls[0][0][0:4] == [MPIEXEC, "-n", "2", TOOL]


def test_source_has_no_runtime_assembler_selector():
    root = Path(__file__).resolve().parents[2]
    for relative in ("micall/core/denovo.py", "micall/core/benchmark_assembler.py"):
        source = (root / relative).read_text()
        assert "MICALL_DENOVO_ASSEMBLER" not in source
        assert "os.environ" not in source
        assert "assembler_dispatch" not in source


def test_source_recovery_recipe_is_source_attested(tmp_path, monkeypatch):
    """The documented Ray native recovery stays bound to the audited pins."""
    doc = (Path(__file__).resolve().parents[2] / "assembler-bench"
           / "RAY_SOURCE_RECOVERY.md").read_text()
    for expected in (
        "621dfe8454dc96d49f405e413cb759d3f48790b2",
        "c8d9fe2e1347be299f2e74dd8a0fc278b5a02e16",
        "fc24be5a854af6d2669d9db7f02fdbaf1bab72d16089362fa39f3169666e4956",
        "a9d8d325805dbe2d92390a3f74e310bd92fbfcf1e07c038a42fdc304788d76ee",
        "068ee2b85bfcb7be592b1fd718dcf8f115e0b544d7d28aabf97e9f0f21edf9a2",
        "b119603aee2856331824749bc9f46819056c305c390a83ce18b86a5c0d31cf5d",
        'test "$(readlink /src/ray/RayPlatform)" = "../RayPlatform"',
    ):
        assert expected in doc
    # The runtime adapter is unchanged by this documentation-only fix.
    first, second = sample_reads(tmp_path)
    calls = []
    monkeypatch.setattr(adapter.subprocess, "run", fake_ray(calls))
    with WorkDir.using(tmp_path):
        adapter.assemble(first, second, None)
    assert calls[0][0] == [MPIEXEC, "-n", "2", TOOL, "-k31", "-p",
                           str(first), str(second), "-o",
                           str(Path(calls[0][1]["cwd"]) / "ray-out")]
