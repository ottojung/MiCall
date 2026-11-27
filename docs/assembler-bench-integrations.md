# MiCall assembler integrations (canonical fork source)

This fork owns the MiCall integration of seven assemblers: IVA, Ivanka,
Haploflow, MEGAHIT, ABySS, SPAdes and Velvet. Upstream
`cfe-lab/MiCall` is **strictly fetch-only**: never push or open PRs there.

Default MiCall continues to use its original, cached IVA run (including
original optional merged contig seeds). A fork-built contender image
pins `MICALL_DENOVO_ASSEMBLER` to exactly one of the supported names.
This selects committed MiCall dispatch, not benchmark-time source patching.
Other contenders receive the same original paired FASTQs and the unchanged
MiCall read-to-final-consensus downstream stages.

Ivanka itself is invoked **directly** at `/usr/local/bin/ivanka`, with
only `--reads1`, `--reads2`, `--output` and `env={}`. Ivanka never
receives HXB2, subtype references, hidden truth, score or tuning flags.
Haploflow requires an interleaved FASTQ generated from **both** input
mates; this preprocessing counts as assembler work. The remaining
contenders use explicit, committed commands without shell injection.
Failures, empty outputs and missing external executables fail closed.

## Reproducibility

Build the **fork base image** from a clean checkout of an exact immutable
`ottojung/MiCall` commit using `scripts/build_assembler_base.sh <tag>`. The script refuses
dirty worktrees/non-fork remotes, binds an exact full source commit and
verifies the resulting base OCI provenance labels.
Then set `FORK_BASE_IMAGE` to that verified image ID and `IVANKA_IMAGE`
to a pinned native-Rust ELF source image ID before running
`scripts/build_assembler_bench_image.sh <assembler> <tag>`.
The script refuses dirty source trees, unknown tools, wrong remotes,
non-fork base images and source/base commit mismatches.

The contender Dockerfile copies the pinned external Ivanka executable
and immutable Haploflow binary, installs Debian-packaged MEGAHIT,
ABySS, SPAdes and Velvet, and fixes the desired MiCall assembler
choice in the image. It does **not** rewrite installed MiCall Python
after the build. Every output image includes the full fork source
commit, common-base ID, and assembler label. The independent bench
must additionally record the exact image ID and tool binary digest.

These commands are the source of test images, *not* a waiver of
independent fork-build verification, original read-data integrity,
or scientific qualification. A source label alone is insufficient.


## ABySS contig-only goal

ABySS uses a Makefile driver. Its implicit default also runs
distance-estimation and summary stages that are not used by
MiCall's downstream remapping. On the source-attested HXB2 clonal
case clonal-s006, the default aborted in DistanceEst after
creating assembly-contigs.fa, incorrectly losing valid contigs.
The committed invocation now explicitly requests this output as
the Makefile goal, with the same input reads and k-mer settings.
It does not create a reference-supported result, omit required
assembly stages, substitute a fabricated contig, or hide command
errors. If the requested target or MiCall downstream fails, the
candidate still fails. All seven candidate images must be rebuilt
from this one new canonical MiCall source baseline before a new
qualification run can use this profile.


## Exploratory dedicated profile: Unicycler (NONQUALIFYING)

Branch `bench/assembler-unicycler` adds only the Unicycler short-read adapter,
installed from pinned source `1429301eb24df9162f3c9386e8522f942594ae42` and built
against SPAdes pinned at `896694ce5c7a9050a6ffa9fccc950a4cd9f04363`. License:
GPL-3.0. The committed invocation uses only the original paired FASTQ (`-1`/`-2`)
and no reference, truth or target. It accepts the native `assembly.fasta`,
including a legitimate empty zero-contig file, while still failing on a nonzero
exit or a missing FASTA.

Unicycler's Illumina-only mode is a SPAdes optimiser, so this candidate is not
algorithmically independent of SPAdes; that limitation is disclosed rather than
hidden. The image contains no frozen seven tool. This profile is experimental,
must be built only by the guarded launcher, and is excluded from qualification
and release. No image digest or pilot result is asserted by this source commit.

Native artifact provenance is kept separate: `SPADES_BINARY_SHA256` attests the
compiled `spades-core`, and `TOOL_BINARY_SHA256` attests the compiled Unicycler
`cpp_functions.so`. Both are checked with `sha256sum -c` at image build time and
must come from independent attestation of a real guarded build. On 2026-11-27
the exact source pins were re-derived over authenticated HTTPS `git ls-remote`
(Unicycler HEAD/main `1429301eb24df9162f3c9386e8522f942594ae42`; SPAdes tag
`v3.15.5` `896694ce5c7a9050a6ffa9fccc950a4cd9f04363`), with codeload archive
SHA256 digests `62cb582468f18b3597e818990f4a6d15e58d3115300695eb92f776b5f549512e`
and `6d60324dc37c99f0ffd6a4bc8981dd6ba2de756fa48a92b2e4661c29c905294c`.
Source-byte verification is not binary attestation, an image digest or a pilot
result; none of those is claimed here.
