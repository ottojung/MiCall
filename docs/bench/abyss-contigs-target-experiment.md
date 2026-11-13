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

Remaining proof: build a dedicated fork-image from this exact source,
run the same MiCall end-to-end process for the failed case plus several
unaffected cases, compare full final consensus against the frozen old
ABySS image and peer assemblers, then rerun required 400-HXB2 and
198-physical cohort qualification if adopted. Do not claim a gate pass
from the presence of a contig file alone. Full original-pair evidence,
consumer output and failure accounting remain mandatory.
