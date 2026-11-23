# Dedicated SKESA MiCall adapter — NONQUALIFYING

This branch is derived from exact frozen clinical master
`8458f9e5d34c39a6694b1fb6a40e055d7ce89553`. It changes only the assembler
integration (`micall/core/benchmark_assembler.py`), the adapter-specific
clinical bridge (`micall/core/denovo.py`), its focused test and this
container recipe. All other MiCall clinical source, scoring and frozen
seven-tool branches/images are untouched.

The adapter follows the original seven fixed per-tool interface: `denovo.py`
calls `benchmark_assembler.assemble(first, second, seeds)` directly. There is
no mutable runtime assembler selector, no `MICALL_DENOVO_ASSEMBLER` switch,
no `assembler_dispatch`, no SRA input, no reference/truth-contig use and no
scoring changes. The seeded-contig bridge argument is accepted but ignored.
Pinned SKESA CLI: `/usr/local/bin/skesa --reads R1,R2 --contigs_out ...
--cores 2 --memory 4`, built from `Makefile.nongs` at source commit
`34c872e7fd61c758d0d3917acd76507a43edfc64` (https://github.com/ncbi/SKESA).
Independently attested native binary SHA256:
`d7d97a95add33476e3b84ad8dab48db7278c3833ef8a9df76b08d1bbd78fb85c`.

License: NCBI public domain (US Government Work); bundled third-party
exceptions. This is an exploratory arm only: excluded from the seven-way
qualification, Psi matrix, acceptance denominator and release gates.

The image recipe `Containerfile.assembler-bench` takes an already attested
native-tool image as `ASSEMBLER_TOOL_IMAGE`, deletes its MiCall installation,
installs this branch's exact clinical source, and verifies the adapter, denovo
bridge and native binary SHA256 before finalising. Supply build arguments:
`MICALL_BASE_COMMIT` (the frozen SHA above), `MICALL_SOURCE_COMMIT` (this
branch's exact 40-character commit), `TOOL_IMAGE_ID` (immutable donor image
ID), `TOOL_BINARY_SHA256` (the attested SHA above), `MICALL_ADAPTER_SHA256`
and `MICALL_DENOVO_SHA256` (sha256 of the two committed source files).
No image digest or pilot result is asserted by this source commit; image and
canary status remain separate, capacity-gated steps.

Source SHA256 for this tree's changed files (recomputed by the image guards):
`benchmark_assembler.py` `0f6865975d64512228b81ad77b293f907383cd087915178b81843ae4388bb277`,
`denovo.py` `c622f0371901de682b5ea6c2486e2ccedc7793421401ca186d5c9d4938a05230`.
