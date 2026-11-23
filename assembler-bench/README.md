# unicycler assembler-only MiCall benchmark

Exact upstream clinical MiCall master: 8458f9e5d34c39a6694b1fb6a40e055d7ce89553.
The branch changes only the assembler integration, its test and its container
recipe. It has no alternate assembler dispatch, no benchmark scoring, and no
reference-informed assembly selection.

This branch uses Unicycler's Illumina-only short-read de novo path with the
original paired FASTQ passed via `-1` / `-2`. No reference, truth, target or
score-selected contig is supplied. Source pin (old adapter, now superseded):
`1429301eb24df9162f3c9386e8522f942594ae42` (https://github.com/rrwick/Unicycler,
GPL-3.0). Short-read Unicycler is a SPAdes optimiser, not an algorithmically
independent assembler: the native tool calls external `spades.py` from the
pinned SPAdes build `896694ce5c7a9050a6ffa9fccc950a4cd9f04363` (v3.15.5).
A successful run with no retained contigs yields a present, empty
`unicycler/assembly.fasta`, which is a valid zero-contig result.

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
