# Dedicated SOAPdenovo2 MiCall adapter (NONQUALIFYING)

Adapter-only branch `bench/assembler-soapdenovo2` on the immutable common
fork-MiCall baseline `eeca0381808a6e9ba5ef791c80238a0e2940abb0`. It installs
only SOAPdenovo2, built from pinned source
`7560c0b9d59e253cb0c819eca40d60f8636b4a11`
(https://github.com/aquaskyline/SOAPdenovo2); no frozen seven-tool or clinical
source is changed.

License: **GPL-3.0**, verified from the `LICENSE` blob at the pinned commit.
Source-provenance extra: the codeload archive of that exact commit has SHA256
`41386f6b259cea4aedba33c447719fa90b793dceb80f562f2f87c3ff56bb6421`.

## Memory note (source estimate, not a pilot)

The upstream README states a *generic* 5G physical-memory minimum for the tool's
target large plant/animal genomes (and ~150 GB for human), but the pinned source
does not make a fixed 5 GB allocation. With the committed default `-a 0` the
k-mer hash grows dynamically (`standardPregraph/kmerhash.c:343`,
`newhash.c:353`), and the large scratch buffers in
`standardPregraph/prlHashReads.c:339-343` are `calloc`'d fixed-size slots that
are only touched up to the actual k-mer count (`ckalloc` = `calloc`,
`check.c:95`). For a viral-scale input the distinct k-mer set is bounded by the
genome (roughly <= 2 x 300 kbp), so the resident set stays far below the
4,000,000,000-byte per-run guard. See `docs/assembler-bench-integrations.md`
for the full source-linked estimate.

This is a **source/size estimate only**. No image build and no physical or
synthetic sample run has been performed (the shared-disk PX gate is closed).
Do not claim a pilot result from this source commit.

This image is experimental and excluded from the seven-way acceptance, the Psi
matrix and all release gates.
