# tadpole assembler-only MiCall benchmark

Exact upstream clinical MiCall master: 8458f9e5d34c39a6694b1fb6a40e055d7ce89553.
The branch changes only the assembler integration, its test and its container
recipe. It has no alternate assembler dispatch, no benchmark scoring, and no
reference-informed assembly selection.

This branch runs BBTools `tadpole.sh mode=assemble` with the original paired
FASTQ supplied through the twin-file argument `in=R1,R2`; assembly mode never
takes `ref=`. Source pin (old adapter, now superseded):
`fb1a2727b7b4994ecae0ddc362d4ed8148307b20` (https://github.com/bbushnell/BBTools,
LBNL/Regents BSD-like 3-clause; upstream README states free for unlimited use).
A true zero-contig result is an empty but present `tadpole-contigs.fa`; the
adapter never fabricates a record.

The image reuses an immutable native-tool donor, but deletes the donor's
MiCall package and application directory, then installs the entire clinical
MiCall package and versions from this branch's uv.lock. The donor is not a
qualified benchmark image. Build and test each final image once before any
expensive sample benchmark. Record branch SHA, source tree, tool donor image ID,
final image ID, and smoke-test results in a single immutable run manifest.

The final runtime image contains only the clinical MiCall runtime and the
selected assembler integration. MiCall test source and any embedded
build-time checker are excluded. Execute all smoke tests, source/binary
attestation, and benchmark preflight on the host before freezing image IDs.
