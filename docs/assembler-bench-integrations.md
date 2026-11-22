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


## Exploratory dedicated profile: Fermi-lite (NONQUALIFYING)

Branch `bench/assembler-fermi-lite` adds only the Fermi-lite adapter, built
from pinned source `85f159e5a2e15a4c4fb41cdfce91ba0c9b68d2e1`
(https://github.com/lh3/fermi-lite), whose `LICENSE.txt` is MIT and is
verified by SHA-256 in the image. The committed invocation calls
`/usr/local/bin/fml-asm` with a single interleaved FASTQ and no reference,
seed, truth or target argument. Both source-attested mates are interleaved
into that one input in original order. `misc.c:fml_utg_print` writes actual
assembled unitigs as FASTQ on stdout; the committed dispatcher captures that
stdout and converts each valid record to an exact-sequence FASTA record
without inventing or altering contigs. A valid zero-unitig assembly is an
empty FASTA. Malformed or truncated FASTQ, a nonzero assembler exit and a
missing output all fail closed; they are never reported as empty success.

The image contains no frozen seven tool. This profile is experimental, must
be built only by the guarded launcher, and is excluded from qualification,
the Psi matrix and release. The tool binary digest is independently
attested at build time and recorded as an OCI label; no image digest or
pilot result is asserted by this source commit.
