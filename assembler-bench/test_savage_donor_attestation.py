#!/usr/bin/env python3
"""Static checks for SAVAGE donor attestation/dry plan (no build/container)."""
from pathlib import Path
import re
import sys

DOC = Path(__file__).with_name("savage-donor-attestation.md")
PLAN = Path(__file__).with_name("savage-dry-plan-20261128.md")


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "24e4d9fc35ef6a93e336949a9a8f98ed4ceef362",
        "199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590",
        "QC_BINARIES_BUILD_SHA256",
        "VIRAL_QUASISPECIES_BUILD_SHA256",
        "NumPy 1.16.6",
        "e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff",
        "No build/container executed",
        "NONQUALIFYING",
        "MISSING",
    ]
    missing = [s for s in required if s not in text]
    if missing:
        print("MISSING", missing)
        return 1
    hashes = re.findall(r"\b[0-9a-f]{64}\b", text)
    if len(hashes) < 4:
        print("too few hashes", len(hashes))
        return 1

    pt = PLAN.read_text(encoding="utf-8")
    for s in [
        "e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff",
        "4b41a2badc29877c28a0e903fe7df29a6666a220",
        "ec45769285aaafe1068fc7ac164777343c11a508b1dae34b15aac2d83ed08876",
        "git tree object ID (SHA-1",
        "VIRAL_QUASISPECIES_BUILD_SHA256",
        "QC_BINARIES_BUILD_SHA256",
        "twfJQwQwe22fWGSKuhOXwm-walrus",
        "NOT executed",
        "Static checks in this dir are",
        "not build evidence",
        "Step A — donor/tool prebuild",
        "Step B — final adapter image",
        "no circular expected build SHA",
        "Dockerfile.assembler-bench.savage.donor-pinned.corrected",
    ]:
        if s not in pt:
            print("PLAN MISSING", s)
            return 1
    if "QUICKCLIQUES_SOURCE_TREE_SHA256 is a 40-char git tree SHA-1" in pt:
        print("old misleading claim")
        return 1
    print("ok", len(hashes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
