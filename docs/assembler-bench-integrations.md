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


## Exploratory dedicated profile: SOAPdenovo2 (NONQUALIFYING)

Branch `bench/assembler-soapdenovo2` adds only the SOAPdenovo2 adapter, installed
from pinned source `7560c0b9d59e253cb0c819eca40d60f8636b4a11`
(https://github.com/aquaskyline/SOAPdenovo2). The `LICENSE` blob at that commit
is GPL-3.0 (codeload archive SHA256
`41386f6b259cea4aedba33c447719fa90b793dceb80f562f2f87c3ff56bb6421`). The image
contains no frozen seven tool. This profile is experimental, must be built only
by the guarded launcher, and is excluded from qualification and release. No
image digest or pilot result is asserted by this source commit.

### Verified upstream contract (from the pinned source, not from memory)

* `README.md` "System Requirement": the 5G figure is a generic minimum for the
  tool's intended large plant/animal genomes ("also works well on bacteria and
  fungi"); ~150 GB is quoted for human.
* `README.md` "Get started": the exact one-shot invocation is
  `${bin} all -s config_file -K 63 -R -o graph_prefix`. `-R` means "resolve
  repeats by reads" (`-R (optional) resolve repeats by reads, [NO]`).
* `README.md` / `example.config`: paired FASTQ libraries are declared with
  `q1=<read 1>` and `q2=<read 2>` inside a `[LIB]` section; the other library
  keys (`avg_ins`, `reverse_seq`, `asm_flags`, `rd_len_cutoff`, `rank`,
  `pair_num_cutoff`, `map_len`) are the official grammar. `max_rd_len` is the
  only global key. No reference/genome argument exists, so the argv is
  source-blind.
* `standardPregraph/output_contig.c:157` writes the native result with
  `sprintf(temp, "%s.contig", outfile)`, i.e. `graph_prefix.contig`.
  `output_1contig()` at lines 65-88 emits FASTA records (`>id length ... cvg_
  ..._tip_...` followed by wrapped sequence), so the native `.contig` file is
  itself a valid FASTA. A zero-contig success produces an empty (zero-record)
  FASTA; this adapter returns that empty file rather than fabricating contigs
  or reporting success after a failed/non-native command.
* `Makefile` targets `SOAPdenovo-63mer` from the exact pinned commit using
  bundled `libbam.a` plus `-lz -lm -pthread -lbam -lrt`.

### Why the viral path is plausibly under 4,000,000,000 bytes

The 5 GB figure is not a fixed allocation in the source:

1. `standardPregraph/inc/global.h:90` sets `initKmerSetSize = 0` by default.
   Only `-a <GB>` changes it. With the default, `encap_kmerset()` /
   `encap_kmerset2()` (`newhash.c:353`, `kmerhash.c:343`) grow the hash by
   doubling/realloc in proportion to inserted k-mers instead of reserving a
   multi-gigabyte static pool.
2. `standardPregraph/prlHashReads.c:43` sets `buffer_size = 100000000`. Lines
   339-343 allocate ~2.9 GB of *virtual* scratch (`kmerBuffer` 100M x 16 B =
   1.6 GB, `hashBanBuffer` 100M x 8 B = 0.8 GB, two char buffers 0.2 GB, plus
   read buffers). `ckalloc` is `calloc` (`check.c:95`); on 64-bit glibc these
   large allocations are mmap-backed and lazily faulted. Nothing loops over the
   full 100M capacity: indices are bounded by the actual k-mer count and
   `maxReadNum = buffer_size / (maxReadLen - overlaplen + 1)`.
3. For a viral genome (order 10^4-10^5 bp, at most ~2x that many distinct
   canonical 63-mers), the hash (`kmer_t` ~24 B/entry, load factor 0.77) and
   edge/contig structures are tens of MB, not GB. The 2.9 GB virtual reservation
   is never resident in full.

Therefore a viral-scale `SOAPdenovo-63mer all -s config_file -K 63 -R -o
graph_prefix` run is expected to stay well under the 4 GB guard. This is a
source/size justification only: the true guard is the enforced 4 GB cgroup limit
at actual run time, and no pilot has been run while the shared-disk gate is
closed. Do not increase the limit or assert a pilot result from this source.
