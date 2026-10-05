# QuixBugs source provenance

Upstream: https://github.com/jkoppel/QuixBugs
Pinned revision: `4257f44b0ff1181dedaedee6a447e133219fcebf`
License: MIT, retained verbatim in `LICENSE`.

The four Python modules and corresponding JSON-lines fixtures are copied verbatim from that revision: `mergesort`, `flatten`, `next_permutation`, `find_in_sorted`. No corrected source is used in classifier training or repair proposals. The wrapper materializes the flatten generator and compares outputs to upstream expected values. A three-second timeout applies per case. Duplicate binary-search targets may have multiple valid indices; the wrapper follows the upstream exact expected index and does not generalize that into an algorithmic correctness proof.

These are external programming-challenge defects. They are not production bug reports. The selection tests out-of-taxonomy behavior and is not representative sampling. Source and test files remain separate from synthetic training data.
