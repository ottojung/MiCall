#!/usr/bin/env python3
"""Static checks for the SAVAGE low-space build files (not build evidence)."""
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
FILES = [
    HERE / "Dockerfile.savage-py27",
    HERE / "Dockerfile.savage-tool-donor",
    HERE / "build_savage_lowspace.sh",
    HERE / "README.md",
]

FORBIDDEN = ["apt-get", "apt install", "curl ", "wget ", "pip install", "git clone"]

COMMON_REQUIRED = [
    "da795bbdbfbdd3c735c59d0ee008dae1781c68268b24298235e6b2cfe50a23ad",
    "da3080e3b488f648a3d7a4560ddee895284c3380b11d6de75edb986526b9a814",
    "24e4d9fc35ef6a93e336949a9a8f98ed4ceef362",
    "09cad6b864206300caaa543d7df1aab6ac80ba63c80ff66d99bfdba67b87f19e",
    "f1a05a2c077624736118e0d16b2d9514e1ee24f1b02086a6a021ecbb595859ef",
    "5be07d4848307eb0613380cfc27f342fed8292e3e3ac8c4733f71d4a830f410f",
    "199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590",
    "4b41a2badc29877c28a0e903fe7df29a6666a220",
    "ec45769285aaafe1068fc7ac164777343c11a508b1dae34b15aac2d83ed08876",
    "0919ffa97f609b6f0b650ce834f0fc79822f18e5",
]

SCRIPT_REQUIRED = COMMON_REQUIRED + [
    "savage-lowspace-UNZbwJhfujc2BbDNDtWgYq-practices-V9ro-lOL3",
    "PX_P1_REMAP_CLEAR",
    "RESERVE_KB=$((32 * 1024 * 1024))",
    "NEEDED_KB=$((2 * 1024 * 1024))",
    "--pull=never",
    "--network=none",
    "--layers=false",
    "--force-rm",
    "--memory=4g",
    "--cpuset-cpus=0-1",
    "qc-bundle-sha256.txt",
    "retire_stage",
    "READY_BUILD_DONE",
]


def main() -> int:
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        if "/workspace/" in text or "/tmp/opencode/" in text:
            print("PRIVATE PATH", path.name)
            return 1
        for token in FORBIDDEN:
            if token in text:
                print("FORBIDDEN", path.name, token)
                return 1

    all_text = "\n".join(p.read_text(encoding="utf-8") for p in FILES)
    for token in COMMON_REQUIRED:
        if token not in all_text:
            print("MISSING PIN", token)
            return 1

    script = (HERE / "build_savage_lowspace.sh").read_text(encoding="utf-8")
    for token in SCRIPT_REQUIRED:
        if token not in script:
            print("SCRIPT MISSING", token)
            return 1
    if re.search(r"network=host|pull=always|pull=missing", script):
        print("NETWORK FALLBACK")
        return 1

    py = (HERE / "Dockerfile.savage-py27").read_text(encoding="utf-8")
    donor = (HERE / "Dockerfile.savage-tool-donor").read_text(encoding="utf-8")
    if "ARG BASE_IMAGE" not in py or "FROM ${BASE_IMAGE}" not in py:
        print("PY27 BASE NOT PINNED BY ARG")
        return 1
    if "/opt/python27/bin/python2.7" not in donor:
        print("DONOR WRAPPER MISSING")
        return 1
    if "ViralQuasispecies" not in donor or "QC_SHA256SUMS" not in donor:
        print("DONOR HASH GATE MISSING")
        return 1
    if "numpy" in donor.lower() or "scipy" in donor.lower():
        # Only the explanatory comment is allowed; verify no install command.
        for line in donor.splitlines():
            low = line.lower()
            if ("setup.py install" in low or "pip " in low) and ("numpy" in low or "scipy" in low):
                print("UNEXPECTED NUMPY/SCIPY INSTALL")
                return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
