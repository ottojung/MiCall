# SAVAGE de novo low-space guarded build (READY, not executed)

This directory contains the exact staged build for the missing SAVAGE de novo
NONQUALIFYING image. It is source/build preparation only: no build, container,
image, pilot, registry, frozen-evidence, STOP, lease or guard mutation occurred
when these files were authored.

## Exact pins and donors

| Item | Value |
|---|---|
| Pinned base image (already resident) | `sha256:da795bbdbfbdd3c735c59d0ee008dae1781c68268b24298235e6b2cfe50a23ad` |
| SAVAGE adapter | `bench/frozen-8458f9e5-savage-20261123 @ 0919ffa97f609b6f0b650ce834f0fc79822f18e5` |
| CPython donor | `Python-2.7.18.tgz` SHA-256 `da3080e3b488f648a3d7a4560ddee895284c3380b11d6de75edb986526b9a814` |
| HaploConduct source | commit `24e4d9fc35ef6a93e336949a9a8f98ed4ceef362` |
| HaploConduct archive | SHA-256 `09cad6b864206300caaa543d7df1aab6ac80ba63c80ff66d99bfdba67b87f19e` |
| Source manifest | SHA-256 `f1a05a2c077624736118e0d16b2d9514e1ee24f1b02086a6a021ecbb595859ef` |
| Provenance file | SHA-256 `5be07d4848307eb0613380cfc27f342fed8292e3e3ac8c4733f71d4a830f410f` |
| quick-cliques git tree SHA-1 (recipe semantics) | `4b41a2badc29877c28a0e903fe7df29a6666a220` (35 files) |
| quick-cliques source manifest SHA-256 | `ec45769285aaafe1068fc7ac164777343c11a508b1dae34b15aac2d83ed08876` |
| Donor `ViralQuasispecies` | SHA-256 `199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590` |

NumPy 1.16.6 (`e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff`)
and SciPy 1.2.3 (`ecbe6413ca90b8e19f8475bfa303ac001e81b04ec600d17fa7f816271f7cca57`)
were verified in earlier readiness evidence but are deliberately not installed:
the exact pinned source imports SciPy only in `scripts/min_ev_table.py`, not in
the de-novo `haploconduct savage` path. This removes an unnecessary large build
without changing the pinned SAVAGE source or runtime contract.

## No apt/network fallback

All Dockerfiles use the pinned base image with `COPY` from a verified host-local
context. The build script passes `--pull=never`, `--network=none`,
`--layers=false`, `--force-rm`, `--memory=4g` and `--cpuset-cpus=0-1`. There is
no `apt`, `curl`, `pip` or remote source fetch in any build stage. Any missing
input fails closed.

## Disk budget (includes accumulated retained layers and final copy)

The 3.34 GB common base image is already resident in the bound store and is
shared; it is not downloaded or duplicated. Newly written data is bounded by:

- Stage 1 retained delta: Python 2.7.18 install ~70 MB; transient source/object
  files ~300-350 MB removed inside the same layer.
- Stage 2 retained delta: donor `ViralQuasispecies` ~15 MB, quick-cliques
  binaries and provenance ~20 MB; transient source/object files ~100-150 MB
  removed inside the same layer.
- Final adapter delta: copied pinned MiCall source and `uv sync` output ~50 MB
  on the shared tool-donor layer.
- Podman metadata/margin: ~100-200 MB.

Conservative budget enforced by the script: **2 GiB usable above the 32 GiB
reserve**, with a single build at a time. The script requires that both the
build context filesystem and bound podman store have that headroom. Verified
own-stage images are retired only after the final digest and host-local receipt
are written.

## Coordinator gate

The script requires the exact named grant
`savage-lowspace-UNZbwJhfujc2BbDNDtWgYq-practices-V9ro-lOL3`, explicit
confirmation that P1/remap priority is clear, no STOP, no unbound global lock,
and no active containers in the bound store. `UNZbwJhfujc2BbDNDtWgYq-practices`
is the sole current coordinator; stale pre-UNZbw references do not authorize
execution. This is not authority to consume the guarded worker; the coordinator
grants the real slot on V9ro and lOL3.

After the image digest is attested, parent global admission and a named pilot
window are still required for one physical and one synthetic minimal canary.
No score, proxy zero, qualification, seven-way inclusion or frozen-evidence
change is implied.
