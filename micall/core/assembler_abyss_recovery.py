"""Recover genuine ABySS graph unitigs when an empty SAM aborts DistanceEst."""
import gzip
import logging
from pathlib import Path
import shutil

LOG = logging.getLogger(__name__)
FAILURE = b"DistanceEst.cpp:669: int main(int, char**): Assertion `in' failed."


def no_alignment(path: Path) -> bool:
    """Require a complete SAM header with reference dictionaries, and no rows."""
    if not path.is_file():
        return False
    has_ref = False
    try:
        with gzip.open(path, "rt", encoding="ascii") as lines:
            for line in lines:
                if not line.startswith("@"):
                    return False
                if line.startswith("@SQ\t"):
                    has_ref = True
    except (OSError, UnicodeError, EOFError):
        return False
    return has_ref


def valid_graph(path: Path) -> bool:
    """Require a nonempty complete graph-generated FASTA, without guessing."""
    if not path.is_file():
        return False
    records = 0
    sequence = False
    for line in path.read_text(encoding="ascii").splitlines():
        if line.startswith(">"):
            if records and not sequence:
                return False
            records += 1
            sequence = False
        elif line and all(base in "ACGTNacgtn" for base in line):
            if not records:
                return False
            sequence = True
        else:
            return False
    return bool(records and sequence)


def recover(work: Path, output: Path) -> bool:
    """Only recover a proven ABySS no-alignment DistanceEst assertion."""
    log = work / "assembler.log"
    graph = work / "assembly-3.fa"
    sam = work / "assembly-3.sam.gz"
    if (not log.is_file() or FAILURE not in log.read_bytes()
            or output.exists() or not no_alignment(sam)
            or not valid_graph(graph)):
        return False
    shutil.copyfile(graph, output)
    with log.open("ab") as stream:
        stream.write(
            b"ABYSS_GRAPH_UNITIGS_NO_PAIRED_ALIGNMENTS_USED_AS_CONTIGS\n")
    LOG.warning("ABySS DistanceEst had no SAM alignments; using native unitigs")
    return True
