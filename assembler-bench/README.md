# Source-pinned Ivanka mate-competition adapter

This fork branch contains only the source-committed Ivanka tool image
profile. It reuses the same downstream MiCall Python source tree as
fork commit `74f60e7be6248bdf5019498276036a0ebd339006`,
shared with IVA and all other repaired pilot assemblers.

The build script accepts only the exact clean published fork branch,
immutable fork-built common MiCall base image, and a source-pinned Rust
donor marked `rust-direct-*`. Only the native Ivanka binary is copied
from the donor. The MiCall source tree is not patched at build or runtime.

This candidate is diagnostic, not production qualified: independent final
MiCall and original-molecule testing plus the complete mandatory
198-real and HXB2-derived 400-synthetic seven-assembler gates are required.
Known references and evaluator truth must never enter native Ivanka
assembly or its selection logic.
