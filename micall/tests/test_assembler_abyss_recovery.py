"""ABySS graph recovery is permitted only for proven no-link DistanceEst."""
import gzip
from pathlib import Path

import pytest

from micall.core.assembler_abyss_recovery import no_alignment, recover


def fixture(work, *, alignment=False, failure=True):
    (work / "assembly-3.fa").write_text(">graph1\nACGTNACGT\n>graph2\nTTTTACGT\n")
    if failure:
        (work / "assembler.log").write_bytes(
            b"DistanceEst.cpp:669: int main(int, char**): Assertion `in' failed.\n")
    else:
        (work / "assembler.log").write_bytes(b"unrelated error\n")
    with gzip.open(work / "assembly-3.sam.gz", "wt") as output:
        output.write("@HD\tVN:1.4\n@SQ\tSN:graph1\tLN:9\n")
        if alignment:
            output.write("read1\t0\tgraph1\t1\t60\t9M\t*\t0\t0\tACGTNACGT\tIIIIIIIII\n")


def test_graph_is_recovered_only_after_empty_sam_distanceest_failure(tmp_path):
    fixture(tmp_path)
    output = tmp_path / "assembly-contigs.fa"
    assert no_alignment(tmp_path / "assembly-3.sam.gz")
    assert recover(tmp_path, output)
    assert output.read_text() == (tmp_path / "assembly-3.fa").read_text()
    assert b"NO_PAIRED_ALIGNMENTS" in (tmp_path / "assembler.log").read_bytes()


@pytest.mark.parametrize("change", ("aligned", "unrelated", "missing_sam",
                                    "broken_gzip", "empty_graph",
                                    "incomplete_fasta", "prior_output"))
def test_fail_closed_when_other_error_or_no_graph_provenance(tmp_path, change):
    fixture(tmp_path, alignment=(change == "aligned"),
            failure=(change != "unrelated"))
    output = tmp_path / "assembly-contigs.fa"
    if change == "missing_sam":
        (tmp_path / "assembly-3.sam.gz").unlink()
    elif change == "broken_gzip":
        (tmp_path / "assembly-3.sam.gz").write_bytes(b"broken")
    elif change == "empty_graph":
        (tmp_path / "assembly-3.fa").write_text("")
    elif change == "incomplete_fasta":
        (tmp_path / "assembly-3.fa").write_text(">missing\n")
    elif change == "prior_output":
        output.write_text(">prior\nACGT\n")
    assert not recover(tmp_path, output)


def test_missing_sam_reference_records_is_not_proof(tmp_path):
    fixture(tmp_path)
    with gzip.open(tmp_path / "assembly-3.sam.gz", "wt") as output:
        output.write("@HD\tVN:1.4\n")
    assert not recover(tmp_path, tmp_path / "assembly-contigs.fa")


def test_dispatch_uses_graph_only_when_abyss_command_errors(tmp_path, monkeypatch):
    from subprocess import CalledProcessError
    from micall.core.assembler_dispatch import run_external_assembler
    from micall.utils.work_dir import WorkDir
    from unittest.mock import patch

    def abort(*args, **kwargs):
        fixture(Path(kwargs["cwd"]))
        raise CalledProcessError(2, args[0])

    with WorkDir.using(tmp_path), patch(
        "micall.core.assembler_dispatch.subprocess.run", side_effect=abort
    ):
        out = run_external_assembler("abyss", tmp_path / "R1", tmp_path / "R2")
    assert out.read_text().startswith(">graph1\n")


def test_non_abyss_failure_is_not_recovered(tmp_path):
    from subprocess import CalledProcessError
    from micall.core.assembler_dispatch import run_external_assembler
    from micall.utils.work_dir import WorkDir
    from unittest.mock import patch

    with WorkDir.using(tmp_path), patch(
        "micall.core.assembler_dispatch.subprocess.run",
        side_effect=CalledProcessError(3, ["megahit"])
    ):
        with pytest.raises(CalledProcessError):
            run_external_assembler("megahit", tmp_path / "R1", tmp_path / "R2")
