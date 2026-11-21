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

The independently attested `TOOL_BINARY_SHA256` build argument is the SHA256 of
the compiled `/opt/spades/bin/spades-core`; the Dockerfile checks it with
`sha256sum -c` and fails closed on mismatch. No SHA is inferred or fabricated by
this source commit.

This image is experimental and excluded from the seven-way acceptance, the Psi
qualification matrix and all release gates. No image digest or pilot result is
asserted by this source commit; builds require the guarded launcher, an admitted
single worker and separate binary/image attestation.
