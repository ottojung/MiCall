# Dedicated Ray MiCall adapter — NONQUALIFYING

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

Pinned command: `mpiexec -n 2 Ray -k31 -p R1 R2 -o <work>/ray-out`; MiCall
consumes `<work>/ray-out/Contigs.fasta` (an empty FASTA is valid). Tool source:
`621dfe8454dc96d49f405e413cb759d3f48790b2`
(https://github.com/sebhtml/ray); the `make` target builds only the de-novo
`Ray` MPI binary. License: Ray application GPL-3.0, Ray Platform LGPL-3.0
(`LICENSE.txt`, independently verified SHA256
`fc24be5a854af6d2669d9db7f02fdbaf1bab72d16089362fa39f3169666e4956`).
The container sets only the two OpenMPI root-permission variables required to
launch `mpiexec`; they do not select an assembler or alter clinical stages.
No independently attested native binary SHA256 is asserted by this source
commit: the image recipe requires one as a build argument and fails closed on
mismatch; image/pilot status stays source-pinned until such attestation exists.

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
`benchmark_assembler.py` `482428df56171ce545dd18c1c03147bc8b67fe26f84d4c9689cdb07b70f62e7e`,
`denovo.py` `21fb9779eaf0b87b5d630339a6e9f655cc502238ad3722eec28d667b2833c6f5`.
