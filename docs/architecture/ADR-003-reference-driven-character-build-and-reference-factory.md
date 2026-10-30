# ADR-003 — Reference-Driven Character Build and Reference Factory

**Date:** 2026-10-30  
**Status:** PROPOSED FOR MANUAL VALIDATION; NOT YET PRODUCTION-ACCEPTED  
**Branch:** `feature/koma-25d-core-021`  
**Scope:** Asset acquisition, reference construction, multi-view character build, semantic decomposition, QA, and the order in which rig/IK/animation automation is introduced.  
**Relationship to ADR-002:** This ADR does **not** replace the Three.js/WebGL2 2.75D runtime selected in ADR-002. It refines how character assets are created for that runtime.

## Decision in one sentence

Build characters with a **reference-driven workflow**, not prompt-only generation: combine a character identity reference, a task example, and a structural reference; manually validate the complete path first; then freeze the accepted examples into a reusable **Reference Factory / Reference Atlas** and automate only the steps that have passed visual acceptance.

## Why this ADR exists

The earlier architecture established the runtime direction but left asset creation too open-ended. A prompt such as "draw this character at 90 degrees" is not a sufficiently stable production contract. The model knows the requested text, but not necessarily:

- what exact yaw/camera/crop is required;
- what a valid anime turnaround view should look like;
- which hair/face/accessory structure must remain unchanged;
- how hidden regions should be completed;
- how semantic parts should correspond across views;
- what a correct 2.5D scaffold, rig, or motion result looks like.

The workflow therefore needs **visual ground truth at every standardizable AI step**.

## Core rule: no prompt-only production step

For production-oriented experiments, an AI step should normally receive three classes of evidence:

1. **Identity Reference** — who/what the current character is.
2. **Task Example** — what a correct result for this specific operation looks like.
3. **Structure Reference** — where geometry, silhouette, depth, segmentation, landmarks, skeleton, or motion should be.

Text instructions remain useful, but are supplementary constraints rather than the primary source of truth.

Example for Aka 90-degree generation:

```text
Aka canonical front
+ Aka accepted 45-degree view
+ generic accepted 90-degree anime turnaround example
+ 90-degree silhouette/depth/landmark guide
+ preservation instructions
-> Aka 90-degree candidate
```


## Production invariants that must be fixed before the first Aka 90-degree acceptance

These constraints are part of the asset contract, not optional implementation details.

### 1. Coordinate, camera, image, and color contract

Every generated or rendered view must record and obey one explicit convention:

- right-handed/left-handed world convention;
- semantic meaning of +X/+Y/+Z;
- semantic meaning of positive and negative yaw;
- whether view direction is described from the character or camera perspective;
- orthographic versus perspective camera;
- orthographic scale / FOV;
- camera target and character pivot;
- canvas width/height;
- character crop and margins;
- pixel-center convention;
- transparent/opaque background;
- alpha representation;
- texture orientation / flipY;
- texture filtering and wrapping;
- input texture color space;
- internal working color space;
- output/display color space.

For the Three.js/WebGL path, source color textures must be explicitly tagged and converted according to the selected color-management contract instead of relying on defaults. A structurally correct reference is not accepted if color conversion changes the source art materially.

The exact numeric convention may change during manual research, but once a Golden Reference Set is created it must be versioned and immutable for that set.

### 2. Separate SOURCE TRUTH from CHARACTER DESIGN TRUTH

Not every target view has an original ground truth. A source front image can prove what the visible front looks like, but it cannot prove hidden back hair, ear backs, rear clothing, or occluded accessories.

Every visual datum must carry one provenance class:

    SOURCE_TRUTH
    INFERRED_STRUCTURE
    GENERATED_CANDIDATE
    AUTHORED_HIDDEN_AREA
    HUMAN_APPROVED_DESIGN
    GOLDEN_REFERENCE

Rules:

- SOURCE_TRUTH is never overwritten by generated content.
- INFERRED_STRUCTURE may constrain geometry but is not automatically art truth.
- GENERATED_CANDIDATE has no authority until reviewed.
- A hidden/back design becomes character canon only after explicit human approval as HUMAN_APPROVED_DESIGN.
- Accepted design truth is frozen into a versioned GOLDEN_REFERENCE.
- Later model upgrades must not silently redesign an already approved hidden region.

This creates an explicit Character Design Truth layer between source truth and animation assets.

### 3. Reference precedence and contamination control

More references are not automatically better. Different references have different authority.

Default precedence:

    SOURCE / GOLDEN IDENTITY
      > APPROVED CHARACTER DESIGN TRUTH
      > CHARACTER DETAIL REFERENCES
      > STRUCTURE REFERENCES
      > TASK EXAMPLES
      > TEXT INSTRUCTIONS

A task example should communicate the operation, camera, crop, or desired organization, not donate identity/style details.

When possible:

- use silhouette/depth/normal/landmark guides instead of a full-color unrelated character;
- mask or simplify task examples to prevent hair/face/costume leakage;
- keep structure guidance style-neutral;
- reject candidates that copy distinguishing features from the task example.

### 4. Multi-view generation is a graph, not a one-way chain

Do not rely on a single 0 -> 45 -> 90 -> 135 -> 180 chain because errors accumulate.

Each view is a node in a reference graph. A target view may consume immutable source identity, approved neighboring views, the target structural reference, character detail references, and an approved far/opposite anchor when available.

Example for Aka 90:

    canonical 0
    + accepted 45
    + target 90 structural guide
    + face/hair/ear detail anchors
    + accepted 180 design anchor when available
    -> Aka 90 candidate set

After a complete set exists, run reverse and loop consistency checks:

    0 -> 45 -> 90 -> 135 -> 180
    180 -> 135 -> 90 -> 45 -> 0

A regenerated downstream view never automatically replaces the upstream Golden Reference that helped create it.

### 5. Candidate sets, ranking, and generation lineage

The generation unit is not one prompt -> one image. It is:

    task
    -> N candidates
    -> automated/visual comparison
    -> human selection
    -> accepted candidate
    -> frozen Golden version

For every candidate, retain lineage sufficient to reproduce or audit it:

    character_id
    task_id
    view/yaw
    provider
    model
    model_version/checkpoint
    seed when meaningful
    request/job id when meaningful
    prompt template version
    compiled prompt hash
    reference asset ids + hashes
    structure guide ids + hashes
    generation parameters
    timestamp
    parent candidate ids
    repair history
    QA results
    approval state

If a provider cannot expose a seed, preserve all identifiers and inputs it does expose.

### 6. Semantic correspondence is a graph, not a strict one-to-one mapping

A semantic part can split, merge, disappear, or be partially occluded between views.

The correspondence model must support at least:

    VISIBLE
    PARTIAL
    OCCLUDED
    SPLIT
    MERGED
    NOT_APPLICABLE

A stable semantic identity may map to multiple render fragments in a given view. UV/scaffold code must not assume one bitmap/mesh per semantic part at every angle.

### 7. Lighting and paint must be controlled separately

Cross-view source art must use a controlled visual-lighting contract.

Prefer a neutral/flat anime base, explicitly fixed key/fill lighting, or source-authored cel shadows that are declared part of the character texture.

Do not allow every generated view to invent independent highlights or shadows, because view switching would animate lighting discontinuously.

Runtime lighting/post effects must be distinguishable from baked character paint. If a shadow/highlight is intentionally baked, record that fact in metadata.

### 8. Asymmetry must be supported from the schema level

The first manual proof may render only one side, but the schema must not assume mirroring.

Support distinct signed views such as:

    -180 ... -135 -90 -45 0 +45 +90 +135 +180

Hair clips, earrings, ears, eye details, costume ornaments, scars, weapons, and other asymmetric elements may require independently authored left/right views.

Mirroring is an optimization only when an explicit symmetry rule permits it.

### 9. Identity references may include local high-resolution anchors

A single full-body/front image is not sufficient for all identity-sensitive operations.

The character package should support optional anchors:

    face_closeup
    eye_detail
    hair_detail
    ear_detail
    accessory_detail
    costume_detail
    hand_detail

These remain subordinate to source/golden truth but may be supplied to a generation or repair task when the full-frame reference does not preserve small features reliably.

### 10. Freeze states and versioning

Every important visual asset must have an explicit lifecycle:

    CANDIDATE
    REVIEWED
    APPROVED
    GOLDEN
    SUPERSEDED
    REJECTED

GOLDEN is immutable.

A corrected or redesigned view becomes a new version, for example Aka Reference Set v1 -> v2. Never overwrite an approved asset in place and never silently move a character to a new model-generated appearance.

### 11. Failure taxonomy and repair routing

A generic FAIL flag is insufficient. At minimum classify:

    IDENTITY_DRIFT
    VIEW_ANGLE_ERROR
    CAMERA_CROP_ERROR
    STRUCTURE_ERROR
    SILHOUETTE_ERROR
    STYLE_DRIFT
    COLOR_DRIFT
    DETAIL_LOSS
    PART_MISSING
    PART_DUPLICATED
    ASYMMETRY_ERROR
    OCCLUSION_ERROR
    HIDDEN_AREA_DESIGN_ERROR
    SEMANTIC_CORRESPONDENCE_ERROR
    TEMPORAL_POP
    SEAM_ERROR

The failure class determines the repair action: whole-view regenerate, local masked repair, strengthen identity references, replace structure guide, choose a different candidate, revise approved hidden design, or correct scaffold/visibility instead of repainting.

### 12. Reference Factory evidence must itself be versioned

Task examples, pass/fail examples, structural guides, camera metadata, and reference renderers are production dependencies.

Each Reference Atlas release must record:

- version;
- source provenance;
- source licenses;
- renderer/tool versions;
- camera contract version;
- semantic schema version;
- content hashes;
- changelog.

A reference update can invalidate previous QA thresholds. References are versioned inputs, not informal documentation.


## Additional closed-loop invariants: anchors, regional truth, dependency invalidation, compositing

The following contracts complete the asset model. They are required before scaling from the first Aka proof to multiple views, expressions, characters, or automated rebuilds.

### 13. Anchor Lattice: view, expression, and variant anchors

Character identity cannot be represented only by yaw.

The reusable reference model is a sparse **Anchor Lattice**:

    Character Identity
      x View Anchor
      x Expression Anchor
      x Part Variant

Do not materialize the full Cartesian product. Use a sparse graph of authoritative anchors.

Initial view anchors:

    0
    45
    90
    135
    180

Optional denser structural anchors:

    0
    22.5
    45
    67.5
    90
    112.5
    135
    157.5
    180

Initial expression anchors should remain minimal:

    neutral
    blink
    mouth_open
    smile

The first character proof only requires a complete neutral multi-view set. Expression anchors may be authored at selected views and propagated through the accepted rig/ArtMesh system later.

Part-variant anchors may include:

    eye_open / eye_closed
    mouth_closed / mouth_open
    front_hair_variant
    ear_variant
    accessory_variant

Every anchor must have a stable ID and explicit authority/provenance.

### 14. Canonicalization is explicit and reversible

The source artwork and the canonical model-sheet view are distinct assets.

Never modify SOURCE_TRUTH merely to make it easier for downstream models.

Record a reversible source -> canonical transform including, where applicable:

    source asset/version
    source rig parameters
    crop
    scale
    translation
    rotation
    camera/pivot
    background/alpha handling
    color-space conversion
    canonicalization tool/version

The canonical front used for generation is a derived reference asset, not a replacement for the original source.

### 15. Regional truth, authority, confidence, and uncertainty

Whole-image provenance is too coarse.

A single accepted view may contain regions with different authority levels. Provenance must therefore be available at semantic-part and, where useful, mask/pixel-region level.

Example:

    Aka_180
      rear_hair:
        authority = HUMAN_APPROVED_DESIGN
        confidence = 1.0
      ear_back_L:
        authority = AUTHORED_HIDDEN_AREA
        confidence = 0.92
      collar_hidden:
        authority = GENERATED_CANDIDATE
        confidence = 0.71
      palette:
        authority = SOURCE_TRUTH

Recommended fields:

    authority
    source_asset_ids[]
    source_region_ids[]
    confidence
    uncertainty
    editable
    locked
    approval_id
    notes

Optional confidence/uncertainty maps may be stored for generated geometry, masks, depth, or hidden-region completion.

Agent repair must preferentially modify low-authority / low-confidence regions and must not rewrite locked SOURCE_TRUTH or GOLDEN regions without an explicit new-version operation.

### 16. Asset Dependency DAG and invalidation

Lineage alone is insufficient. The build system must know when downstream assets are stale.

Represent the character build as a dependency DAG, for example:

    source_front
      -> golden_090_v1
      -> segmentation_090
      -> correspondence_v1
      -> scaffold_v3
      -> uv_v2
      -> turntable_v5

If a parent asset changes:

    golden_090_v1 -> golden_090_v2

all affected descendants must become:

    STALE

until explicitly rebuilt or revalidated.

Asset states therefore include at least:

    CURRENT
    STALE
    REBUILDING
    REVALIDATED
    SUPERSEDED

The dependency system must support:

- direct dependencies;
- transitive invalidation;
- dependency hashes;
- rebuild reasons;
- revalidation without rebuild when a change is proven irrelevant;
- reproducible rebuild ordering.

A stale downstream artifact must not be silently promoted, rendered, or used for production QA.

### 17. Stable semantic part identity across versions

Semantic role names alone are not stable enough.

Every persistent semantic part needs an immutable part UUID.

Example:

    part_uuid = hair.rear.cluster.03

If a later version splits or merges a part, record migration relations rather than silently renumbering:

    parent_part_uuid
    child_part_uuids[]
    split_from
    merged_from[]
    supersedes

Rig bindings, visibility rules, correspondence, and animation references must target stable semantic IDs/UUIDs rather than positional array indexes.

### 18. Compositing and appearance schema

A 2.75D character part is more than RGBA + mesh + UV.

The schema must preserve, where available:

    part_uuid
    semantic_role

    rgba
    lineart
    base_color
    baked_shadow
    emission
    normal_optional

    opacity
    blend_mode

    mask_sources[]
    mask_mode

    draw_order
    physical_depth

    alpha_mode
    underpaint_padding
    overscan

    authority_map
    confidence_map

Critical distinction:

    draw_order != physical_depth

2D authoring may intentionally place a part earlier/later for visual composition even when that order is not a physically correct Z relationship. Preserve both concepts independently.

### 19. Alpha, edge bleed, and hidden-underpaint safety

Generated or separated layers must not stop exactly at the visible mask boundary.

Every deformable/rotating layer needs configurable hidden margin:

    underpaint_padding
    edge_bleed
    overscan
    dilation_radius

The image contract must explicitly define:

    straight alpha vs premultiplied alpha
    RGB values under transparent pixels
    texture-border behavior
    filtering behavior

This prevents white/black fringes, transparent holes, and exposed empty pixels when a mesh deforms or rotates.

### 20. Line art and paint may be separate production stages

The workflow must support a conservative alternative to whole-image regeneration:

    structural guide
      -> accepted lineart / contour
      -> reference-guided color/detail transfer
      -> final candidate

This becomes the fourth Aka 90-degree experimental arm, **D**.

The purpose is to test whether preserving geometry/line structure first and transferring Aka color/detail second produces better identity retention than regenerating the entire view.

This is optional for production, but the asset schema must not force line art and color to be inseparable.

### 21. View-conditioned skin transition contract

View-specific textures require a deterministic runtime transition model.

Every view-conditioned part may define:

    support_yaw_range
    preferred_yaw
    blend_in_curve
    blend_out_curve
    visibility_curve
    seam_zone
    hysteresis
    fallback_view

Do not leave texture switching to ad-hoc runtime thresholds.

The transition model must be validated at anchor and mid-angle frames for:

    temporal popping
    double features
    seam exposure
    alpha discontinuity
    inconsistent baked lighting
    visibility inversion

### 22. Human review protocol must be reproducible

Human approval is the final artistic authority, but the review procedure itself must be controlled.

For A/B/C/D comparisons:

- use the same crop, scale, background, and target angle;
- use the same contact-sheet layout;
- randomize candidate order where practical;
- hide provider/model identity during first-pass visual ranking where practical;
- score the same dimensions for every candidate;
- record rejection reasons using the failure taxonomy;
- preserve the reviewed contact sheet and chosen candidate IDs.

Suggested review dimensions:

    identity
    angle accuracy
    silhouette
    facial structure
    hair structure
    ears/accessories
    costume
    asymmetry
    line quality
    color/palette
    hidden-region plausibility
    reference contamination

A human decision without the reviewed evidence/contact sheet is not sufficient for promotion to GOLDEN.


### 23. Evaluation Order and Transform Stack

Animation correctness depends on a deterministic evaluation order. Deformation systems must not independently mutate the same state in an undefined order.

The initial Koma evaluation contract is:

    Source Rest State
      -> source/native parameter deformation
      -> canonical 2D-to-2.75D correspondence
      -> character skeleton / FK / IK
      -> view-dependent surface deformation
      -> expression / eye / mouth / gaze controls
      -> constraints
      -> secondary motion (hair / ears / clothes)
      -> visibility / occlusion evaluation
      -> view-skin selection / blending
      -> compositing
      -> final render

This ordering is a starting contract, not a claim that every stage is already implemented. Any experimentally justified order change must be versioned.

Rules:

- the same vertex/parameter must not be deformed twice by two stages without an explicit composition rule;
- source INX deformation remains distinguishable from Koma skeleton deformation;
- camera yaw is not silently substituted for native source HeadYaw;
- physics operates on the already-defined upstream pose, not on stale/rest transforms;
- view-dependent texture selection occurs only after final visibility-relevant pose state is known;
- the complete transform/evaluation order is part of the asset/runtime version.

### 24. Rig, Bind Pose, Unit, and Constraint Contract

A rig is not only a bone name list.

Every rig profile must define:

    unit scale
    world axes
    canonical rest pose
    bind pose
    local bone axes
    parent hierarchy
    inverse bind transforms
    joint limits
    twist policy
    FK/IK ownership
    IK targets/poles
    constraint order
    retarget role mapping

For humanoid-compatible rigs, use one canonical semantic bone map so motions can be retargeted without relying on arbitrary source bone names.

The first Aka head-only proof may define only:

    root
    neck
    head
    ear_L
    ear_R
    selected hair controls

but the schema must already support the full contract.

A rig version change invalidates dependent skin weights, IK setups, motions, physics, and runtime QA unless explicitly revalidated.

### 25. ViewPose and CharacterPose Anchor Extension

The Anchor Lattice is extended from:

    View x Expression x Variant

to:

    ViewPose x CharacterPose x Expression x Variant

ViewPose may contain:

    yaw
    pitch
    roll
    camera distance
    orthographic scale or FOV
    camera target

CharacterPose may contain sparse authoritative poses such as:

    neutral
    head_turn_extreme
    look_up
    look_down
    arm_up
    sit
    walk_extreme

Do not build the Cartesian product.

For the first Aka proof, instantiate only:

    CharacterPose = neutral
    pitch = 0
    roll = 0
    yaw = target angle

The purpose of this schema is to prevent later head pitch/body-pose support from forcing a Reference Atlas redesign.

### 26. Expression Mixer and Secondary Motion Contract

Expression anchors alone are insufficient because expressions can overlap.

The runtime must define how these channels combine:

    blink
    eye gaze
    mouth/lip-sync
    smile/emotion
    brow
    source INX expression parameters
    procedural facial controls

Each expression control must define:

    target parts/parameters
    blend mode
    weight range
    priority
    override/exclusion relationships
    neutral/default value

Conflicting combinations must be detectable.

Secondary motion must also be deterministic. Hair, ears, clothing, and other spring/physics systems must define:

    fixed timestep
    substeps
    initialization pose
    warm-up frames
    reset behavior
    collision shapes
    damping/stiffness parameters
    deterministic seed if randomness exists

Physics state is runtime state and must not silently survive between reproducibility tests unless the test explicitly asks for continuity.

### 27. Surface Correspondence and Deformation Exposure Envelope

A view image cannot be treated as valid merely because a UV map exists.

Every view-to-surface binding must record how image regions correspond to the canonical surface:

    source view id
    target surface id
    vertex correspondences
    barycentric correspondences where used
    invalid/unmapped regions
    seam ownership
    mapping confidence
    fallback mapping
    visibility applicability

The source front UV remains immutable.

New view UV/correspondence must be independently versioned.

Hidden-region safety must be defined by a deformation exposure envelope, not only edge padding.

For each deformable part, estimate or test the maximum region that can become visible under the supported motion envelope:

    head yaw/pitch/roll
    approved expression extremes
    hair/ear spring extremes
    relevant body pose extremes

If motion can expose pixels outside accepted underpainting, the asset is incomplete even if the neutral anchor view looks correct.

Full 360 assets must also enforce cyclic consistency:

    +180 and -180 describe the same physical rear direction

and must not leave a hidden seam at the periodic boundary.

### 28. Reproducibility, Absolute Gate, Budget, and Scope Contract

Not every stage can promise the same reproducibility level.

Every generated/rebuilt asset must declare one of:

    BIT_EXACT
    INPUT_REPLAYABLE
    VISUALLY_REPRODUCIBLE
    NON_REPRODUCIBLE

Examples:

- deterministic structural/reference rendering should target BIT_EXACT where practical;
- external image generation may only be INPUT_REPLAYABLE or VISUALLY_REPRODUCIBLE;
- if a provider cannot replay equivalent inputs, declare NON_REPRODUCIBLE rather than implying determinism.

Provider input lineage must include the actual payload seen by the provider where observable:

    uploaded image dimensions
    provider-side or client-side resize
    crop
    mask
    reference ordering
    compression/transcode
    prompt
    model/version
    request/job identifiers

Candidate ranking requires an absolute acceptance gate.

The valid flow is:

    N candidates
      -> absolute quality gate
         -> zero pass: NONE_ACCEPTED
         -> one or more pass: ranking
      -> human review
      -> GOLDEN

The best candidate is not automatically acceptable.

Generation and repair loops must also have a budget policy:

    max_candidates
    max_repairs
    max_provider_cost
    max_iterations
    manual_escalation_reason

Exhausting the budget yields MANUAL_REVIEW_REQUIRED, not infinite retries.

Finally, every experiment/build must declare a scope profile:

    HEAD_ONLY
    UPPER_BODY
    FULL_BODY

Passing HEAD_ONLY never implies FULL_BODY acceptance.

### 29. Full-front source parity remains an explicit open gate

PR #31 establishes high-fidelity parity for the authentic Aka ear components across tested source HeadYaw poses. It does not establish whole-character default parity for all Aka ArtMeshes, masks, compositing, and full-puppet source rendering.

Therefore keep an explicit open gate:

    FULL_FRONT_SOURCE_PARITY

covering, at minimum:

    complete Aka front/default source pose
    all relevant ArtMeshes
    masks
    opacity
    blend/composite behavior
    full character transforms
    source textures
    final composed front render

Reference Factory experiments may proceed using authentic source/canonical art, but production acceptance of the full Koma character runtime must not claim front fidelity complete until this full-front gate passes.


### 30. Authoring Master and Runtime Package are separate artifacts

Koma must distinguish editable/source-of-truth assets from optimized runtime delivery assets.

The authoring package is authoritative:

    Koma Authoring Package
      source truth
      canonical/golden art
      PSD/INX and source decomposition
      masks/depth/normal/part maps
      correspondence
      scaffold source
      rig source
      lineage/dependency DAG
      provenance/licenses
      QA evidence

The runtime package is a deterministic derivative:

    Koma Runtime Package
      optimized geometry
      runtime textures
      rig/animation payloads
      view-skin tables
      expression/visibility/physics data
      runtime manifest
      dependency/version fingerprints

Rules:

- runtime optimization never overwrites Authoring Master data;
- compressed/quantized runtime assets never become new GOLDEN references;
- the build from Authoring Master -> Runtime Package must be reproducible/auditable;
- a runtime package records the exact authoring asset hashes from which it was built;
- rebuilding runtime derivatives after tool/runtime upgrades must not silently modify authoring truth.

### 31. Schema Migration and Runtime Compatibility Contract

Version numbers alone are insufficient. Koma packages must declare compatibility explicitly.

At minimum:

    package_schema_version
    authoring_schema_version
    runtime_manifest_version
    min_runtime_version
    max_tested_runtime_version
    required_features[]
    optional_features[]
    migration_history[]

Compatibility is fail-closed for required features.

If a runtime does not understand a required feature, it must reject the package with a machine-readable error rather than silently ignoring the field.

Schema migrations must:

- preserve stable asset/part UUIDs whenever semantics are unchanged;
- record source schema and target schema;
- be deterministic where practical;
- produce a migration report;
- invalidate affected downstream assets through the dependency DAG;
- never mutate an immutable GOLDEN version in place.

### 32. Golden Textures and Runtime Texture Derivatives

Golden visual assets are stored at authoring fidelity. Runtime textures may be resized, tiled, atlased, mipmapped, or compressed, but are derivative assets.

Record:

    master_texture_id
    master_texture_hash
    runtime_texture_id
    runtime_format
    compression_profile
    resize_policy
    mip_policy
    alpha_policy
    color_space
    fidelity_report

Anime line art, eyes, eyelashes, small accessories, and alpha edges are compression-sensitive. Runtime texture generation therefore requires visual regression QA.

Supported runtime formats are implementation choices, not source truth. KTX2/Basis-class GPU texture delivery may be used where appropriate, but the original lossless master remains authoritative.

### 33. Render State Contract

A correct texture/mesh is insufficient without the render state that produced the accepted appearance.

Version and record, where applicable:

    depth_test
    depth_write
    depth_func
    cull_mode
    alpha_test
    alpha_to_coverage
    blend_mode
    blend_equation
    blend_factors
    stencil/mask behavior
    polygon_offset
    MSAA/sample count
    texture filtering
    anisotropy
    texture wrapping
    mip policy
    tone mapping
    output color space
    post-processing chain

Reference renders and production renders must identify their render-state profile.

Changing a render-state profile may invalidate pixel/color QA even when geometry and textures are unchanged.

### 34. ReferenceCamera and SceneCamera are different concepts

The camera used to author or validate canonical views must not be conflated with the camera used by an animation scene.

Define:

    ReferenceCamera
      canonical generation/calibration camera
      exact yaw/pitch/roll
      projection
      scale/FOV
      pivot/target
      crop/canvas

    SceneCamera
      animation/cinematic camera
      free scene transform
      lens/projection
      framing
      camera animation

View-conditioned appearance must be chosen from the relative relationship between the final character/surface state and SceneCamera, not from a raw scene-camera yaw value alone.

Inputs may include:

    relative view direction
    surface normal
    final character pose
    expression state
    occlusion
    part-specific visibility
    approved skin support domain

### 35. Runtime Capability and Resource Budget Profiles

A character may be visually valid but operationally unusable on a target device.

Each Runtime Package must declare measured/expected resource requirements and a target capability profile.

Track at least:

    max_texture_dimension
    decoded_texture_memory
    geometry_memory
    draw_calls
    triangle_count
    bone_count
    active deformers
    morph targets
    simultaneously resident view skins
    preload/streaming memory
    shader/material count

Define quality/capability profiles such as:

    QUALITY_HIGH
    QUALITY_MEDIUM
    QUALITY_LOW

A lower profile may use derived runtime assets:

    lower texture resolution
    different compression
    fewer simultaneously resident views
    reduced secondary motion
    reduced optional effects

but may not replace the Authoring Master.

Performance acceptance should report:

    load time
    peak memory
    steady-state memory
    frame time / FPS
    dropped-frame behavior

for the declared target environment.

### 36. Deformer Stack is explicit per semantic part

Evaluation order is global; each part also needs a declared local deformer stack.

A part may use zero or more:

    INX_ARTMESH
    PARAMETRIC_MORPH
    MORPH_TARGET
    SKELETAL_SKINNING
    FFD
    VIEW_SURFACE
    PROCEDURAL_DEFORM
    PHYSICS

Example:

    front_hair:
      INX_ARTMESH
      -> SKELETAL_SKINNING
      -> VIEW_SURFACE
      -> PHYSICS

The stack must state which representation each stage reads/writes and whether it is additive, absolute, or constrained.

Do not assume every 2.75D part is bone-skinned. Some facial/line-art parts may remain ArtMesh/morph-driven while hair/body use different stacks.

### 37. Canonical Expression Vocabulary

Expression channels need stable semantic names so rigs and motions can be retargeted.

Initial vocabulary should support at least:

    blink
    blink_L
    blink_R

    look_L
    look_R
    look_U
    look_D

    aa
    ih
    ou
    ee
    oh

    happy
    angry
    sad
    relaxed
    surprised

A character may map these semantic channels to source INX parameters, morphs, texture swaps, ArtMesh deforms, or procedural controls.

The expression mixer defines:

    semantic channel
    target bindings
    weight conversion
    priority
    override group
    exclusion group
    fallback

Character-specific extra expressions may extend the vocabulary without changing the standard semantics.

### 38. Motion Clip Contract

A reusable motion is more than animation curves.

Each motion clip should declare:

    motion_id
    rig_profile
    duration
    timebase/fps
    loop_mode
    in_place_or_root_motion
    root_trajectory
    keyframe/interpolation policy
    transition_in
    transition_out
    contact events
    foot/hand lock windows where relevant
    event markers
    required expression channels
    required secondary-motion behavior
    source/provenance
    retargeting status

Motion acceptance must distinguish:

    source motion fidelity
    retarget fidelity
    character-specific artistic adjustment

A generic retargeted motion is not automatically accepted for a production shot.

### 39. Renderer and Encoder Environment Fingerprint

Visual/video evidence must identify the environment that produced it.

Record, where observable:

    OS
    browser/version
    Three.js version
    runtime commit
    WebGL/WebGPU backend
    GPU/vendor/device
    renderer capabilities/limits
    devicePixelRatio
    canvas resolution
    FFmpeg version
    codec
    codec profile
    pixel format
    color primaries
    transfer characteristics
    matrix
    full/limited range

A video acceptance result is tied to this fingerprint.

Changing renderer/backend/encoder may require revalidation even when source assets are unchanged.

### 40. Generalization Gate beyond Aka

Aka is the first proof character, not proof that the Reference Factory generalizes.

After the complete Aka manual path succeeds, validate at least one structurally different second character without redesigning the core schema.

Prefer differences such as:

    different face shape
    different hair topology
    obvious left/right asymmetry
    different accessory placement
    different costume silhouette

Midori or another license-clear character is a suitable candidate if provenance permits.

The Reference Factory is considered generalized only if the second character can pass through the same contracts with configuration/data changes rather than architecture rewrites.

### 41. Asset Load Failure and Runtime Fallback Policy

Runtime degradation must be explicit.

Possible policies include:

    FAIL_CLOSED
    FALLBACK_NEAREST_VIEW
    FALLBACK_SOURCE_FRONT
    DISABLE_OPTIONAL_PART
    DISABLE_OPTIONAL_EFFECT
    FALLBACK_LOWER_QUALITY_PROFILE

Each asset/feature declares which policy is allowed.

Examples:

- missing required face skin -> FAIL_CLOSED;
- unavailable optional high-resolution texture -> fallback lower-quality derivative;
- unsupported optional secondary-motion system -> disable only if the package marks it optional;
- missing/corrupt mask required for compositing -> FAIL_CLOSED.

The runtime must emit structured diagnostics and must never silently fabricate a fallback that changes approved character identity.

### 42. glTF carries standard transport data; Koma manifest carries Koma semantics

Use standard GLB/glTF capabilities for standard geometry/animation transport where practical:

    mesh
    material
    skin
    morph target
    ordinary node transforms
    texture references

Keep Koma-specific behavior in a versioned Koma Runtime Manifest:

    view-conditioned skins
    visibility rules
    semantic part graph
    correspondence
    Anchor Lattice bindings
    expression mixer
    evaluation order
    physics configuration
    provenance/dependencies
    fallback policies
    capability profile

Do not make the core architecture depend on optional ecosystem support for animating arbitrary glTF extension properties.

If a standard extension such as KHR_animation_pointer becomes universally supported by the selected runtime stack, Koma may add an adapter or export path, but the canonical Koma semantics remain independent and versioned.


### 43. Topology, Vertex Identity, and Topology Migration

A semantic part UUID is not sufficient to preserve geometry-dependent bindings. Every persistent surface must also have explicit topology identity.

Record:

    surface_id
    part_uuid
    topology_id
    topology_version
    topology_hash
    vertex_count
    face_count
    vertex_ids[]
    face_ids[]

Bindings that depend on topology include:

    UVs
    skin weights
    morph targets
    FFD cages/bindings
    view/surface correspondence
    seam ownership
    visibility masks projected to surface
    LOD transfer maps

A topology change is not an ordinary asset revision.

If:

    head_surface_v1
      -> retopology
      -> head_surface_v2

the migration record must contain, where possible:

    source_topology_id
    target_topology_id
    vertex_remap
    face_remap
    surface/barycentric transfer map
    unmapped regions
    transfer confidence
    migration report

All topology-dependent descendants become STALE unless explicitly transferred and revalidated.

Never assume vertex array order is a stable identity across topology versions.

### 44. Persistent Artifact Registry and Retention Contract

Actions artifacts are temporary CI/review outputs, not permanent storage for SOURCE_TRUTH, GOLDEN, or Reference Atlas binaries.

Every non-Git binary asset must have a machine-readable registry record:

    asset_id
    asset_version
    sha256
    byte_size
    mime_type
    logical_role
    provenance_class
    retention_class
    primary_locator
    mirror_locator_optional
    created_at
    source/license metadata
    availability_status

Retention classes:

    EPHEMERAL
    REVIEW
    GOLDEN
    SOURCE_TRUTH

Recommended policy:

    EPHEMERAL
      CI workspace / Actions artifact

    REVIEW
      Actions artifact and/or Draft Release

    GOLDEN
      persistent asset location + manifest hash

    SOURCE_TRUTH
      persistent asset location + manifest hash + independent backup/mirror where practical

Git stores identifiers, hashes, provenance, and locators; it does not need to store large binaries.

Rules:

- an asset is not considered safely frozen merely because an Actions run once uploaded it;
- every GOLDEN/SOURCE_TRUTH binary must be retrievable from a persistent locator;
- missing persistent binaries make dependent builds UNAVAILABLE, not silently regenerated;
- moving storage must preserve asset_id and content hash;
- storage migration must produce an audit record.

### 45. Package Integrity and Conformance Validator

No .koma-character or Runtime Package may be loaded for production use before conformance validation.

Provide a machine-readable validator contract, conceptually:

    koma validate <package>

Validation must cover at least:

    manifest/schema compatibility
    required feature support
    file existence
    content hashes
    asset registry resolution
    dependency freshness
    stable part UUID references
    topology hashes
    topology-dependent binding compatibility
    rig/bind compatibility
    expression bindings
    surface correspondence
    render-state profile
    texture derivative/master links
    capability profile
    fallback policy
    provenance/license records where required
    package integrity

Representative errors:

    E_SCHEMA_UNSUPPORTED
    E_REQUIRED_FEATURE_UNSUPPORTED
    E_HASH_MISMATCH
    E_ASSET_UNAVAILABLE
    E_DEPENDENCY_STALE
    E_PART_UUID_MISSING
    E_TOPOLOGY_MISMATCH
    E_BINDING_TOPOLOGY_MISMATCH
    E_RIG_BIND_MISMATCH
    E_CORRESPONDENCE_STALE
    E_TEXTURE_PROFILE_UNSUPPORTED
    E_RENDER_PROFILE_UNSUPPORTED
    E_FALLBACK_ILLEGAL

Identity-critical or structural integrity failures are fail-closed.

The validator itself is versioned, and validation reports are retained as QA evidence.

### 46. Hermetic Toolchain Lock and Build Provenance

An environment fingerprint describes what happened; a hermetic build contract defines what must happen again.

Maintain a toolchain/build lock containing exact or digest-pinned dependencies where practical:

    Node version
    package-manager version
    JS lockfile hash
    Three.js exact version/commit

    Rust toolchain
    Cargo.lock hash

    Python version
    Python lockfile hash

    FFmpeg version/build
    texture encoder/transcoder version
    geometry optimizer version

    container image digest
    OS/base image digest

    AI model/checkpoint revision and SHA256 where available
    external model/code commit
    downloaded dependency hashes

Every Runtime Package build records:

    build_id
    source_commit
    authoring_package_hash
    toolchain_lock_hash
    container_digest
    resolved_dependencies[]
    build_parameters_hash
    input_asset_hashes[]
    output_asset_hashes[]
    builder/runtime version
    build_timestamp

Borrow the useful ideas of software supply-chain provenance without requiring full external certification.

Cache reuse is allowed only when the complete cache key contract matches.

Recommended cache key inputs:

    source/input hashes
    schema version
    toolchain lock hash
    build config hash
    renderer/profile version
    relevant model/checkpoint hash

A cache hit must never bypass conformance validation.

### 47. LOD, Texture Atlas, and Other Runtime Derivative Mapping

Performance derivatives must remain traceable to Authoring Master data.

Geometry LOD example:

    Authoring Surface
      -> LOD0
      -> LOD1
      -> LOD2

Each LOD records:

    source_topology_hash
    lod_topology_hash
    generation_tool/version
    reduction parameters
    vertex/surface transfer map
    weight transfer
    UV transfer
    semantic part preservation
    silhouette/error metrics
    fidelity QA

Changing LOD topology does not change the Authoring Master topology.

Texture atlas/repacking example:

    Master texture + Master UV
      -> runtime atlas packing
      -> atlas UV transform

Record:

    source_texture_ids[]
    source_uv_profile
    atlas_id
    atlas_region_map
    UV transform per source region
    padding/gutter
    mip policy
    compression profile
    fidelity QA

Runtime atlas UVs are derivatives. They never replace source/front UV0 or Golden authoring UVs.

The same rule applies to mesh quantization, geometry compression, texture transcoding, shader specialization, and baked runtime caches.

### 48. Release Channels, Rollback, and Conformance Matrix

Versioned assets need explicit release state and rollback semantics.

Recommended package channels:

    CANDIDATE
    REVIEW
    STABLE
    REJECTED
    SUPERSEDED

A release record contains:

    release_id
    package_version
    authoring_package_hash
    runtime_package_hash
    schema versions
    toolchain/build provenance
    conformance report id
    QA report ids
    target capability profiles
    previous_stable_release
    rollback_target
    release notes

Promotion to STABLE requires all mandatory gates for the declared scope.

Rollback must be atomic at the package level: do not mix files from old/new runtime packages.

Maintain a conformance matrix across supported environments/profiles, for example:

    package version
    runtime version
    browser/backend
    capability profile
    validator version
    result
    known limitations

A new runtime, schema migration, renderer backend, or major toolchain update must run the applicable conformance matrix before replacing the previous stable baseline.

The existence of a newer CANDIDATE never invalidates the last known-good STABLE package unless its Authoring Master dependencies themselves have been explicitly revoked.

## Reference Factory instead of one universal reference character

A single Seed-san/VRM character is useful for smoke tests but is too narrow to serve as the universal reference. The preferred long-term design is a small **Reference Factory** built from license-clear source assets that can deterministically produce task-specific reference material.

### Source truth classes

| Class | Initial source | Role |
|---|---|---|
| 2D animation truth | Inochi2D Aka / Midori INX + PSD | Real layered art, ArtMesh, UV, node hierarchy, parameter deformation, source-render comparison |
| Character design truth | Human-approved side/back/hidden-region designs derived from generated candidates | Canonical appearance for information not present in source truth; versioned and frozen after approval |
| 3D structure truth | Small VRoid/VRM sample bank with clear reuse terms, prioritizing CC0 samples | Exact camera/yaw renders, silhouette, depth, normal, body/head/hair structure, humanoid skeleton baseline |
| Layer/occlusion candidate | See-through | Candidate semantic RGBA layers, occluded-region completion, pseudo-depth/drawing order; must be benchmarked against real Aka PSD/INX |
| Multi-view structure candidate | MV-Adapter | Geometry-consistent view candidates and structural guidance; not accepted as final art without visual QA |
| Anime geometry research | PAniC-3D, CharacterGen, StdGEN; track SeparateGen | Geometry priors and canonical multi-view/component ideas; auxiliary only |
| Hair research | CHARM / AnimeHair workflow | Hair-card / strand-structure references and hairstyle priors |
| Rig research | UniRig, Make-It-Animatable, DRiVE | Skeleton/weight references after visual asset path is stable |
| Multi-view QA research | MEt3R, MVGBench-style metrics | Quantitative assistance for consistency; never substitutes direct rendered-frame review |
| Final visual repair | high-quality reference-conditioned image editing | Identity/style/art repair after structural view generation |

### Research references

- Inochi2D example models: <https://github.com/Inochi2D/example-models>
- See-through: <https://github.com/shitagaki-lab/see-through>
- MV-Adapter: <https://github.com/huanngzh/MV-Adapter>
- PAniC-3D: <https://github.com/ShuhongChen/panic3d-anime-reconstruction>
- StdGEN: <https://github.com/hyz317/StdGEN>
- CHARM: <https://github.com/hyz317/CHARM>
- CharacterGen project: <https://zjp-shadow.github.io/publications/charactergen/>
- Make-It-Animatable paper: <https://arxiv.org/abs/2411.18197>
- UniRig paper: <https://arxiv.org/abs/2504.12451>
- DRiVE paper: <https://openaccess.thecvf.com/content/CVPR2025/html/Sun_DRiVE_Diffusion-based_Rigging_Empowers_Generation_of_Versatile_and_Expressive_Characters_CVPR_2025_paper.html>
- MEt3R paper: <https://openaccess.thecvf.com/content/CVPR2025/html/Asim_MET3R_Measuring_Multi-View_Consistency_in_Generated_Images_CVPR_2025_paper.html>
- MVGBench paper: <https://openaccess.thecvf.com/content/ICCV2025/html/Xie_MVGBench_a_Comprehensive_Benchmark_for_Multi-view_Generation_Models_ICCV_2025_paper.html>

These are research inputs, not declarations that every repository/checkpoint is already integrated or redistribution-safe. Check model/checkpoint/data licenses separately before promotion into production artifacts.

## Reference Factory outputs

The factory should be able to create deterministic structural references independent of the current production character.

For 0-180 degrees, produce at least nine structural anchors:

```text
0
22.5
45
67.5
90
112.5
135
157.5
180
```

For every anchor, prefer:

```text
beauty/reference render
silhouette
depth
normal
part-ID / semantic map
wireframe where useful
landmarks
camera metadata
```

The first production-facing visual set may still use only:

```text
0 / 45 / 90 / 135 / 180
```

The denser structural set exists to constrain intermediate views and later continuous turning.

## Proposed Reference Atlas

The reusable output of the factory is not one character. It is a library of accepted examples by operation:

```text
reference-atlas/
  anchors/
    views/
      000/
      045/
      090/
      135/
      180/
    expressions/
      neutral/
      blink/
      mouth-open/
      smile/
    poses/
      neutral/
      head-turn-extreme/
      look-up/
      look-down/
    variants/
  views/
    000/
    045/
    090/
    135/
    180/
  structural/
    silhouette/
    depth/
    normal/
    landmarks/
    camera/
  segmentation/
    examples/
    semantic-maps/
    masks/
  correspondence/
    examples/
  scaffold/
    examples/
    wireframe/
  hair/
    short/
    long/
    bangs/
    ponytail/
    twintail/
  rig/
    skeleton/
    weights/
  motion/
    head-turn/
    idle/
  identity/
    face/
    hair/
    ears/
    accessories/
    costume/
  design-truth/
    approved-hidden-regions/
    asymmetry/
  lineage/
  dependencies/
  evaluation/
  rig-contract/
  surface-correspondence/
  reproducibility/
  authoring-package/
  runtime-package/
  schema-migrations/
  render-profiles/
  capability-profiles/
  motion-contracts/
  environment-fingerprints/
  fallback-policies/
  topology/
  artifact-registry/
  conformance/
  toolchain-lock/
  build-provenance/
  lod-derivatives/
  release-channels/
  compositing/
  regional-truth/
  qa/
    pass/
    fail/
    taxonomy/
```

Each task reference should show both **what is correct** and, where useful, common failure modes.

## Standard character build data flow

```text
source PSD / INX / canonical art
        |
        v
identity freeze
        |
        +----------------------+
        |                      |
        v                      v
reference factory         task examples
(structure truth)         (accepted visual truth)
        |                      |
        +----------+-----------+
                   v
          N-view candidate generation
                   |
                   v
             cross-view QA/ranking
            /                 \
         SELECT              REJECT/REPAIR
          |                       |
          |                region/view repair
          |                       |
          +-----------<-----------+
                   |
                   v
          human design acceptance
                   |
                   v
          versioned GOLDEN views
                   |
                   v
           semantic decomposition
                   |
                   v
         cross-view part correspondence
                   |
                   v
        minimal 2.5D spatial scaffold
                   |
                   v
            0-180 turn validation
                   |
                   v
             rig / weights / IK
                   |
                   v
                motion
                   |
                   v
          workflow automation
```

## Manual-first validation plan

Do **not** build the final orchestration layer first. The workflow must be manually demonstrated end to end and only then consolidated.

### Phase M0 — Freeze the source character

Use Aka first.

Required inputs:

- original Aka INX;
- original textures / PSD;
- one canonical front render from the known source pose;
- fixed neutral expression;
- fixed canvas, crop, camera convention, and scale;
- explicit coordinate/yaw/image/color-space contract;
- a reversible source -> canonical transform manifest;
- declared scope profile (HEAD_ONLY / UPPER_BODY / FULL_BODY);
- declared reproducibility level for each pipeline stage;
- declared authoring/runtime schema versions and compatibility policy;
- declared topology identity/version policy for persistent surfaces;
- declared persistent binary-asset registry/retention policy;
- declared ReferenceCamera profile distinct from future SceneCamera behavior;
- a written character-fact checklist for face, hair, ears, accessories, clothing, and asymmetries;
- optional high-resolution identity anchors for face/hair/ears/accessories where needed.

Acceptance:

- the canonical front is the identity authority;
- source references and exact source pose are recorded;
- subsequent generated views cannot silently redefine character features.

### Phase M1 — Build the minimal reference source bank

Start small:

- Aka and Midori for 2D truth;
- a small license-clear VRM/VRoid sample set for 3D truth;
- at least one female and one male hair/character structure example if licensing permits.

Do not download a huge VRoid corpus yet. A small source bank is enough to validate the factory concept.

Acceptance:

- every retained source has provenance and license notes;
- source binaries remain outside normal Git blobs when required by repository policy;
- a source can be rendered reproducibly.

### Phase M2 — Deterministic structure renders

Render the reference 3D assets with one fixed camera convention at nine yaw angles.

For each yaw, produce structural maps such as silhouette, depth, normal, landmarks, and optional part IDs.

Acceptance:

- yaw/camera/crop are exact and machine-recorded;
- repeated render produces identical output under the same environment;
- 90 degrees is an actual defined camera/character yaw, not a hand-selected "looks sideways" image.

### Phase M3 — Benchmark semantic decomposition on Aka

Run a candidate decomposition method such as See-through on a flattened/canonical Aka image, then compare it with the real Aka PSD/INX decomposition.

Measure/inspect:

- face mask;
- front/back hair separation;
- ears;
- eyes/mouth;
- body/clothing;
- hidden-region completion;
- drawing order / pseudo-depth.

Acceptance:

- publish the actual comparison sheet and failure cases;
- do not treat a generated PSD as correct merely because layers exist.

### Phase M4 — One-angle A/B/C/D experiment: Aka 90 degrees

Before generating the entire turnaround, isolate one difficult target: 90 degrees.

Run at least:

**A. image-edit / identity model only**

```text
Aka identity + textual view instruction
-> Aka 90
```

**B. multi-view/structure model only**

```text
Aka canonical input
-> structurally generated Aka 90 candidate
```

**C. structure first, art second**

```text
Aka identity
+ accepted 90-degree task example
+ 90-degree structural candidate / silhouette / depth
-> high-fidelity Aka 90 repair/refinement
```

**D. structure/lineart first, reference-guided color/detail transfer**

```text
90-degree structural guide
-> accepted 90-degree lineart/contour
+ Aka source color/detail references
+ semantic correspondence controls
-> Aka 90-degree colored candidate
```

Keep the target crop/angle/output contract identical across A/B/C/D.

Generate a candidate set for each arm rather than relying on one sample. Preserve regional authority/confidence metadata when repairs or transfers combine multiple sources. Persist provider/model/checkpoint, prompt/reference hashes, actual provider payload metadata where observable, parameters, parent/repair lineage and QA results for every candidate.

Before ranking, apply an absolute quality gate. If no candidate passes, record NONE_ACCEPTED and escalate/retry within the configured generation budget; never promote the least-bad image merely because it ranks first.

Acceptance criteria:

- identity stability;
- facial proportions;
- nose/mouth/eye placement;
- skull/back-head thickness;
- front/side/rear hair logic;
- fox-ear structure and occlusion;
- accessory persistence;
- clothing persistence;
- line/shading/palette fidelity;
- actual 90-degree orientation.

The preferred production path is chosen from measured output, not from model reputation.

### Phase M5 — Expand only after 90-degree acceptance

After a 90-degree method passes, create:

```text
0 / 45 / 90 / 135 / 180
```

Use adjacent accepted views as additional references, but never as the sole identity source. Multi-view generation must follow the reference-graph rule: every target remains anchored to immutable source/golden identity and its target structural guide, so drift cannot propagate unchecked from one generated view to the next.

Example:

```text
Aka front + accepted 45 + 90 task/structure reference
-> 90
```

and later:

```text
accepted 90 + accepted 135 + source identity
-> 180
```

Acceptance:

- five-view contact sheet passes direct human inspection;
- no major identity, costume, hairstyle, proportion, palette, or line-style drift;
- side/back hidden regions are internally plausible.

### Phase M6 — Semantic part split and correspondence

Only after the five views are accepted, split into a minimal first semantic set:

```text
face
front_hair
rear_hair
ear_L
ear_R
body
major_accessory
```

Then establish the same stable semantic part UUIDs across views and versions.

Acceptance:

- one part can be traced across visible views;
- disappearance/reappearance is explicit, not accidental;
- overlap and front/back ordering are recorded;
- correspondence explicitly supports VISIBLE / PARTIAL / OCCLUDED / SPLIT / MERGED / NOT_APPLICABLE.

Do not start with dozens of micro-parts.

### Phase M7 — Minimal spatial scaffold

Fit the smallest structure needed for correct spatial reasoning:

- head / skull proxy;
- face shell;
- front-hair shell(s);
- rear-hair shell(s);
- ears;
- minimal neck/body proxy.

This is **not** a traditional full character-modeling milestone. Geometry exists to provide:

- depth;
- visibility;
- occlusion;
- surface orientation;
- continuous interpolation support.

Acceptance:

- scaffold dependencies point to the exact Golden views, masks, correspondence graph, and schema versions;
- 0-degree source view remains high-fidelity;
- front/back occlusion is correct at anchor angles;
- no requirement to create a production-quality closed 3D avatar.

### Phase M8 — First continuous motion: head turn only

Before IK or full-body motion, render:

```text
0 -> 45 -> 90 -> 135 -> 180
```

Inspect at least:

```text
0
22.5
45
67.5
90
112.5
135
157.5
180
```

Check:

- identity jumps;
- double facial features;
- hair popping;
- missing ears/accessories;
- seam/texture switching;
- bad occlusion;
- depth inversion;
- silhouette discontinuity;
- view-conditioned texture blend/visibility curve failures;
- alpha-edge/underpaint exposure.

Acceptance requires decoded video and extracted-frame inspection, not merely successful encoding. The test must record fps/timebase, evaluation-order version, view-skin transition version, render-state profile, runtime capability profile, renderer/encoder environment fingerprint, and deterministic physics/reset state if secondary motion is enabled.

### Phase M9 — Rig, weights, IK, then motion

Only after the static/multi-view/turn path is accepted:

1. head/neck;
2. ear and hair controls;
3. facial controls;
4. torso/shoulder/arm/hand/leg;
5. IK;
6. reusable motion references.

Rigging research projects such as UniRig, Make-It-Animatable, and DRiVE may provide reference skeletons/weights, but must be fitted and visually verified against the accepted Koma character asset.

Before accepting rigged motion, freeze the rig contract: unit scale, rest/bind pose, bone local axes, inverse bind transforms, joint limits, IK ownership/targets, retarget semantic map, canonical expression vocabulary/mixer rules, secondary-motion update/reset behavior, and the Motion Clip Contract.

### Phase M10 — Automation last

Only now convert proven manual actions into:

- prompt/reference templates;
- provider adapters;
- retry policies;
- semantic schemas;
- deterministic rendering jobs;
- automated QA;
- deterministic Authoring Master -> Runtime Package build;
- runtime texture/geometry optimization profiles;
- schema migration tooling;
- topology migration/transfer tooling;
- persistent artifact registry resolution;
- package conformance validator;
- hermetic toolchain/build lock and cache-key generation;
- capability/fallback validation;
- release/rollback tooling;
- `koma character build ...` orchestration.

The Agent may choose a repair strategy, but it must not invent the production process ad hoc.

## QA hierarchy

QA is layered:

1. **Human visual acceptance** — final authority for character identity and artistic correctness.
2. **Reference comparison** — pass/fail examples for each operation, with a stable failure taxonomy and repair route.
3. **Structural checks** — yaw, camera, silhouette, depth, landmarks, semantic masks, part ordering, regional authority/confidence and dependency freshness.
4. **Cross-view consistency metrics** — research metrics such as MEt3R-style comparison where practical.
5. **Runtime/video checks** — decoded frame inspection at anchors and mid-angles.

A passing automated metric never upgrades a visually broken result to accepted.

## Reference-example policy

Every standardizable operation should eventually have:

```text
input example
accepted output example
optional rejected examples
structure guide
metadata describing the exact task, coordinate/camera/color contract, authority/precedence, regional truth/confidence, dependency version, and reference version
```

Examples are preferable to prose when an exact visual result is important.

This applies to:

- view generation;
- segmentation;
- hidden-region completion;
- semantic correspondence;
- scaffold fitting;
- rig placement;
- skin weights;
- IK poses;
- motion;
- QA.

## Storage policy

Continue repository policy from ADR-002:

**Git may contain**

- code;
- schemas;
- manifests;
- prompts/reference metadata;
- provenance;
- licenses/URLs;
- QA reports;
- numeric metrics;
- small text fixtures.

**Do not commit large/source art binaries as normal Git blobs.**

Use GitHub Actions artifacts and owner-only Draft Releases for binary research material when appropriate.

For external datasets/models:

- record source URL;
- record exact version/commit/checkpoint;
- record license;
- record whether redistribution is allowed;
- distinguish code license from checkpoint/data license;
- record provider/model/checkpoint, prompt template version, reference/content hashes and generation lineage for generated candidates;
- version Reference Atlas releases and never mutate GOLDEN assets in place;
- persist dependency hashes and STALE/revalidation state;
- preserve stable part UUID migration records across split/merge changes;
- record evaluation-order, rig-contract, expression-mixer, surface-correspondence, timebase, scope-profile and reproducibility versions;
- record actual provider payload transforms (resize/crop/mask/reference ordering/compression) where observable;
- preserve Authoring Master hashes separately from Runtime Package derivative hashes;
- record schema compatibility/migration history;
- record render-state, runtime capability, fallback-policy and environment-fingerprint versions;
- retain texture compression/resizing/mipmap fidelity reports;
- never rely on expiring CI artifacts as the only copy of GOLDEN/SOURCE_TRUTH binaries;
- maintain persistent asset registry records for all non-Git GOLDEN/SOURCE_TRUTH files;
- record topology IDs/hashes and migration reports;
- record toolchain-lock/build-provenance hashes and conformance-validator reports;
- record LOD/atlas derivative mapping and release/rollback metadata.

## What is deliberately NOT decided yet

The following remain experimental until the manual path proves them:

- See-through as the final production semantic decomposer;
- MV-Adapter as the final production multi-view generator;
- any specific GPT/image-edit model as a permanent provider;
- exact number of final production views;
- exact semantic part granularity;
- exact scaffold topology;
- exact automatic rigging system;
- final evaluation order refinements after real motion tests;
- exact full-body humanoid bone/retarget profile;
- final expression mixing policy after facial-motion tests;
- final physics system and parameters;
- final runtime texture compression/profile policy after fidelity/performance tests;
- final device capability tiers and budgets;
- final GLB/Koma-manifest packaging details;
- final persistent binary storage backend, while the registry/retention contract remains fixed;
- final topology simplification/LOD algorithms;
- final software-BOM/provenance interchange format;
- whether SeparateGen or later component-aware methods replace any current candidate.

The architecture intentionally makes these replaceable.

## Immediate experiment sequence after the existing CORE-021

**Numbering correction:** PR #31 already owns `CORE-021` for authentic Aka source GPU/CPU parity. This ADR must not reuse that milestone number. The Reference Factory/manual character-build work starts **after CORE-021**, nominally at `CORE-022+`, unless later split into a separate `REF-xxx` / `CHAR-xxx` track.

The next work should be ordered as follows:

1. freeze the coordinate/yaw/camera/image/color-space contract, canonicalization manifest, ViewPose/CharacterPose Anchor Lattice schema, scope profile, reproducibility levels, evaluation-order contract, and asset lifecycle/provenance schema;
2. inventory and provenance for Aka/Midori + small VRM/VRoid reference bank;
3. render nine-yaw structural references with fixed, machine-recorded camera metadata;
4. benchmark Aka flatten -> semantic decomposition -> compare with real PSD/INX;
5. prepare one accepted generic 90-degree task example and neutral structural guide that cannot donate identity;
6. define Aka source truth, optional detail anchors, and the policy for human-approved hidden/back design truth;
7. run Aka 90-degree A/B/C/D comparison using N candidates per arm, regional truth/confidence, and full lineage metadata;
8. inspect actual candidates with the controlled human-review protocol, classify failures, select and freeze the first accepted Aka 90-degree Golden view;
9. create the dependency DAG and verify that changing the Golden 90-degree parent marks dependent masks/correspondence/scaffold/UV/video artifacts STALE;
10. define and test the 90-degree view-to-surface correspondence record, including mapping confidence and invalid/seam regions;
11. only then generate 45/135/180 using the non-linear reference graph and create a five-view contact sheet;
12. run reverse/loop consistency checks, explicitly inspect asymmetries, and reserve the +180/-180 cyclic seam contract for later 360 validation;
13. only after five-view acceptance begin stable-UUID semantic correspondence and spatial scaffold work;
14. before rig/IK promotion, freeze rig/bind/expression/timebase/physics contracts and verify deformation exposure envelopes;
15. before full runtime promotion, complete FULL_FRONT_SOURCE_PARITY for the whole Aka front/default composition, not only the ear subset;
16. define Authoring Master -> Runtime Package build, schema compatibility/migration, render-state profile, runtime texture derivative policy, capability budget, and fallback behavior;
17. fingerprint the accepted renderer/encoder environment and run performance/memory QA for the selected capability profile;
18. define topology/vertex identity and prove that a topology revision invalidates or explicitly migrates all dependent UV/weight/morph/correspondence assets;
19. establish the persistent artifact registry and verify GOLDEN/SOURCE_TRUTH binaries remain retrievable independently of expiring CI artifacts;
20. implement/run package conformance validation, including hash/topology/dependency/rig/render/capability checks;
21. lock the toolchain/build provenance and verify a clean rebuild of the same Runtime Package inputs produces an auditable equivalent result;
22. validate one LOD/atlas derivative path without mutating Authoring Master UV/topology;
23. define STABLE/CANDIDATE release metadata and execute one package-level rollback test;
24. after Aka passes end to end, run a second structurally different license-clear character through the same contracts as a Generalization Gate.

**Do not proceed to rig/IK automation before this chain is visually demonstrated.**

## Promotion criterion

This ADR moves from PROPOSED to ACCEPTED FOR CHARACTER-BUILD RESEARCH only after the repository contains reproducible evidence for:

- one versioned coordinate/camera/image/color-space contract plus reversible canonicalization manifest;
- one versioned ViewPose/CharacterPose/Expression/Variant Anchor Lattice definition;
- one versioned asset lifecycle / lineage / provenance schema with regional authority/confidence;
- one deterministic Reference Factory structural render set;
- one Aka semantic-decomposition comparison against real source layers;
- one A/B/C/D Aka 90-degree comparison using candidate sets, absolute acceptance gates, generation budgets, and controlled human review;
- one explicitly approved Aka 90-degree Golden view with source/design-truth provenance;
- an accepted five-view Aka reference set with asymmetry and reverse/loop consistency review;
- documented failure taxonomy, representative rejected examples, and chosen repair strategies;
- semantic correspondence capable of split/merge/occlusion states with stable part UUIDs;
- a working dependency invalidation proof that marks descendants STALE when a Golden parent changes;
- a compositing/appearance schema preserving draw order separately from physical depth, blend/mask/alpha semantics, and hidden underpaint margins;
- a deterministic view-conditioned texture transition contract;
- a versioned evaluation-order/transform-stack contract;
- a rig/bind/unit/constraint and expression-mixer contract before accepting rigged motion;
- one surface-correspondence record with mapping confidence, invalid regions, seam ownership, and deformation exposure envelope;
- declared reproducibility level and scope profile for every promoted artifact;
- an explicit Authoring Master -> Runtime Package boundary with deterministic derivative hashes;
- schema compatibility and migration rules with fail-closed required features;
- Golden-vs-runtime texture derivative policy with visual fidelity QA;
- versioned render-state profile and ReferenceCamera/SceneCamera separation;
- a declared runtime capability/resource budget and measured performance/memory report;
- explicit per-part deformer stacks and canonical expression vocabulary;
- a versioned Motion Clip Contract for reusable motion assets;
- renderer/encoder environment fingerprints for accepted image/video evidence;
- structured asset-load fallback policies with fail-closed behavior for identity-critical assets;
- stable topology/vertex identity plus a topology migration/invalidation proof for geometry-dependent bindings;
- a persistent artifact registry demonstrating GOLDEN/SOURCE_TRUTH binaries are not dependent on expiring CI artifact retention;
- a versioned package conformance validator with fail-closed integrity/topology/dependency checks;
- a pinned toolchain/build-provenance record and cache-key contract;
- one validated LOD/atlas derivative with transfer mappings and fidelity evidence while Authoring Master remains unchanged;
- release-channel metadata plus a successful package-level rollback/conformance-matrix test;
- a FULL_FRONT_SOURCE_PARITY gate tracked separately from the ear-only CORE-021 evidence;
- a second-character Generalization Gate before claiming the Reference Factory broadly reusable;
- evidence that Golden assets and Reference Atlas versions are immutable/versioned.

Production promotion remains a separate gate in `tims-SP/koma-motion`.
