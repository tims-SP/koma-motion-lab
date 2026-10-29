# CORE-008 · GPT image generation prompts / visual reference contract

**Status: prompts authored, NO AI view imagery yet generated.**
Always pass the *actual Aka source front head image* as reference input. A text-only invocation is INVALID: arbitrary model-remembered "Aka" designs would be unauthentic.

## Reference image pack before generation

- SOURCE_A = full, unmodified composite of official Aka \`tutorial-aka.psd\` head. This is the MASTER identity, color, contour and original linework reference.
- SOURCE_B = contact sheet of original separated parts, especially front/side/back hair, ears, eyes, brows, mouth and face base, with unique part labels. It is an analytical reference, not an alternate redesign.
- SOURCE_C (optional for 45° ONLY) = SELECTED 30° generated image that passed identity/geometry review. This helps geometry continuity, but SOURCE_A is always more authoritative.
- For patch repairs, source includes selected 30°/45° image PLUS original single-part PSD PNG and editable mask region.
- Do NOT assume generated transparency, mesh, UV or provenance from a generic image file. Save those only after actual validation.

## Immutable image-space angle contract

Camera is fixed and orthographic. Positive yaw means **NOSE TOWARD IMAGE RIGHT**, not camera orbit and not a left-right mirror. Neutral pose/expression, eyes gaze naturally in the same direction as the head. Head scale, eye level and neck pivot must match across candidates.

## PROMPT 30° · generate 4 independent candidates

**Reference inputs:** SOURCE_A and SOURCE_B. Each sample independent from original inputs, never condition on another rejected generated output.

\`\`\`text
EDIT THE ATTACHED ORIGINAL CHARACTER REFERENCE, NOT A NEW CHARACTER DESIGN.

Use Reference A (the official original Aka front-view anime head illustration) as the authoritative identity and color source. Reference B contains close-ups of the SAME original character's separated hair, face, eyes, ears and details. Do not invent visual properties absent from those references.

Produce ONE clean, full-head Japanese 2D animation model-sheet illustration showing this exact character's HEAD AND ATTACHED NECK rotated approximately +30 degrees about the vertical head axis: the nose points to the RIGHT SIDE OF THE IMAGE. The virtual camera stays fixed in front at eye height, orthographic perspective, no camera roll, no camera repositioning, no body turn and no expression change.

Use the EXACT SAME character identity, line weight, anime contour styling, color palette, eye colors and shapes, recognizable asymmetric hair locks, bangs, fox ears, head accessories and artwork-specific painted highlights. All hair masses and both fox ears must keep the correct geometry and root locations across this rotation. Near/far facial features change visibly with yaw: far eye becomes narrower and partially occluded as appropriate, nose position/contour shifts to image-right, near cheek and chin have a credible new silhouette. Hair root and ear positions remain attached to the same skull. A real three-quarter face is required, NOT just squeezing the 0-degree image horizontally.

Full head, both ears and visible neck are entirely within the canvas with margin; identical character scale, head pivot, neutral soft lighting and crop. Flat clean neutral background (#F1F2F6) for reliable later masking, no shadows cast on background. Preserve original anime cel/shadow painting, fine clean outlines and crisp flat color, without material/PBR/3D renderer effects.

Output one single character only, one view per image. No labels, grids, watermarks, text, additional faces, extra ears, redesigned bangs, eye-color changes, novel costume decorations, arbitrary mirrored details, dynamic pose, tilted head, fisheye lens or exaggerated perspective. This image will be registered to existing 2D rig parts, so preserving stable anatomy and feature relationships is more important than decorative variation.
\`\`\`

## PROMPT 45° · generate 4 independent candidates

**Reference inputs:** SOURCE_A + SOURCE_B; optionally selected 30° as SOURCE_C. Reject 45° candidates looking less rotated than the accepted 30° reference.

\`\`\`text
Create a missing three-quarter-view turnaround image of EXACTLY the anime character in Source Reference A (original Aka official front illustration). This is a faithful view complement for an existing 2D rig, NOT a new drawing concept. Source Reference B is a labeled collection of the exact same original character's individual eye, face, fringe, side-hair, back-hair and fox-ear painted parts. If Reference C is supplied, it is the already approved +30-degree intermediate orientation; use it for spatial correspondence but never override the identity, color or hairstyle of Reference A.

Rotate only the head and its neck attachment by approximately +45 degrees in 3D about the vertical axis, with NOSE POINTING TO IMAGE RIGHT. Keep a fixed orthographic camera at the same eye height, focal scale, framing and head pivot as Source A. The head turn should be CLEARLY MORE SIDE-ON than the +30-degree example, while still a readable 3/4 anime portrait, not a full 90-degree profile.

Keep exact character identity, style and design: matching color palette, original stroke shapes, distinctive fringe clusters, asymmetrical hair locks, hair color/shadows, ear structure, iris design and outline thickness. Correctly reduce far-side eye visibility, show a coherent near-side cheek and profile of the nose, preserve the chin/jaw identity, and reveal only physically plausible newly exposed side/back hair with original strand direction. Near/far ears must have correct overlapping order. Keep the mouth aligned to the face orientation.

Show the entire head, both ears and attached neck within consistent margins. Original 2D Japanese-animation linework and hand-painted shadows, not sculpted 3D texture, not semi-realistic lighting, no photorealism. Simple flat background #F1F2F6 and one neutral-expression view only.

Do not mirror the source art, invent features, change eyes or jewelry, make the far eye equally large, paste the front hair flat, create new ear tips, paint arbitrary extra face details, crop any hair/ear, introduce camera tilt, pose the body, add any written labels, panels, diagrams or signatures. The image must remain cleanly segmentable into original hair/face/eye/ear components.
\`\`\`

## PROMPT 15° fallback · only if the 0→30 interpolation fails

**Reference inputs:** SOURCE_A and selected 30°.

\`\`\`text
Make an accurate +15-degree in-between anime head drawing of the SAME official Aka character shown in Reference A, using approved +30-degree Reference B strictly as spatial guidance. Camera fixed orthographic and nose toward image-right. Preserve every original hair lock, ear, eye/eyelid, mouth, complexion, decorative asymmetry, flat shading and ink line width. The head must be visibly rotated less than the approved +30-degree view and more than the original 0-degree view, with stable eye line and neck pivot. Neutral expression, full head and ears, background #F1F2F6, no labels or redesigned features. Produce one clean image only.
\`\`\`

## PROMPT PATCH · for a single diagnosed bad region (mask-based edit)

**Reference inputs:** current accepted generated full view, SOURCE_A original and SOURCE_B specific part/crop + a single editable region mask.

\`\`\`text
LOCAL CHARACTER-FIDELITY REPAIR ONLY. Preserve ALL unmasked pixels and the exact camera angle, image placement, size and expression of the provided accepted Aka +{ANGLE}-degree view. The editable masked region is '{PART}' only. Use the separately attached official front-art '{PART}' reference to correct its color, characteristic outline, strand/eye/ear geometry and occlusion order for this rotated perspective. At the mask boundary create clean seamless Japanese-animation linework; do not shift landmarks or alter any other part. Do not add new hair ornaments, eyes, ears, bangs or highlights not supported by source. Return the same full-frame image with only that localized region improved. No text, background changes or new composition.
\`\`\`

## PROMPT SEGMENT · only if image editing/masking is explicitly supported

**References:** accepted single-angle head image plus reference contact of original PSD parts.

\`\`\`text
For this accepted +{ANGLE}-degree Aka view, isolate ONLY the component '{PART_ID}' matching the original PSD layer identity and mask. Keep its exact original colors and outlines from the accepted rotated drawing, preserve accurate position, scale and edge coordinates on the original canvas. All other components must be transparent if real alpha is supported; otherwise output a high-contrast segmentation mask for this component WITHOUT repainting or inventing hidden areas. Do not change perspective, shape, colors or add interior features. This is a cutout/correspondence task, not a fresh drawing task.
\`\`\`

Image generation is NOT a guaranteed source of true alpha masks or original INX ArtMesh metadata. For repeatable masks prefer deterministic segmentation (SAM2 / original PSD priors), with generated edits restricted to missing content.

## Candidate QA rubric (per generated view)

| Test | Weight | Examples of FAIL |
|---|---:|---|
| Identity / iconic hairstyle and asymmetry | 30% | Changed bangs, colors, ear or accessory |
| Angle/landmark and perspective credibility | 25% | 45° looks front, far eye unchanged |
| Hair/ear/face occlusion correctness | 20% | Back hair over face, ear floating |
| Raster/style and cel-shadow preservation | 15% | Smooth 3D rendering, altered line weight |
| Part separation/registration tractability | 10% | Unresolvable merged hair/eyes |

Score each from 0–5, weighted total/5. **Target >=4.3/5** with no catastrophic identity, anatomy or overlap failure, and rank candidates under same-scale aligned contact sheets. A higher score does not prove the nominal angle is geometrically exact; landmark/contour fitting is a second separate gate.

## Retry policy

- Identity drift -> improve SOURCE_A/B crops and retry at same angle, NOT using a distorted generated image as new master.
- Wrong yaw sign -> fix direction explicitly and retry, never silently flip non-symmetric asset.
- Good artwork, bad segment boundary -> repair isolated part / mask, not entire head.
- 45° anatomy still implausible -> cap project yaw at 30° instead of pretending it works.
- If all four candidates are rejected, record failure and stop; no unbounded image-generation loop.

## Asset manifest sample

\`\`\`json
{
  "character_id": "aka-seagetch",
  "source_license": "CC BY 4.0",
  "source_author": "seagetch",
  "source_ref": "pinned PSD/INX asset hash",
  "prompt_revision": "core008-prompt-v1",
  "target_yaw_degrees": 30,
  "direction": "nose_to_image_right",
  "source_image_reference": "source_front",
  "status": "GENERATED_UNREGISTERED",
  "candidate_id": "aka+030-cand-001",
  "model": "record actual image-generation engine",
  "image_sha256": "record after generation",
  "notes": "nominal image-view angle, not calibrated camera pose"
}
\`\`\`
