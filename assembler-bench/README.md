# Dedicated Minia MiCall adapter — NONQUALIFYING

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

Both original mates are interleaved losslessly in input order into one FASTQ
(plain or gzipped input is supported; unequal mate counts fail closed). Pinned
command: `/usr/local/bin/minia -in <work>/both_mates.fastq -kmer-size 31
-abundance-min 3 -out <work>/minia`; MiCall consumes
`<work>/minia.contigs.fa` (an empty FASTA is valid). Tool source:
`7b7239c69ecc63534a20fc0d0c2de30f0f67e31c` (https://github.com/GATB/minia),
License: AGPL-3.0. No independently attested native binary SHA256 is
asserted by this source commit: the image recipe requires one as a build
argument and fails closed on mismatch; image/pilot status stays source-pinned
until such attestation exists.

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
`benchmark_assembler.py` `bb6c492f43d6e6a1ac182efdc3c255a98505eeac6273d9a7af6ca7b54ba7fee2`,
`denovo.py` `bc89e6f1e6241df7b328e973292961104065f9349c07b5665758f58f6501ef41`.
