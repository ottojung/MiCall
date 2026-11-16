# Source-pinned stitched-count MiCall comparator: megahit

Dedicated fork branch bench/assembler-megahit-stitched-counts-20261116. Original comparator image ID
b654ab74e015a7c858b9460a603f370b1a81e42244a9feb3b9fc19d8aa2e8533 is preserved; the only runtime code changes are the
general-purpose stitched-read-count provenance fix in
micall/drivers/sample.py and micall/utils/stitched_read_counts.py.

Patched source is shared fork commit e18ebccf9e68d5ee9e01206e7b69045f2be672f3.
All six comparator branches use an identical source tree under micall/.

The Ivanka Rust binary is not copied, built, executed or scored.
The original physical/synthetic inputs and hidden truth are unchanged.
This experiment is NOT release-qualified. All failed arms remain failed.
