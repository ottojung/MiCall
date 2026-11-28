# SAVAGE de novo exact dry plan — audited (2026-11-28)

Scope: source staging and dry plan only. No container, no build, no slot,
no live registry/STOP/worker/lease, no frozen/common MiCall edit. Host-local
paths and all provenance stay on the authorized host; this document is
public-safe (content-addressed values only). Static checks in this dir are
**not** build evidence.

Superseded execution estimate: the later exact guarded low-space build in
`assembler-bench/lowspace/` replaces this document's single-stage 8 GiB
plan with three pinned stages and a 2 GiB usable-above-reserve budget. This
document is retained for recipe-semantics audit only; do not execute its
single-stage command template.

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
- `git rev-parse HEAD:quick-cliques` = `4b41a2badc29877c28a0e903fe7df29a6666a220`.
  This is a **git tree object ID (SHA-1 in this SHA-1 repo)**, not a SHA-256.
- Deterministic quick-cliques content manifest SHA-256 (sorted `sha256  relpath` over
  the 35 tracked quick-cliques blobs): `ec45769285aaafe1068fc7ac164777343c11a508b1dae34b15aac2d83ed08876`.
- Recipe arg semantics (from PR576 `Dockerfile.assembler-bench.savage.donor-pinned.corrected`):
  `ARG QUICKCLIQUES_SOURCE_TREE_SHA256=4b41a2badc29877c28a0e903fe7df29a6666a220` is compared by
  `test "$(git rev-parse HEAD:quick-cliques)" = "${QUICKCLIQUES_SOURCE_TREE_SHA256}"`.
  The arg name is misleading; its value/semantics are the git tree SHA-1. Any execution
  must pass the exact git tree SHA-1 `4b41a2ba...` for that check, and should record the
  manifest SHA-256 `ec457692...` separately as content attestation.
- Built quick-cliques binaries (`qc`, `printnm`, `compdegen`) are NOT retained in the donor
  artifact dir; `QC_BINARIES_BUILD_SHA256` remains unattained and must come from the reviewed
  armed build guard (no circular expected build SHA).

## 3. Exact dry build plan — two explicit steps (NOT executed)

**Recipe source of truth:** PR576 `docs/bench/px-source-readiness-20261126/Dockerfile.assembler-bench.savage.donor-pinned.corrected`.
It is **not** assumed to be `{ADAPTER_CHECKOUT}/Dockerfile.assembler-bench`. Before execution,
copy/verify the exact corrected recipe file by immutable digest from PR576 evidence.

### Step A — donor/tool prebuild (armed build guard, bounded slot required)

- Build context: isolated guarded context containing only pinned donor archives and the
  corrected donor-pinned recipe; no new large cache.
- Required context files/digests:
  - `Python-2.7.18.tgz` SHA-256 `da3080e3b488f648a3d7a4560ddee895284c3380b11d6de75edb986526b9a814`
  - `numpy-1.16.6.zip` SHA-256 `e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff` (staged/verified)
  - `scipy-1.2.3.tar.gz` SHA-256 `ecbe6413ca90b8e19f8475bfa303ac001e81b04ec600d17fa7f816271f7cca57`
- Source pin: `HaploConduct/HaploConduct@24e4d9fc35ef6a93e336949a9a8f98ed4ceef362`
- Quick-cliques git tree SHA-1 (recipe arg semantics): `4b41a2badc29877c28a0e903fe7df29a6666a220`
- Quick-cliques content manifest SHA-256 (record separately): `ec45769285aaafe1068fc7ac164777343c11a508b1dae34b15aac2d83ed08876`
- `VIRAL_QUASISPECIES_BUILD_SHA256` and `QC_BINARIES_BUILD_SHA256` are **outputs/attestations
  of the armed build guard**, not pre-known inputs. The recipe fails closed if empty; do not
  set them to donor prebuilt hash `199d97b7...` as a rebuild assertion.

### Step B — final adapter image (after Step A attestation, same bounded slot)

- Use the frozen savage adapter branch `bench/frozen-8458f9e5-savage-20261123 @ 0919ffa97f609b6f0b650ce834f0fc79822f18e5`
  (or independently reviewed successor) with its `Containerfile.assembler-bench` / adapter files.
- Inputs: `ASSEMBLER_TOOL_IMAGE` = digest-pinned output of Step A; `MICALL_BASE_COMMIT=8458f9e5d34c39a6694b1fb6a40e055d7ce89553`;
  `MICALL_SOURCE_COMMIT=<reviewed adapter commit>`; `TOOL_IMAGE_ID=<Step A image digest>`.
- No `:latest`, no mutable tags, no live registry mutation.

**Example command template (NOT executed; fill only after grants/attestations):**

```
# Step A: donor-pinned corrected recipe (armed build guard produces build SHAs)
podman build --pull=never \
  --file {PR576_RECIPE_COPY_VERIFIED_BY_DIGEST} \
  --tag localhost/ivanka-exploratory-savage-donor:0919ffa9 \
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
  {ISOLATED_DONOR_BUILD_CONTEXT}

# Step B: final adapter image from frozen adapter checkout
podman build --pull=never \
  --file {FROZEN_ADAPTER_CHECKOUT}/Containerfile.assembler-bench \
  --tag localhost/ivanka-exploratory-savage-denovo:0919ffa9 \
  --build-arg ASSEMBLER_TOOL_IMAGE={STEP_A_IMAGE_DIGEST} \
  --build-arg MICALL_BASE_COMMIT=8458f9e5d34c39a6694b1fb6a40e055d7ce89553 \
  --build-arg MICALL_SOURCE_COMMIT=0919ffa97f609b6f0b650ce834f0fc79822f18e5 \
  --build-arg TOOL_IMAGE_ID={STEP_A_IMAGE_DIGEST} \
  {FROZEN_ADAPTER_CHECKOUT}
```

## 4. Bounded build prerequisites (all must hold)

1. Named bounded slot grant from sole PX owner `twfJQwQwe22fWGSKuhOXwm-walrus` (no competing worker; 32 GiB reserve).
2. Reviewed armed build guard produces in-container `VIRAL_QUASISPECIES_BUILD_SHA256` and
   `QC_BINARIES_BUILD_SHA256`; values are not pre-filled/circular.
3. Pinned common MiCall base image digest available in bound store.
4. Build context contains verified Python-2.7.18.tgz, NumPy 1.16.6.zip, scipy-1.2.3.tar.gz,
   pinned HaploConduct source; no new large cache.
5. Corrected recipe file identity verified by immutable digest before use.
6. No pilot until image attestation + parent global admission receipt; one physical + one
   synthetic minimal canary only, no truth/score/truth-selected contigs, hashed scratch cleanup.

## 5. Non-claims

No build, no container, no slot, no image, no pilot, no registry/receipt/checkpoint change,
no frozen edit, no proxy zero, no score, no seven-way inclusion. SAVAGE remains source-pinned
and NONQUALIFYING. Static substring checks are not build evidence.
