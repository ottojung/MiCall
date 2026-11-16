# Source-pinned stitched-count MiCall comparator: abyss

Dedicated fork branch bench/assembler-abyss-stitched-counts-20261116. Original comparator image ID
12aaf4eb419c563f01c9bf917c5d7e28ed3baa0430e07ba4a15d7ee50557a37d is preserved; the only runtime code changes are the
general-purpose stitched-read-count provenance fix in
micall/drivers/sample.py and micall/utils/stitched_read_counts.py.

Patched source is shared fork commit e18ebccf9e68d5ee9e01206e7b69045f2be672f3.
All six comparator branches use an identical source tree under micall/.

The Ivanka Rust binary is not copied, built, executed or scored.
The original physical/synthetic inputs and hidden truth are unchanged.
This experiment is NOT release-qualified. All failed arms remain failed.
