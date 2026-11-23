# Dedicated IDBA-UD MiCall adapter — NONQUALIFYING

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

Pinned commands from the two original paired FASTQs (input order preserved):
`/usr/local/bin/fq2fa --merge --filter R1 R2 <work>/idba-reads.fa` then
`/usr/local/bin/idba_ud -r <work>/idba-reads.fa -o <work>/idba-out`; MiCall
consumes `<work>/idba-out/contig.fa` (an empty FASTA is valid). Tool source:
`a1bafe6b012912cd9a76926ec75a98aee6213af6`
(https://github.com/loneknightpy/idba); only the de-novo `idba_ud` binary is
used, never the hybrid/reference-guided path. License: GPL-2.0-or-later
(pinned README). No independently attested native binary SHA256 is asserted
by this source commit: the image recipe requires one as a build argument and
fails closed on mismatch; image/pilot status stays source-pinned until such
attestation exists.

This is an exploratory arm only: excluded from the seven-way qualification,
Psi matrix, acceptance denominator and release gates. The image recipe
`Containerfile.assembler-bench` takes an already attested native-tool image
as `ASSEMBLER_TOOL_IMAGE`, deletes its MiCall installation, installs this
branch's exact clinical source, and verifies the adapter, denovo bridge and
native binary SHA256 before finalising. Supply build arguments:
`MICALL_BASE_COMMIT` (the frozen SHA above), `MICALL_SOURCE_COMMIT` (this
branch's exact 40-character commit), `TOOL_IMAGE_ID` (immutable donor image
ID), `TOOL_BINARY_SHA256` (independently attested), `MICALL_ADAPTER_SHA256`
and `MICALL_DENOVO_SHA256` (sha256 of the two committed source files).
No image digest or pilot result is asserted by this source commit.

Source SHA256 for this tree's changed files (recomputed by the image guards):
`benchmark_assembler.py` `fb38bfded362ec773e9a09252216b16fb8ba63cf99060a9b79573b533eccd750`,
`denovo.py` `7cfac4f3a4f4033aa39794a7ba479793ea4d75ef79e98f0ddf612509e60b1694`.
