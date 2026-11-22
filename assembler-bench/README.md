# Dedicated Fermi-lite MiCall assembler integration (NONQUALIFYING)

Adapter-only branch `bench/assembler-fermi-lite` on the immutable common
fork-MiCall baseline eeca0381808a6e9ba5ef791c80238a0e2940abb0. It installs
only Fermi-lite at pinned source
85f159e5a2e15a4c4fb41cdfce91ba0c9b68d2e1 (https://github.com/lh3/fermi-lite);
no frozen seven tool or clinical source is changed.

`fml-asm` reads a single FASTQ. Both source-attested mates are interleaved
into that one input, in original order, with no reference, seed or evaluator
input. `fml_utg_print` (misc.c) emits assembled unitigs as FASTQ; the adapter
converts each valid record to an exact-sequence FASTA record, rejects
invalid or truncated FASTQ, and treats zero unitigs as a valid empty FASTA.

License: MIT (verified LICENSE.txt at the pinned source revision). This image
is experimental and excluded from the seven-way acceptance, Psi matrix and
all release gates.
