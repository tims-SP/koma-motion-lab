# MVP-009 · Live2D / Agent 面部制作与跨视角数据契约

Date: 2026-11-01
Status: **REFERENCE CONTRACT ADOPTED / ORGAN-LEVEL IMPLEMENTATION PENDING**
Applies to: `experiments/head009` (selected Plan B), then validated head 360.
Production repository remains independent.

## 1. Scope and source hierarchy

This contract extracts reusable conventions from **official Cubism** and **open-source Agent automation**, while preserving MVP-009's Euclid-inspired multi-view original artwork, 3D anchors, ArtMesh/VDD and region-aware occlusion. It does not require the discontinued Euclid application, a fully volumetric head, or an official Cubism runtime in the target Three.js engine.

Upstream authoritative specifications:
- Official [Standard Parameter List](https://docs.live2d.com/en/cubism-editor-manual/standard-parameter-list/): parameter IDs and control semantics.
- Official [How to create PSDs to import](https://docs.live2d.com/en/cubism-editor-manual/reimport-psd/) and [Notes on PSD creation](https://docs.live2d.com/en/cubism-editor-manual/precautions-for-psd-data/): RGB/8-bit PSD, distinct layer names, one composite image per imported part, opacity and source separation.
- Official [Draw Order](https://docs.live2d.com/en/cubism-editor-manual/draworder/), [Drawing Order Groups](https://docs.live2d.com/en/cubism-editor-manual/drawing-order-group/) and [Model Templates](https://docs.live2d.com/en/cubism-editor-manual/applying-the-model-template/): parameter-dependent ordering and reusable deformer hierarchy.
- Official [External application integration API](https://docs.live2d.com/en/cubism-editor-manual/external-application-integration-api/) and [API methods](https://docs.live2d.com/en/cubism-editor-manual/external-application-integration-api-list/): WebSocket/JSON external model access. Current verified stable Editor API capability must be determined by connecting to the installed version, not by assuming all alpha edit commands exist.

Third-party candidate tooling (requires version/license/runtime verification):
- [PSD2Live](https://github.com/tsunehimatoi/psd2live), especially [PSD layer and naming spec](https://github.com/tsunehimatoi/psd2live/blob/master/docs/en/spec/PSD_LAYER_SPEC.md): PSD classification, auto ArtMesh/deformers and MCP workspaces.
- [Live2D Agent Kit](https://github.com/Ariakage/live2d-agent-kit/blob/main/SKILL.md): repeatable agent workflow, five coordinate systems, original pixel preservation, reproducible source manifests and independent Core/WebGL test.
- [CubismExternalEditMCP](https://github.com/nana7chi/CubismExternalEditMCP): official editor API adapter; 5.4 Alpha enhanced object edit methods require a supported current Editor release. Official 5.4 Alpha ended on 2026-10-18, so the old MCP full-edit path is an **EVALUATION CANDIDATE**, not a production prerequisite.
- [CLI-Anything Live2D](https://github.com/HKUDS/CLI-Anything): inspect/lint/manifest/patch runtime file references; a .model3.json metadata check cannot certify mesh, original painting or a real editable .moc3 model.

## 2. Coordinate systems and identity

For every source and rendered organ record the transforms among:
1. Original reference image pixels (view-specific, origin at upper left).
2. Transparent part crop pixels (part bounding rectangle and padding).
3. Shared artwork/model canvas units (fixed origin, calibrated scale).
4. Runtime ArtMesh and bone-local/3D anchor XYZ, including the part local face plane.
5. Texture atlas coordinates / normalized UV when RGBA textures are present.

Record the matrix and inverse for each conversion; never visually guess placement or treat equal-looking pixels as corresponding coordinates. Every organ has a **permanent semantic ID** independent from SVG path names, PSD layer names, and optional Cubism Part/Drawable IDs. Left/right means the **character's own** anatomical left/right, not the screen side. A separate `exportId` can map to Cubism's alphanumeric/underscore naming.

For each key view `0,45,90`, and held-out refs `30,60,75`, the following semantics are required (mark truly occluded data as `occluded`, preserve anatomical identity):
- Face: forehead, temples, cheeks L/R, jaw L/R, chin, skin/hairline contours.
- Nose: radix/bridge, profile ridge, tip, alar base/nostril when visible.
- Eyes L/R: upper/lower lids and lashes, sclera, iris, pupil, eye corners, eye openness, occlusion masks.
- Eyebrows L/R: inner/outer, brow arch, view-specific visibility.
- Mouth and oral cavity: outer corners L/R, upper/lower lip, mouth opening, inner-mouth shape, upper/lower teeth and tongue if the expression requires them.
- Ears L/R: outer rim, tragus/inner folds, ear root, hair overlap.
- Hair: front / side L/R / back, root pivots, inner hairline, scalp contact and overlap.

One face polygon is not a substitute for independently transformable eye, nose or mouth semantic parts. A closed-mouth line is not sufficient source art to animate oral interior; preserve hidden iris/eye-white and open-mouth contents from separate authored source.

## 3. Portable schema for agent-generated artwork

```ts
interface OrganView {
  yawDeg: number;                    // keyed / independent held-out
  sourceId: string; sourceSHA256: string;
  pixelToCanvas: number[];          // explicit affine matrix
  rgbaLayerId: string;              // source art, not renderer-derived test data
  landmarks: Record<string,[number,number]>;
  visibility: 'visible'|'occluded'|'enter'|'exit'|'split'|'merge';
  mesh?: {verticesXY:[number,number][]; uv:[number,number][]; triangles:number[]};
  clippingMaskIds: string[];
  depth: {anchorXYZ:[number,number,number]; localBias:number};
  frontOf: string[]; behind: string[];
  deformerParentId?: string;        // reuse hierarchy across views when possible
}
interface Organ {
  semanticId: string;               // e.g. face.eye.L.iris or face.mouth.interior
  parentSemanticId: string;
  cubismPartId?: string;            // separate interoperability ID
  parameterBindings: string[];     // IDs/ranges defined centrally
  keys: OrganView[];
  heldOutReferenceViews: OrganView[]; // NEVER used by runtime interpolation
}
```

ArtMesh may have topological changes at profile (far eye disappearing, ear revealing, mouth-interior switching). Use explicit state/split/merge and registered landmarks. A source missing the required profile organ must trigger a **source art task**, not numerical interpolation pretending to reconstruct it.

## 4. Adopt established parameter semantics

- `ParamAngleX`, `ParamAngleY`, `ParamAngleZ`: official facial orientation convention; default standard range often -30..30.
- `ParamEyeLOpen`, `ParamEyeROpen`: eyes closed=0, open=1; `ParamEyeBallX/Y`: gaze.
- `ParamMouthOpenY`: mouth closure/opening 0..1; `ParamMouthForm`: expression -1..1.
- `ParamBrowL*`, `ParamBrowR*` for eyebrow movement and shape; `ParamHairFront/Side/Back` for sway.
- Keep **horizontal camera-relative 360 yaw** as `cameraYawDeg`/per-bone local view. It is not the same as `ParamAngleX`: preserve the official 2D rig semantics as a local facial control, map from the 3D yaw with a documented adaptor.

Keyforms need compatibility checks in combinations: view yaw × eye openness × gaze × mouth openness × mouth form. Do not validate each isolated parameter and infer the combined animation is correct.

## 5. Agent / MCP responsibilities

**Artwork Agent**: asset inventory, generate/check independent transparent source layers and hidden regions, stable naming, hashes; preserve approved eye/face design.

**Rig/Geometry Agent**: PSD/SVG import, ArtMesh creation, hierarchy, per-view semantic registration, Warp-like deformation and anchor depth.

**Motion Agent**: parameter binding, eye and mouth animation, bone/head movement with view-dependent conditions.

**QA Agent** (read-only against locked reference): compare independent key and held-out art, semantic landmarks, per-organ alpha/mask, visibility/depth and animated combinations. Must inspect real screenshot/video, not only JSON counts.

**Connector/Tool validation**: before production, pin each upstream revision and license, execute on a **copy** of an example model: inspect -> change one editable field -> render actual frame -> restore -> load via valid runtime (where applicable). Keep Editor/MCP/SDK versions and capabilities in evidence. A CLI `validate`/file-exists PASS is insufficient to claim native authoring.

## 6. HEAD009 acceptance additions

At `0,15,30,45,60,75,90`, collect:
- Per-organ landmark reprojection error measured as % of head crop height (initial target <= 2% at key views; held-out errors measured and reviewed).
- Eye, nose, lip/mouth cavity, ear, chin, hairline: organ-specific mask/shape comparison against source and held-out references, not only whole-head IoU.
- Explicit visibility checks for L/R eyes and ears at profile; front/behind graph with nonzero overlapping pixels; clipping/alpha checks.
- Beauty / ID / depth / alpha coverage from the **same** geometry, mask and alpha-test code; fault injection must be detected.
- Eye blink and mouth opening at 0/45/90 and 30/60/75; at least representative combinations before head-motion claim.
- Actual source and rendered cropped image pairs and marked error overlays, with source SHA, render SHA, frame/yaw, and decision.

Gate statuses: `SOURCE_REGISTERED` -> `ORGAN_BINDINGS_VERIFIED` -> `HELDOUT_ORGANS_VISUAL_PASS` -> `PASS_HEAD90_VISUAL`. The latter gates are currently **NOT IMPLEMENTED**.

## 7. First integration task

Add `reference/organ-landmarks.json` and a parser/validator for all current key/held-out SVGs. Extract and review eye, nose, mouth, ear and face landmarks from each original drawing. Render ID/organ crops at 0/30/45/60/75/90 and produce per-organ overlays and numerical reprojection errors; correct semantic registration, source layers and depth before proceeding to T04. Keep T03B as the current stage.

Large reference art and rendered images continue to live in Actions artifacts or approved private storage. Git holds reproducible source/metadata/checks only.
