# Dedicated Unicycler MiCall assembler integration (NONQUALIFYING)

Adapter-only branch `bench/assembler-unicycler` on the immutable common fork-MiCall
baseline `eeca0381808a6e9ba5ef791c80238a0e2940abb0`. It installs exactly one
exploratory tool and no frozen seven tool or clinical source is changed.

- Tool: Unicycler short-read (Illumina-only) de novo path, pinned at upstream
  commit `1429301eb24df9162f3c9386e8522f942594ae42`
  (https://github.com/rrwick/Unicycler). Verified with HTTPS `git ls-remote`
  on 2026-11-21: this commit is both `HEAD` and `refs/heads/main`.
- License: GPL-3.0 (upstream `LICENSE` file is the GNU GPL v3 text; `setup.py`
  declares `license='GPL'`). Source redistribution obligations apply to any
  resulting image.
- Inputs: original Illumina paired FASTQ via `-1` / `-2` only. No reference,
  truth, target or score-selected contig is passed at any point.
- Native output: `assembly.fasta` in the Unicycler output directory. Upstream
  `StringGraph.save_to_fasta` opens the file for writing and filters contigs by
  `--min_fasta_length` (default 100); a run producing no retained contigs yields
  a present, empty FASTA. The adapter accepts that legitimate zero-contig result
  and still rejects only a missing FASTA or a nonzero tool exit.
- Dependency: Unicycler's short-read mode is a **SPAdes optimiser**, not an
  algorithmically independent assembler. It calls external `spades.py` plus
  `makeblastdb`/`tblastn`. SPAdes is built from the exact pinned upstream commit
  `896694ce5c7a9050a6ffa9fccc950a4cd9f04363` (release tag `v3.15.5`,
  https://github.com/ablab/spades), verified with HTTPS `git ls-remote` on
  2026-11-21. SPAdes 3.15.5 is the minimum-compatible line documented by this
  Unicycler commit (v3.14.0 or later required).

Two independently attested binary digests are required; neither is inferred or
fabricated by this source commit. `SPADES_BINARY_SHA256` attests the compiled
`/opt/spades/bin/spades-core` built from the pinned SPAdes commit, while
`TOOL_BINARY_SHA256` attests Unicycler's compiled native module
`/opt/Unicycler/unicycler/cpp_functions.so`. The Dockerfile checks each with
`sha256sum -c` and fails closed on mismatch. Both binaries are compiled from
pinned source (Unicycler's Makefile uses `-O3 -mtune=native`), so their digests
are properties of the actual guarded build, not constants that can be honestly
pre-pinned from upstream source alone.

Independently re-verified on 2026-11-27 with authenticated HTTPS `git ls-remote`:
Unicycler `HEAD` and `refs/heads/main` both equal
`1429301eb24df9162f3c9386e8522f942594ae42`, and SPAdes `refs/tags/v3.15.5`
equals `896694ce5c7a9050a6ffa9fccc950a4cd9f04363`. Content digests of the exact
codeload source archives are
`62cb582468f18b3597e818990f4a6d15e58d3115300695eb92f776b5f549512e` (Unicycler,
17,627,939 bytes) and
`6d60324dc37c99f0ffd6a4bc8981dd6ba2de756fa48a92b2e4661c29c905294c` (SPAdes,
15,314,749 bytes). These attest source bytes only: no image was built, no
binary digest was produced, and no pilot was run by this source increment.

This image is experimental and excluded from the seven-way acceptance, the Psi
qualification matrix and all release gates. No image digest or pilot result is
asserted by this source commit; builds require the guarded launcher, an admitted
single worker and separate binary/image attestation.
