# CORE-024 native-priority supervisor return

The earlier worker is stuck in background rembg installation. Finish useful native
exports immediately using the already installed primary psd-tools/Pillow/NumPy;
do not wait for or repeat the install, and do not touch its venv/model state.

Supervisor's independent read-only source check found:
- PSD has 62 genuine RGBA leaf layers with alpha 0..255.
- psd.composite(alpha=0) still returns cached fully opaque merged pixels.
- psd.composite(force=True, alpha=0.0, color=(1.0,1.0,1.0)) returns genuine
  transparent source-layer rendering: 62.061% transparent, 32.671% opaque,
  5.268% soft alpha at 1630x1630.

The existing native_layers.py first draft is unaccepted and broken: ROOT points
to experiments rather than reference-factory, report references psd before open,
and layer.path must not be assumed. Fix/rewrite that SMALL helper using pathlib,
opening PSD before reading metadata, and explicit recursion to construct paths.
Verify source SHA256 from sources.lock.json first. Never white-key character fur.

Export full-source-canvas transparent composite via maintained PSD SDK with force=True,
and export all 62 actual native leaf PNGs via layer.topil() for pixel-preserving
raw RGBA extraction. Preserve names, path, bounds, order, visibility, opacity,
blend and mask/clip flags in JSON. Raw layers with masks/blends are not automatically
standalone appearance-equivalent; state that distinction. Do not bake/repaint them.

Use out/core024/native-v2/ only for outputs. Generate a black/checker/white composite
QA sheet and a genuine-layer contact sheet including face/ears/hair/eyes/mouth/leaf.
Measure white-composited native rendering vs cached merged PSD RGB (foreground
MAE), and native layer PNG pixel equality to topil RGBA. Record actual alpha stats,
source and output hashes. Run the helper, inspect errors, fix and rerun. Keep it
small (roughly <=220 lines), no generic framework, no package installs or model
inference. No credentials, delegation or commit/push.

Allowed code: native_layers.py and docs/research/CORE-024-native-alpha-results.md.
The other model/imagegen comparison may remain pending/blocked. A valid native
source-layer export is separately useful and must not be mislabeled AI decomposition.
Original PSD bytes, CORE-023 code and renderer remain untouched.
