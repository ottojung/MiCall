# MiCall prebenchmark master freeze — user review and reauthoring handoff

**State:** PREPARED BRANCH ONLY. Nothing in this branch is merged into
MiCall `master`. Neither this branch nor its tests starts an assembler
benchmark. The user's active fixed-comparator first-pass and queued
synthetic runs were stopped before preparing this branch. All previously
committed MiCall outputs, original FASTQs and benchmark evidence remain
preserved. Do not restart benchmarks before the owner has reauthored,
reviewed and merged the baseline and explicitly approved a new run.

**Repository:** `ottojung/MiCall`, never `cfe-lab/MiCall`.
**Base:** exact fork `master` at
`cba1898a764fc4ffa6eb8f99b3650df9665f35e2`.
**Prepared review branch:**
`prepare/prebenchmark-micall-freeze-20261116`.
**Release status:** NOT QUALIFIED and NOT FROZEN until the user merges
the approved reauthored commits, creates a protected immutable baseline
tag, and requires the freeze check on future changes.

## Changes grouped for review and reauthoring

1. **Stitcher plotting soundness and runtime:** close the ancestry graph
   iteratively, prevent revisiting cyclic/shared ancestors, and avoid
   repeated expensive closure computation. This changes diagnostics,
   not assembler output sequences.
2. **Reference-blind long-overlap phase guard:** do not claim phase for
   a contig overlap longer than the two-mate span based only on
   independent read placement. This affects assembled contigs and
   warrants explicit biological phase validation.
3. **Unexpected paired technical tails:** infer a common terminal
   adapter only from sufficiently frequent paired-read evidence;
   apply to Cutadapt. This is a real input-transforming change:
   review potential false trimming of conserved biological sequence.
4. **Shared explicit assembler dispatch:** assembler-name-only entry
   points and deterministic command contracts for IVA, Ivanka,
   Haploflow, MEGAHIT, ABySS, SPAdes, and Velvet. Integration remains
   reference-blind and does not select contigs using benchmark truth.
   This sets up assembler-only post-freeze extension points.
5. **External assembler edge cases:** retain original trimmed paired
   reads for IVA when merge-mates provides an empty overlap; recover
   ABySS native graph unitigs only on a specifically validated
   no-alignment DistanceEst failure. Neither case invents output
   sequence or read support.
6. **Cross-stage stitched read-count provenance:** MiCall remaps reads
   against original unstitched contigs, but reference-blind stitching
   may reorder, reverse-complement, join, duplicate, or remove them.
   The next stage must not interpret the old row numbers as positions
   in the stitched CSV. Project counts ONLY for full sequences that
   uniquely appear on both sides, including reverse-complement
   canonicalization. A novel join or ambiguous mapping gets an
   UNKNOWN count, never borrowed positional support or invented zero.

   **Important correction to experimental MiCall PR #12:** that patch
   added counts from repeated identical original contigs (example:
   412 + 392 = 804). In MiCall's non-stealing multi-mapping, those
   values can cover the SAME reads, so adding them is not justified.
   This branch conservatively leaves such counts UNKNOWN instead.
   Repeated identical stitched outputs also do not each receive a
   duplicate full count. New regression tests cover both cases,
   reverse complements, partial missing support, reordered unique
   contigs, joined contigs, and `remap-final` precedence.

No experimental benchmark Dockerfiles, OCI image IDs, per-assembler
MiCall code forks, tuned environment variables, real alignment
reference panels, synthetic hidden truths, or benchmark results
belong in the frozen shared source. The `micall/core/remap.py` remapping
implementation is unchanged by this branch from the current fork
master; investigate any further read-mapping changes separately
*before* final freeze rather than slipping them into bench branches.

## Evidence needed before owner reauthors and merges

Run targeted unit tests for all six changes, then the full MiCall
standard CI in a reproducible Python 3.12 environment. Check
end-to-end HIV/HCV assembly outcomes on representative source-attested
real data, particularly phase safety, adapter trimming, and the
count-provenance stages. The original 198-sample benchmark's S39
diagnosis showed a 102-to-179 final score when the experimental
**sum-of-duplicates** patch was applied. That cannot be used as
validation of the new conservative count semantics, and it is NOT
a reason to change this code to favor Ivanka.

The owner should review and reauthor the six commits as needed,
keeping only fixes whose general correctness is established, then
merge into `ottojung/MiCall` master. The total suite and biological
checks are release gates, not post-hoc benchmark-score tuning.

## Freeze activation — only after user-controlled merge

Once the reviewed code is on master, record its exact immutable commit
SHA and publish a **protected annotated tag** pointing to that commit:

```sh
git switch master
git pull --ff-only origin master
git rev-parse HEAD
git tag -as micall-prebenchmark-frozen-v1 -m "Frozen MiCall shared code before assembler comparison"
git push origin micall-prebenchmark-frozen-v1
```

Enable GitHub branch protection requiring the `frozen-baseline` check
from `.github/workflows/frozen-micall.yml`, prevent tag deletion or
retargeting, and require human code review of assembler integrations.
The check explicitly says **PRE_FREEZE** until the tag exists; its
pre-tag green result does NOT imply the project is frozen.

After activation, `scripts/check_frozen_micall.py --frozen-tag
micall-prebenchmark-frozen-v1` rejects any changes to shared MiCall
driver, mapper, stitcher, read trimming, plotting, tests, CI, dependency
locks, or other source outside the narrow assembler-integration
allowlist. Allowed surfaces are `micall/core/assembler_*.py`,
`micall/tests/test_assembler_*.py`, `Dockerfile.assembler-*`,
`assembler-bench/**`, and `docs/assemblers/**`.
This is a *path-level* safety gate: code reviewers must still confirm
that every allowed change only incorporates an assembler and does not
change shared MiCall behavior. Do not broaden the allowlist to make
an unrelated change pass.

Each future assembler integration must build from the exact frozen
shared tree, with a separate source-pinned image and dedicated fork
branch. No post-freeze modifications to `micall/drivers/sample.py`,
`micall/core/remap.py`, `micall/core/trim_fastqs.py`,
`micall/core/denovo.py`, or either stitching engine.
If any core defect is found later, pause comparison and explicitly
replace the common baseline for **all** assemblers with a new approved
freeze; never silently fix only one contender's MiCall image.

## Benchmark restart policy

The old 198/400 benchmark artifacts and historical published web
progress are **superseded evidence**, not results of this master
baseline. Start no new benchmark until the new master SHA/tag,
per-assembler integration commits, identical shared code checks, all
required diagnostic metrics, and source-attested input cohort hashes
have been recorded. Restart all six fixed non-Ivanka assemblers on
the frozen common MiCall first; only then run changing Ivanka versions.
Do not reinterpret prior completed runs as the new baseline.

The stopped services have persistent `down` files. The hourly Ivanka
production-readiness automation was also paused. Neither should be
reactivated by this branch or by a successful unit test.
