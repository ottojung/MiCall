#!/usr/bin/env python3
"""Static checks for the guarded SAVAGE low-space build files (not build evidence)."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
FILES = [
    HERE / "Dockerfile.savage-py27",
    HERE / "Dockerfile.savage-tool-donor",
    HERE / "GUARDED_COMMANDS.sh",
    HERE / "verify_guard_run.py",
    HERE / "README.md",
]

FORBIDDEN = [
    "apt-get", "apt install", "curl ", "wget ", "pip install", "git clone",
    "timeout ", "--memory=", "--cpuset-cpus", "flock", "broad prune",
    "image prune", "system prune", "PX_GLOBAL_LOCK",
]

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
    "e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff",
    "ecbe6413ca90b8e19f8475bfa303ac001e81b04ec600d17fa7f816271f7cca57",
]

SCRIPT_REQUIRED = [x for x in COMMON_REQUIRED if x not in (
    "e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff",
    "ecbe6413ca90b8e19f8475bfa303ac001e81b04ec600d17fa7f816271f7cca57",
)] + [
    "savage-lowspace-UNZbwJhfujc2BbDNDtWgYq-practices-V9ro-lOL3",
    "PX_P1_REMAP_CLEAR", "PX_CONTROL_ROOT", "PX_ROOT", "PX_REGISTRY",
    "PX_BASELINE", "PX_RECEIPT_PATH", "PX_DONOR_DIR", "PX_ADAPTER_CHECKOUT",
    "python3 -m assembler_bench.exploratory_runtime.cli",
    "--tool savage-denovo", "--mode build", "--reserve-bytes 1073741824",
    "--pull=never", "--network=none", "--layers=false",
    "PROVENANCE.json", "qc-bundle-sha256.txt",
    "Containerfile.assembler-bench", "GUARDED_BUILD_DONE",
    "verify_guard_run.py", "--build-arg BASE_IMAGE=\"$BASE_IMAGE\"",
    "--require-hash-lines", "find \"$PX_ROOT\"", "GUARD_LOG",
]

MODULE_HASHES = [
    "9189cedd3eb6a4daf78daebc16d5ba6629b8d1466e92659b0b0df97c10afc21c",
    "a258e1bfd0258d97a4f466978ea1d686a053a648833a159fb49b08557c4ba203",
    "1e3b0529aee95b3e1645a578b710ad46e498751c1b7f00e515beff906c87cde8",
    "10c4856d4b2247d6734525088d43f199a12ecadb8d55c977d5ab8a53395f23a6",
    "b0bbefa221ff092acf33021b0203f2b07a912c250fc0893e8fdd59dad642293c",
    "2022fad9f7a75b94d96007fe25bd2e6f121d79b3870c3adb10adfa7e10e9c97c",
    "05921f79cefe0ea762e693d823b5a66d28410845ace199f28e50ccc13226cfb3",
    "bffdc90b703475aeb68f31c2df4334cb36a8912ebaba806cd7baee4d2bc18943",
    "406234797006f0a3e086633b13c61c3e392f913bca3c13ec340ed48d89e2ecb0",
]


def main() -> int:
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        for token in ("/workspace/", "/tmp/opencode/"):
            if token in text:
                print("PRIVATE PATH", path.name, token)
                return 1
        if path.name != "README.md":
            for token in FORBIDDEN:
                if token in text:
                    print("FORBIDDEN", path.name, token)
                    return 1

    all_text = "\n".join(p.read_text(encoding="utf-8") for p in FILES)
    for token in COMMON_REQUIRED + MODULE_HASHES:
        if token not in all_text:
            print("MISSING PIN", token)
            return 1

    script = (HERE / "GUARDED_COMMANDS.sh").read_text(encoding="utf-8")
    for token in SCRIPT_REQUIRED:
        if token not in script:
            print("SCRIPT MISSING", token)
            return 1
    if "| tee" in script:
        print("PIPELINE MASKS GUARD FAILURE")
        return 1
    if script.count("guard_and_verify") < 5:
        print("INSUFFICIENT GUARDED STAGES")
        return 1
    if "podman build" in script and "guard_and_verify" not in script:
        print("UNGUARDED BUILD")
        return 1
    helper = (HERE / "verify_guard_run.py").read_text(encoding="utf-8")
    for token in [
        "parse_status", "find_receipt", "lease_last", "log_sha256",
        "exit_code", "active_unreleased", "orphan_cleanup",
        "job_temp_cleanup", "CLOSED", "HASH64", "GUARD_OK",
    ]:
        if token not in helper:
            print("HELPER MISSING", token)
            return 1

    readme = (HERE / "README.md").read_text(encoding="utf-8")
    for token in [
        "cli.py", "launch.py", "setup.py", "cleanup.py", "monitor.py",
        "pilot.py", "terminate.py", "exploratory_space.py", "plan.py",
        "haploconduct.py", "savage.py", "bin/ViralQuasispecies",
        "quick-cliques/bin/{qc,printnm,compdegen}", "gcc", "g++", "make",
        "zlib.h", "libz.so", "32 GiB", "2400", "4e9",
    ]:
        if token not in readme:
            print("README MISSING", token)
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
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
