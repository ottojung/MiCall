"""Assembler branch tests: fixed command, paired input and failure behavior."""
from pathlib import Path
import subprocess
import pytest

from micall.core import denovo
from micall.core.benchmark_assembler import (
    SOAPDENOVO2_CONFIG,
    SOAPDENOVO2_PREFIX,
    assemble,
    soapdenovo2_config_text,
)
from micall.utils.work_dir import WorkDir


TOOL = "SOAPdenovo-63mer"


def sample_reads(tmp_path):
    first, second = tmp_path / "R1.fastq", tmp_path / "R2.fastq"
    for path, mate in ((first, 1), (second, 2)):
        path.write_text(f"@sample/{mate}\n" + "ACGT" * 40
                        + "\n+\n" + "I" * 160 + "\n")
    return first, second


def expected_output(work):
    return work / (SOAPDENOVO2_PREFIX + ".contig")


def write_output(work, content=">contig\nACGT\n"):
    output = expected_output(work)
    output.write_text(content)
    return output


def test_only_fixed_assembler_is_invoked(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(([str(a) for a in argv], kwargs))
        write_output(Path(kwargs["cwd"]))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        output = assemble(first, second, None)
    assert output.read_text() == ">contig\nACGT\n"
    assert len(calls) == 1
    argv, kwargs = calls[0]
    work = Path(kwargs["cwd"])
    assert argv == [
        TOOL, "all", "-s", str(work / SOAPDENOVO2_CONFIG), "-K", "63", "-R",
        "-o", str(work / SOAPDENOVO2_PREFIX),
    ]
    assert output == expected_output(work)
    assert kwargs["check"] is True
    assert kwargs["stdout"] is not None
    assert kwargs["stderr"] == subprocess.STDOUT
    assert kwargs["env"] is None
    assert work.is_dir()


def test_config_uses_only_validated_paired_fastq(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)
    seeds = tmp_path / "consensus.csv"
    seeds.write_text("contig\nACGTACGTACGT\n")
    configs = []

    def fake_run(argv, **kwargs):
        work = Path(kwargs["cwd"])
        configs.append((work / SOAPDENOVO2_CONFIG).read_text())
        write_output(work)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        assemble(first, second, seeds)
    assert len(configs) == 1
    text = configs[0]
    assert text == soapdenovo2_config_text(first, second)
    assert text.startswith("max_rd_len=251\n[LIB]\n")
    for key in ("avg_ins=200", "reverse_seq=0", "asm_flags=3",
                "rd_len_cutoff=251", "rank=1", "pair_num_cutoff=3",
                "map_len=32"):
        assert key + "\n" in text
    assert f"q1={first}\n" in text
    assert f"q2={second}\n" in text
    assert not any(line.startswith(("q=", "f1=", "f2=", "p=", "b="))
                   for line in text.splitlines())
    lowered = text.lower()
    for banned in ("reference", "--ref", "--seeds", "target", "hxb2",
                   "sra_run", "genome", "consensus.csv"):
        assert banned not in lowered


def test_zero_contig_empty_fasta_is_valid(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        write_output(Path(kwargs["cwd"]), "")

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path):
        output = assemble(first, second, None)
    assert output.is_file()
    assert output.read_text() == ""
    assert denovo.count_fasta_sequences(output) == 0


def test_missing_fasta_is_rejected(tmp_path, monkeypatch):
    first, second = sample_reads(tmp_path)

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr("micall.core.benchmark_assembler.subprocess.run", fake_run)
    with WorkDir.using(tmp_path), pytest.raises(
        RuntimeError, match="without the expected FASTA"
    ):
        assemble(first, second, None)


def test_denovo_bridge_uses_fixed_assembler_without_runtime_selector(tmp_path,
                                                                     monkeypatch):
    first, second = sample_reads(tmp_path)
    calls = []

    def fake_assemble(fastq1, fastq2, seeds):
        calls.append((fastq1, fastq2, seeds))
        output = tmp_path / "bridged.fasta"
        output.write_text(">contig\nACGT\n")
        return output

    monkeypatch.setattr("micall.core.benchmark_assembler.assemble", fake_assemble)
    monkeypatch.setenv("MICALL_DENOVO_ASSEMBLER", "spades")
    with WorkDir.using(tmp_path):
        result = denovo.run_subprocess.__wrapped__(first, second, None)
    assert result == tmp_path / "bridged.fasta"
    assert calls == [(first, second, None)]


def test_config_preserves_physical_251bp_mates(tmp_path):
    first, second = sample_reads(tmp_path)
    text = soapdenovo2_config_text(first, second)
    assert "max_rd_len=251\n" in text
    assert "rd_len_cutoff=251\n" in text
    assert "max_rd_len=100" not in text
    assert "q1=" + str(first) in text
    assert "q2=" + str(second) in text
