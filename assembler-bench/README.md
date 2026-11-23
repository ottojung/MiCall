# SAVAGE de-novo assembler-only MiCall benchmark

Exact upstream clinical MiCall master: 8458f9e5d34c39a6694b1fb6a40e055d7ce89553.
The branch changes only the assembler integration, its test and its container
recipe. It has no alternate assembler dispatch, no benchmark scoring, and no
reference-informed assembly selection.

The image reuses an immutable native-tool donor, but deletes the donor's
MiCall package and application directory, then installs the entire clinical
MiCall package and versions from this branch's uv.lock. The donor is not a
qualified benchmark image. Build and test each final image once before any
expensive sample benchmark. Record branch SHA, source tree, tool donor image ID,
final image ID, and smoke-test results in a single immutable run manifest.

SAVAGE is used in de-novo-only mode: both source-attested paired FASTQs are
passed with `-p1`/`-p2`, and neither `--ref` nor `--count_strains` is supplied.
No reference, truth or evaluator contig is used to select output. A true empty
assembly is represented by a valid zero-contig FASTA.

NONQUALIFYING / experimental only. No OCI image has been built: native tool
source and binary attestation must be completed before any build is allowed.
