# CORE-023 Task B — final narrow supervisor correction

The supervisor independently ran all 16 probe tests successfully, then found a
remaining false-positive: test_actual_weight_file_counts writes 64 zero bytes to
diffusion_pytorch_model.safetensors and assess_weights declares weights_complete=True.
An arbitrary nonempty filename is not a validated multi-checkpoint installation.

Make assess_weights explicitly presence-only: expose checkpoint_payload_found,
set weights_complete=False because this probe performs no model/index integrity
or load validation, and never return PASS for raw file presence. FOUND payload
must be NOT_TESTED (or BLOCKED readiness), absent payload remains blocked/failed.
Preserve exact names/bytes as observations. Do not implement a checkpoint loader.
Update that test to require payload_found=True but complete=False; add a readiness
regression proving a dummy .safetensors file cannot enable local PASS. Update the
report's interpretation accordingly. Actual current environment is still blocked.

Only probe_decomposition.py, tests/test_probe_decomposition.py and its M3 report.
Run the probe tests and offline probe; do not repeat network GET, install,
upload/infer, access credentials, delegate or commit. This is a narrow change;
do not rewrite the whole file or touch Task A/C.
