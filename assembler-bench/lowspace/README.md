# SAVAGE de novo low-space guarded build (READY, not executed)

`GUARDED_COMMANDS.sh` is the executable command set for the missing SAVAGE de
novo NONQUALIFYING image. It uses only the shared PX guard protocol: every OCI
build and in-image attestation runs through
`python3 -m assembler_bench.exploratory_runtime.cli`, exactly as the reviewed
Unicycler donor workflow does. The CLI status dict is captured with a direct
redirect (never a pipeline), and `verify_guard_run.py` then checks the durable
run receipt, `status`, `exit_code`, closed lease owner and mode, build
orphan-cleanup, job-temp removal and SHA-256 of the exact `root/run-<id>.log`
child log before the next stage. Every stage, including the in-image
attestation, is authorized only in `--mode build` (never pilot), and attestation
requires one bare QC-bundle hash plus the exact `sha256sum` line of the
in-image `ViralQuasispecies` binary. No direct `podman build`/`podman run`,
no `timeout`, `--memory`,
`--cpuset-cpus`, advisory-lock grep, new guard protocol, STOP/lease
manipulation, prune or registry mutation is performed.

## Required operator environment

- `PX_DONOR_DIR`: host-local directory containing verified `context/` and
  `PROVENANCE.json`.
- `PX_ADAPTER_CHECKOUT`: pinned frozen SAVAGE adapter checkout.
- `PX_CONTROL_ROOT`: deployed PX control root owning the guard modules.
- `PX_ROOT`: exploratory project root owning `storage.conf` (used only for
  post-build read-only `podman image inspect` with `CONTAINERS_STORAGE_CONF`).
- `PX_REGISTRY`, `PX_BASELINE`: absolute paths bound by the guard.
- `PX_RECEIPT_PATH`: host-local receipt output.
- `PX_NAMED_GRANT`: exact named slot grant
  `savage-lowspace-UNZbwJhfujc2BbDNDtWgYq-practices-V9ro-lOL3`.
- `PX_P1_REMAP_CLEAR=yes`, explicitly confirmed by the coordinator.

`assembler_bench.exploratory_runtime.setup.prepare()` re-checks the baseline
hash, `storage.conf` exact `[storage]` keys and the registry policy, then the
launcher takes the shared `.global-worker.lock` with `flock`, reconciles the
durable lease, enforces the watchdog contract when armed, admits reserved disk
and binds a job-local temp directory. The commanded `podman` processes inherit
`CONTAINERS_STORAGE_CONF` from that root, so the pinned graphroot/runroot are
preserved without passing `--root`.

## Shared guard modules confirmed (deployed control root HEAD `b8720600...`)

| Module filename | SHA-256 |
|---|---|
| `benchmarks/assembler_bench/exploratory_runtime/cli.py` | `9189cedd3eb6a4daf78daebc16d5ba6629b8d1466e92659b0b0df97c10afc21c` |
| `benchmarks/assembler_bench/exploratory_runtime/launch.py` | `a258e1bfd0258d97a4f466978ea1d686a053a648833a159fb49b08557c4ba203` |
| `benchmarks/assembler_bench/exploratory_runtime/setup.py` | `1e3b0529aee95b3e1645a578b710ad46e498751c1b7f00e515beff906c87cde8` |
| `benchmarks/assembler_bench/exploratory_runtime/cleanup.py` | `10c4856d4b2247d6734525088d43f199a12ecadb8d55c977d5ab8a53395f23a6` |
| `benchmarks/assembler_bench/exploratory_runtime/monitor.py` | `b0bbefa221ff092acf33021b0203f2b07a912c250fc0893e8fdd59dad642293c` |
| `benchmarks/assembler_bench/exploratory_runtime/pilot.py` | `2022fad9f7a75b94d96007fe25bd2e6f121d79b3870c3adb10adfa7e10e9c97c` |
| `benchmarks/assembler_bench/exploratory_runtime/terminate.py` | `05921f79cefe0ea762e693d823b5a66d28410845ace199f28e50ccc13226cfb3` |
| `benchmarks/assembler_bench/exploratory_space.py` | `bffdc90b703475aeb68f31c2df4334cb36a8912ebaba806cd7baee4d2bc18943` |
| `benchmarks/exploratory_builds/plan.py` | `406234797006f0a3e086633b13c61c3e392f913bca3c13ec340ed48d89e2ecb0` |

The CLI enforces the deployed policy: 1 concurrent worker, 32 GiB reserve,
2400 s wall limit and 4e9-byte sampled process-tree RSS limit; those are not
re-declared in the build command.

## Exact SAVAGE launcher modules and compiler dependencies

- Pinned source `HaploConduct/HaploConduct@24e4d9fc35ef6a93e336949a9a8f98ed4ceef362`.
- Dispatch modules: `haploconduct.py`, `savage.py`, `polyte.py`,
  `polyte-split.py`, `estimate_strain_count.py`.
- Native modules: `bin/ViralQuasispecies` (supplied as the exact donor binary
  `199d97b7...`, not rebuilt), plus `quick-cliques/bin/{qc,printnm,compdegen}`
  built from the pinned tree.
- Wrapper: `/usr/local/bin/savage` explicitly executes
  `/opt/python27/bin/python2.7 /opt/savage/haploconduct savage`, avoiding a
  `python` shebang ambiguity.
- Compiler dependencies confirmed in the pinned common base image: `gcc`,
  `g++`, `make`, `zlib.h` and `libz.so` are present. Quick-cliques needs only
  `g++`/`make`; Python 2.7.18 needs `gcc`/`make`/`zlib`. Boost, NumPy and SciPy
  are not build dependencies for this donor-plus-quick-cliques path: the exact
  source imports SciPy only in `scripts/min_ev_table.py`, which is not on the
  de-novo path.
- NumPy 1.16.6 and SciPy 1.2.3 donor archives remain verified but unused; their
  recorded hashes are `e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff`
  and `ecbe6413ca90b8e19f8475bfa303ac001e81b04ec600d17fa7f816271f7cca57`.

## Exact pins

| Item | Value |
|---|---|
| Pinned base image (already resident) | `sha256:da795bbdbfbdd3c735c59d0ee008dae1781c68268b24298235e6b2cfe50a23ad` |
| SAVAGE adapter | `bench/frozen-8458f9e5-savage-20261123 @ 0919ffa97f609b6f0b650ce834f0fc79822f18e5` |
| CPython donor | `da3080e3b488f648a3d7a4560ddee895284c3380b11d6de75edb986526b9a814` |
| HaploConduct archive / manifest / provenance | `09cad6b864206300caaa543d7df1aab6ac80ba63c80ff66d99bfdba67b87f19e` / `f1a05a2c077624736118e0d16b2d9514e1ee24f1b02086a6a021ecbb595859ef` / `5be07d4848307eb0613380cfc27f342fed8292e3e3ac8c4733f71d4a830f410f` |
| quick-cliques git tree SHA-1 | `4b41a2badc29877c28a0e903fe7df29a6666a220` (35 files) |
| quick-cliques source manifest SHA-256 | `ec45769285aaafe1068fc7ac164777343c11a508b1dae34b15aac2d83ed08876` |
| Donor `ViralQuasispecies` | `199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590` |

## Disk budget

The 3.34 GB common base is already resident and shared. New retained layers are
approximately 70 MB (Python 2.7), 30 MB (donor/quick-cliques) and 50 MB (final
adapter); transient per-stage object files are removed inside each layer. The
guard admits the build only with the deployed 32 GiB reserve intact. No broad
prune is used; the guard reclaims its own job temp and stopped build work
containers, and this script does not delete staged donor images.

After image digest attestation, parent global admission and a named pilot
window are still required for one physical and one synthetic minimal canary.
No score, proxy zero, qualification, seven-way inclusion or frozen-evidence
change is implied.
