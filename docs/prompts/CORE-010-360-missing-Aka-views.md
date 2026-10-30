# CORE-010 · Prompts for missing 360-degree Aka head art

**Text planning only. None of these new side/back images has been generated or accepted.**

## Image reference contract

The image-generation engine MUST be fed the **actual official original Aka PSD composite** as a native attached image-edit reference. It is authoritative for identity, hair, eyes, fox ears, leaf ornament, neck and ink/shading style. Use CORE-008 Inox2D actual HeadYaw reference snapshots as additional constraints (they are normalized parameter poses, not physical degrees). The user GPT +3/4 candidate is secondary and may contain original-design drift; cannot supersede genuine Aka source art.

All generations must produce ONE view only, orthographic camera fixed at original frontal height/scale; head/fox ears/neck visible with margins, simple flat background, neutral expression, consistent hair and eye design. A 0° original PSD is never redrawn.

## Priority 1: +90° profile (nose points IMAGE RIGHT)

Use the attached true Aka original reference, NOT a new character concept. Draw exactly ONE full right-side orthographic head profile with the nose facing image right. Show anatomically credible near eye and nose-jaw contour with far eye actually occluded. Preserve short orange-gold bob hair, two huge orange fox ears with white fur, magenta-red eyes, burgundy leaf attached to the original front bangs, original line weight and 2D cel shadows, neck/choker proportions, hair part asymmetry and roots. Rear hair and far ear must overlap plausibly. No extra eyes, flat squeezed front-face, ribbons, new hair ornaments, Japanese shrine outfit, 3D/PBR highlights, captions, grids, other poses, or additional characters. Full head and both ear tips inside canvas.

HARD PASS: one credible visible eye, one nose profile, authentic Aka hair/ear/leaf identity, no mirrored-eye artifact. The nominal 90° remains uncalibrated until landmark inspection.

## Priority 2: 180° rear (camera sees BACK OF HEAD)

Using the exact same attached original Aka front illustration, produce ONE direct 180-degree reverse orthographic image. Show the back of the short orange-gold bob haircut, hair-root structure, rear faces of two upright huge orange fox ears, realistic back hair/shadow layering, rear neck and choker/collar continuity. Crucially, NO eyes, front face, nose, lips or the burgundy leaf on front bangs should appear on the back; do not paste the front painting through the skull. Preserve the fox-ear anatomy, correct fur, same hair/neck proportions, outline thickness and painted cel shading. No back-of-head facial features, third ear, new accessories, camera pitch, panels, labels or watermarks.

HARD PASS: no face, consistent back hair/scalp and ear backs, no invented accessories.

## Priority 3: -90°, then ±135° rear-quarter, then -45° front-quarter

Make a true opposite left profile instead of horizontally mirroring the +90° result: original left/right asymmetric hair and ears must remain correctly oriented.

Generate ±135° only after the 180° rear and side originals pass identity checks; create new rear exposed hair sections rather than projecting front face textures through back skull. The -45° drawing must use original PSD as the master identity reference even if a +45° candidate is supplied.

## Per-view acceptance / provenance

Every generated image starts as GENERATED_UNREGISTERED. Record actual input image hash, prompt revision, model engine, target nominal yaw, output hash, candidate ID, accepted/rejected QC and part/geometry correspondence. Once accepted, segment into original eye/face/ear/fringe/back hair **semantic parts**, and inpaint occluded undersides. Original 0° INX UV must be immutable, while each new view has its own validated part UV and occlusion maps. No image composite automatically equals an INX source skin.

Expected sequence: +90° and 180° first, then -90°, ±135°, -45°; do not spend effort on tiny front in-between angles while back and true side remain missing.

Related established research: ModelSheetTo3D (Eurographics 2026) https://github.com/hjyoon02/ModelSheetTo3D ; angle-verified model-sheet comparison https://github.com/enwong93-sketch/video-to-3d .
