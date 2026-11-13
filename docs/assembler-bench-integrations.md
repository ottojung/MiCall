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
