"""Preserve native ABySS graph unitigs if no mate maps to any unitig.

No synthetic truth, reference panels, fabricated joins, or other assemblers.
"""
import gzip
import hashlib
import json
from pathlib import Path
from shutil import copyfile


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _header_only_sam(path):
    try:
        header, sequence = False, False
        with gzip.open(path, "rt") as stream:
            for line in stream:
                if line.startswith("@SQ\t"):
                    sequence = True
                elif line.startswith("@"):
                    header = True
                elif line.strip():
                    return False
        return header and sequence
    except (OSError, EOFError, UnicodeError):
        return False


def _native_graph(path):
    try:
        with path.open() as stream:
            first = next(stream).strip()
            if not first.startswith(">"):
                return False
            return any(line.strip() and not line.startswith(">")
                       for line in stream)
    except (OSError, StopIteration, UnicodeError):
        return False


def recover(workspace, output, error, log):
    """Return False unless native ABySS had no distance-estimation observations."""
    workspace, output = Path(workspace), Path(output)
    source, mapped = workspace/"assembly-3.fa", workspace/"assembly-3.sam.gz"
    if (error.returncode != 2 or not mapped.is_file()
            or not _header_only_sam(mapped) or not _native_graph(source)):
        return False
    log.flush()
    contents = (workspace/"assembler.log").read_text(errors="replace")
    if "DistanceEst:" not in contents or "Assertion" not in contents:
        return False
    copyfile(source, output)
    report = {
        "schema":"micall.abyss.native-unlinked-unitigs.v1",
        "status":"NATIVE_GRAPH_UNITIGS_NO_PAIRED_DISTANCE",
        "native_graph_sha256":_sha(source),
        "distance_sam_sha256":_sha(mapped),
        "output_sha256":_sha(output),
        "original_abyss_exit_code":error.returncode,
        "original_target":"assembly-contigs.fa",
        "fallback_target":"assembly-3.fa",
    }
    (workspace.parent.parent/"assembler_fallback.json").write_text(
        json.dumps(report, sort_keys=True, indent=2)+"\n")
    log.write(b"ABYSS_NATIVE_NO_PAIRED_DISTANCE_UNITIG_FALLBACK\n")
    return True
