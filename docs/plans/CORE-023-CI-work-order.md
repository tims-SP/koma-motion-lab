# CORE-023 Task D — add the actual regression gates to CI

Use mcode file tools for this small, independent integration change. Only edit
.github/workflows/koma-reference-factory-022.yml.

After its existing dependency install, add a named step that runs from the
existing experiments/reference-factory working directory:

    python -m unittest discover -s tests -v
    python probe_decomposition.py --skip-network

Use raw commands with their actual exit codes, no tail/tee pipelines and no
continue-on-error. Do not run model inference, install ML dependencies, upload
local generated candidates, edit source scripts or change existing rendering,
source integrity, artifact or owner-only Draft Release protections. This CI
tests synthetic regression inputs; it does not reproduce the two local imagegen
candidates and must not claim it does. Preserve that distinction in the step name.

Do not commit/push; supervisor validates current YAML and runs checks before
submission. Final reply list actual diff and any blocker.
