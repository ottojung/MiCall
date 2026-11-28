# SAVAGE de novo exact dry plan — staged NumPy, bounded prerequisites (2026-11-28)

Scope: source staging and dry plan only. No container, no build, no slot,
no live registry/STOP/worker/lease, no frozen/common MiCall edit. Host-local
paths and all provenance stay on the authorized host; this document is
public-safe (content-addressed values only).

## 1. NumPy 1.16.6 source archive — staged, verified

- Pinned SHA-256: `e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff`
- Official PyPI sdist URL (public):
  `https://files.pythonhosted.org/packages/b7/6f/24647f014eef9b67a24adfcbcd4f4928349b4a0f8393b3d7fe648d4d2de3/numpy-1.16.6.zip`
- Downloaded fresh from that URL into an isolated host-local guarded build
  context. Re-derived locally:
  - SHA-256 = `e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff` (exact match)
  - MD5 = `3dc21c84a295fe77eadf8f872685a7de` (matches PyPI metadata)
  - size = `5143340` bytes (matches PyPI metadata)
  - in-archive `numpy-1.16.6/PKG-INFO`: Name numpy, Version 1.16.6,
    License BSD, Requires-Python `>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*`
  - `sha256sum -c` over the staged file: OK
- The archive was absent from the prior donor cache; it is now staged in an
  isolated guarded build context only, never in a public repo.

## 2. Quick-cliques source provenance (re-derived at pinned source)

- Source: `HaploConduct/HaploConduct @ 24e4d9fc35ef6a93e336949a9a8f98ed4ceef362` (verified by `git ls-remote`).
- `git rev-parse HEAD:quick-cliques` =
  `4b41a2badc29877c28a0e903fe7df29a6666a220` (35 tracked files) — matches PR576 source-readiness evidence.
- `git show HEAD:quick-cliques/makefile` SHA-256 =
  `5b831e9ecb7afe5f081391ad68d3bcbf66615a5d0b2e55000e28477363bd37ce`.
- Built quick-cliques binaries (`qc`, `printnm`, `compdegen`) are NOT retained
  in the donor artifact dir; `QC_BINARIES_BUILD_SHA256` remains unattained and
  must come from the reviewed armed build guard.

## 3. Dry build recipe (NOT executed)

Recipe: `Dockerfile.assembler-bench.savage.donor-pinned.corrected` from PR576
public evidence. Exact bounded build command template (once named grant exists):

```
python -m assembler_bench.exploratory_runtime.cli \
  --registry {REGISTRY_PATH} --baseline {BUDGET_BASELINE} \
  --tool savage-denovo --mode build --reserve-bytes 1073741824 \
  -- podman build --pull=never \
     --file {ADAPTER_CHECKOUT}/Dockerfile.assembler-bench \
     --tag localhost/ivanka-exploratory-savage-denovo:0919ffa9 \
     --build-arg FORK_BASE_IMAGE={BASE_IMAGE_DIGEST} \
     --build-arg MICALL_FORK_SOURCE_COMMIT=0919ffa97f609b6f0b650ce834f0fc79822f18e5 \
     --build-arg MICALL_FORK_BASE_COMMIT=8458f9e5d34c39a6694b1fb6a40e055d7ce89553 \
     --build-arg TOOL_SOURCE_REPO=https://github.com/HaploConduct/HaploConduct \
     --build-arg TOOL_SOURCE_COMMIT=24e4d9fc35ef6a93e336949a9a8f98ed4ceef362 \
     --build-arg TOOL_BINARY_SHA256=199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590 \
     --build-arg PYTHON27_ARCHIVE_SHA256=da3080e3b488f648a3d7a4560ddee895284c3380b11d6de75edb986526b9a814 \
     --build-arg NUMPY_ARCHIVE_SHA256=e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff \
     --build-arg SCIPY_ARCHIVE_SHA256=ecbe6413ca90b8e19f8475bfa303ac001e81b04ec600d17fa7f816271f7cca57 \
     --build-arg QUICKCLIQUES_SOURCE_TREE_SHA256=4b41a2badc29877c28a0e903fe7df29a6666a220 \
     --build-arg VIRAL_QUASISPECIES_BUILD_SHA256={ARMED_BUILD_ATTESTED_VIRALQ_SHA256} \
     --build-arg QC_BINARIES_BUILD_SHA256={ARMED_BUILD_ATTESTED_QC_SHA256} \
     {ADAPTER_CHECKOUT}
```

`TOOL_BINARY_SHA256` is the host-built donor provenance label only; the recipe
deliberately does not assert it against a fresh compile. Empty build-attested
values fail closed.

## 4. Bounded build prerequisites (all must hold)

1. Named bounded slot grant from sole PX owner `twfJQwQwe22fWGSKuhOXwm-walrus` (no competing worker; 32 GiB reserve).
2. Reviewed armed build guard produces in-container
   `VIRAL_QUASISPECIES_BUILD_SHA256` and `QC_BINARIES_BUILD_SHA256` (SHA-256 of
   `qc`, `printnm`, `compdegen` bundle in quick-cliques/bin/SHA256SUMS).
3. Pinned common MiCall base image digest available in bound store.
4. Build context contains: Python-2.7.18.tgz, NumPy 1.16.6.zip (staged/verified
   above), scipy-1.2.3.tar.gz, pinned HaploConduct source; no new large cache.
5. Adapter branch pinned at `0919ffa97f609b6f0b650ce834f0fc79822f18e5`; frozen
   upstream master `8458f9e5d34c39a6694b1fb6a40e055d7ce89553`.
6. No pilot until image attestation + parent global admission receipt; one
   physical + one synthetic minimal canary only, no truth/score/truth-selected
   contigs, hashed scratch cleanup.

## 5. Non-claims

No build, no container, no slot, no image, no pilot, no registry/receipt/
checkpoint change, no frozen edit, no proxy zero, no score, no seven-way
inclusion. SAVAGE remains source-pinned and NONQUALIFYING.
