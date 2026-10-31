# CORE-023 Task B — supervisor rejection / revision order

First implementation is NOT_ACCEPTED pending the following concrete corrections.
Do not touch Task A files. Allowed additions extend to tests/test_probe_decomposition.py.

1. OUT_DIR currently points at repository-root out/core023, outside the ordered
   runtime location. Default output must be experiments/reference-factory/out/core023.
   Add injectable output path and a skip-network/offline option for tests.
2. local_readiness currently passes when any known directory exists. An empty
   models directory or a cloned source repo is not loaded model weights. Report
   precise presence-only evidence; only verify completeness with required actual
   checkpoint/index files, otherwise keep readiness BLOCKED/NOT_TESTED. Torch spec
   presence is not import/runtime/CUDA compatibility validation. Do not claim full
   readiness PASS without actual dependency/input/checkpoint checks.
3. Input hash and source/upstream evidence mismatches must block readiness.
   The current implementation calculates those facts but does not use them as gates.
   On missing/mismatched input, never produce local_readiness PASS.
4. HTTP 200 with non-JSON currently becomes PASS. Invalid/HTML/missing dependency
   metadata must not pass. Call names are ADVERTISED, not verified callable.
   Record actual config auth-related fields if present; otherwise auth status
   UNKNOWN and cite README separately. Never infer anonymous inference works.
5. The setup instructions install requirements before cloning, and overlay into
   a nonexistent utils/ path. Replace with correct ordered commands: clone pinned
   upstream, create/activate isolated environment, install torch then requirements
   from that checkout. No overlays are needed because pinned checkout already
   contains the same code (actual location is common/utils/inference_utils.py).
   Make the intended working directory explicit for the inference command.
6. Supervisor refreshed the three local upstream evidence files to remove an
   accidental extra terminal newline. Recompute their actual hashes and use pinned
   source URLs in the report. Do not mutate upstream evidence.
7. Add small offline tests proving: empty directory never means weights ready;
   hash mismatch blocks readiness even when hardware probes are mocked available;
   malformed HTTP-200 metadata is rejected; output default is the ordered location;
   actual decomposition remains NOT_TESTED. Run tests without output pipelines
   that hide unittest exit codes. Then rerun the real bounded metadata probe.

Only edit probe_decomposition.py, its new test file and CORE-023-M3-readiness.md.
No installs, credentials, inference/image uploads, checkpoint downloads, delegation,
commit/push. Report actual changes, raw test exit status and observed probe result.
