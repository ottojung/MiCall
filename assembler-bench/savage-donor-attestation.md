# SAVAGE de novo donor attestation (rederived, no rebuild)

Scope: read-only rederivation from an existing retained donor artifact on the
authorized host. No build, no container, no pilot, no slot taken.

## Pinned source

- Repo: `https://github.com/HaploConduct/HaploConduct`
- Commit: `24e4d9fc35ef6a93e336949a9a8f98ed4ceef362` (verified by `git ls-remote`)
- Adapter branch: `bench/frozen-8458f9e5-savage-20261123` @ `0919ffa97f609b6f0b650ce834f0fc79822f18e5`
- License: GPL-3.0 (LICENSE present at pin)

## Rederived donor (genuine already-built, host-local)

| Artifact | SHA-256 | Status |
|---|---|---|
| `ViralQuasispecies` (ELF x86-64, dynamically linked, PIE, with debug_info, not stripped) | `199d97b7330df213f0adf99aaebb8f74d59806dfe90379f15dea28f0aa0c6590` | Rederived by sha256sum; matches PR576/PX dependency evidence. Provenance logs present (build.log/diag.txt) in retained donor dir. |
| quick-cliques binaries (`qc`, `compdegen`, `printnm`) | MISSING | Not retained in donor dir; cannot be rederived without rebuild/armed build guard. |

## Concrete blockers (remain)

- `VIRAL_QUASISPECIES_BUILD_SHA256` and `QC_BINARIES_BUILD_SHA256` must come from a reviewed armed build guard / in-container rebuild; host-built donor hash is not an in-container rebuild attestation.
- NumPy 1.16.6 archive (`e5cf3fdf13401885e8eea8170624ec96225e2174eb0c611c6f26dd33b489e3ff`) must be operator-staged in build context.
- CPython 2.7.18 (`da3080e3b488f648a3d7a4560ddee895284c3380b11d6de75edb986526b9a814`) and SciPy 1.2.3 (`ecbe6413ca90b8e19f8475bfa303ac001e81b04ec600d17fa7f816271f7cca57`) archives verified in dependency evidence.
- Pinned common MiCall base image digest and reviewed armed build guard required before any image build.
- No paired pilot exists; no image; source-pinned only. NONQUALIFYING.

## Policy

No build/container executed. No slot taken. No frozen/common MiCall mutation.
No proxy zero, no score, no seven-way inclusion. Request named bounded future
slot from sole PX owner `twfJQwQ` once eligible.
