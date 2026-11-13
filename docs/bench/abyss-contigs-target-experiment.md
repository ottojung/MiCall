# Experimental ABySS contig-only MiCall integration

Status: **unqualified source-backed experiment**. This profile does not
replace the frozen seven-assembler qualification image.

MiCall consumes only `assembly-contigs.fa` from ABySS. Running `abyss-pe`
without a target continues into distance-estimation and scaffolding
stages that are not used by MiCall. A real high-depth HXB2-derived
case with all 10,000 original fragments correctly mapped onto one
contig caused the late `DistanceEst` stage to assert on an empty
intercontig input. At the moment of failure, `assembly-contigs.fa`
had already been produced, but the normal wrapper correctly marked
an unsuccessful external process as failed.

The experimental command requests `assembly-contigs.fa` explicitly as
the make target **for every input**, rather than recovering a file after
failure or treating an unsuccessful assembler as a success. In an
independent shell invocation with identical trimmed paired reads,
`abyss-pe k=41 B=128M j=2 name=assembly in=<paired-reads>
assembly-contigs.fa` exited zero and produced that target.

## MiCall-integrated source-pinned smoke evidence

The tested source is fork commit
`833e7de626410a53bfa21204bde87f3fee556745`, with dedicated OCI
image `0a238f706f6936abce97c7f1eb39836d475e6fe33596a46526fb31758d4b16ee`,
from the same pinned base
`7fe84500bfb75507b1700b03d2f94dc116c72de990138a9e415210b1fe6203cd`
as the frozen ABySS comparator
`f2dcfb3a3c7eaa0304cdebb6b931d62305ea513fea0d2ea8ad6e8e10e4fda89a`.
The installed command module was independently SHA-256 compared against
the committed source: both equal
`5005c373e48eab06d391e73fb2db36c7fb5b3b69f6f102bc8df336908fe7e515`.
An earlier candidate image merely *labelled* the changed source without
actually installing it and therefore failed; those attempts are excluded
from evidence for the corrected profile.

| HXB2-derived case | Control outcome / score | Corrected outcome / score |
|---|---:|---:|
| clonal-s006 | process failed | succeeded, 0.99454676 |
| clonal-s000 | succeeded, 0.99927976 | succeeded, 0.99927976 |
| clonal-s001 | succeeded, 0.99063690 | succeeded, 0.99063690 |

All three corrected arms reached final read-supported MiCall MAX
consensus with all 20,000 mapped reads reported. The case records are
preserved separately with JSONL SHA-256
`07e1d143a5905e2124008881215bcff3c1dcebe7fee14a6f4b61893e6e7d2107`.
This is a **three-case exploratory smoke**, not a completed 400-HXB2 or
198-physical strict PSI gate. Runtime variation is not a dominance proof.

Remaining proof: build a dedicated fork-image from this exact source,
run the same MiCall end-to-end process for the failed case plus several
unaffected cases, compare full final consensus against the frozen old
ABySS image and peer assemblers, then rerun required 400-HXB2 and
198-physical cohort qualification if adopted. Do not claim a gate pass
from the presence of a contig file alone. Full original-pair evidence,
consumer output and failure accounting remain mandatory.
