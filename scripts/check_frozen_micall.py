"""Reject post-freeze MiCall changes outside assembler-integration surfaces.

Run against an immutable protected tag created AFTER approved fixes are
reauthored and merged into MiCall master. Branch protection and review
must enforce the check; path checks alone cannot certify the contents.
"""
import argparse
from pathlib import PurePosixPath
import subprocess


def allowed_path(path: str) -> bool:
    """Only permit independent assembler modules, tests, builds and docs."""
    parts = PurePosixPath(path).parts
    if not path or path.startswith("/") or ".." in parts:
        return False
    if path.startswith("micall/core/assembler_"):
        return len(parts) == 3 and path.endswith(".py")
    if path.startswith("micall/tests/test_assembler_"):
        return len(parts) == 3 and path.endswith(".py")
    if path.startswith("docs/assemblers/"):
        return len(parts) >= 3
    if path.startswith("assembler-bench/"):
        return len(parts) >= 2
    if path.startswith("Dockerfile.assembler-"):
        return len(parts) == 1
    return False


def git(*args):
    return subprocess.check_output(["git", *args])


def violations(base: str, head: str = "HEAD") -> list[str]:
    """Compare complete frozen and candidate trees; refuse non-ancestry."""
    commit = git("rev-parse", "--verify", f"{base}^{{commit}}").decode().strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", commit, head],
                   check=True)
    raw = git("diff", "--no-renames", "--name-only", "-z", commit, head)
    paths = [name.decode() for name in raw.split(b"\0") if name]
    return [path for path in paths if not allowed_path(path)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-tag", required=True,
                        help="protected annotated tag on approved master")
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()
    forbidden = violations(f"refs/tags/{args.frozen_tag}", args.head)
    if forbidden:
        print("FROZEN_MICALL_SOURCE_CHANGED:")
        for path in forbidden:
            print("  ", path)
        raise SystemExit(1)
    print("FROZEN_MICALL_SOURCE_UNCHANGED_EXCEPT_ASSEMBLER_INTEGRATIONS")


if __name__ == "__main__":
    main()
