# CORE-024 alternate cutout: original RGB plus deterministic Alpha

User permits alternate cutout methods. Implement one SMALL offline experiment with
the already installed Pillow/NumPy/SciPy only; no installs, model downloads or API.
Only new code cutout_white_canvas.py and docs/research/CORE-024-white-canvas-results.md.
Do not touch native_layers.py or CORE-023 code (other worker owns native export).

Actual source: experiments/reference-factory/out/candidates/pilot-C-001.png,
SHA256 66d661022b811874afb68ac9a033e8cede5d591d005503e4d023702de5424169.
Existing actual imagegen cutout: out/core024/imagegen-cutout-C.png, SHA256
220ee4ff62baae15aa0fa14f9dfb967c74ad14028f902699df2562c1aa9e8f25.

The source has a simple near-white background. Compare two explicitly experimental
ways to preserve its original RGB rather than generatively redraw:
1. Border-connected near-white removal: classify near-white pixels by all RGB
   channels >= threshold (run 250 and 245), then use maintained scipy.ndimage
   binary_propagation from IMAGE BORDER seeds restricted to that near-white mask.
   Only exterior-connected white becomes transparent. Enclosed white fur/eye/highlight
   regions must not be globally erased. Keep a hard alpha baseline, no invented
   soft-matte/hidden-region claim. Do not auto-remove all white pixels or all holes.
2. Transfer ONLY the real imagegen alpha onto the original source RGB at the same
   canvas coordinates, discarding generated RGB. Do not register/warp the source;
   geometry disagreement and halo are failures to report, not hide.

Export new RGBA PNGs under out/core024/white-canvas/. All outputs must preserve
source RGB bit-for-bit (including alpha=0 pixels); verify and record that. Record
real alpha statistics, occupied bbox, edge contact and source/output hashes.
Produce black/white/checker QA composites and zoom crops at fur/ear tips/hair/neck.
Report mask limitations, white-halo/background-pocket risks and whether each
variant is only an experimental cutout. Do not call this semantic decomposition,
rig, exact alpha ground truth or approved multi-view character.

Run the actual script in the PRIMARY Work Python (packages already installed),
check its outputs, then write the short measured report. Keep implementation
around <=180 lines. No package installs, model use, accounts, source overwrites,
delegation or commit/push. The supervisor independently inspects all variants.
