# soapdenovo2 assembler-only MiCall benchmark

Exact upstream clinical MiCall master: 8458f9e5d34c39a6694b1fb6a40e055d7ce89553.
The branch changes only the assembler integration, its test and its container
recipe. It has no alternate assembler dispatch, no benchmark scoring, and no
reference-informed assembly selection.

This branch runs `SOAPdenovo-63mer all` with an upstream-grammar `[LIB]` config
whose `q1` / `q2` are the original paired FASTQ files. No reference, truth,
target or single-end input is supplied. Source pin (old adapter, now
superseded): `7560c0b9d59e253cb0c819eca40d60f8636b4a11`
(https://github.com/aquaskyline/SOAPdenovo2, GPL-3.0; pinned codeload archive
SHA256 `41386f6b259cea4aedba33c447719fa90b793dceb80f562f2f87c3ff56bb6421`).
A true zero-contig success leaves an empty but present
`soapdenovo2_graph.contig`, which is a valid FASTA result; no record is
fabricated.

## Source audit fix (2026-11-23, NONQUALIFYING)

The frozen-8458 adapter inherited `max_rd_len=100` and `rd_len_cutoff=100`
verbatim from the upstream `example.config`. Those keys describe the upstream
100 bp example reads; the frozen MiCall smoke inputs are 150 bp, so the
inherited values would discard 50 bp of every real pair before assembly. The
adapter now samples the paired FASTQs (first 10,000 records per mate, gzip
aware) and writes the observed maximum into both keys, capped at 1000. No
reference, truth, target or evaluator input is read. Two focused mock tests
cover plain and gzipped 150/200 bp pairs and the absence of the old 100 bp
values.

Remaining source-only risk to verify at native build time: `SOAPdenovo-63mer
all` also runs the map/scaffold stages, so a true zero-contig result could
still exit non-zero after a valid `.contig` file is written (the same class of
failure already observed for SKESA). Do not patch that speculatively: verify
the native exit code and, only if confirmed, restrict the invocation to the
pregraph/contig stages with exact upstream grammar. This branch does NOT
change that command.

Source memory note (not a pilot): upstream documents a generic 5 GB physical
memory minimum for large target genomes, but the pinned source grows its hash
dynamically under the committed `-a 0` default; no fixed 5 GB allocation is
made. This remains a source estimate only and must be checked under the
one-worker, 4 GB sampled-RSS pilot guard before any run.

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
