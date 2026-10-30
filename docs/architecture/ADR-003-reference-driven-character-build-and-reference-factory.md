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

## Reference Factory instead of one universal reference character

A single Seed-san/VRM character is useful for smoke tests but is too narrow to serve as the universal reference. The preferred long-term design is a small **Reference Factory** built from license-clear source assets that can deterministically produce task-specific reference material.

### Source truth classes

| Class | Initial source | Role |
|---|---|---|
| 2D animation truth | Inochi2D Aka / Midori INX + PSD | Real layered art, ArtMesh, UV, node hierarchy, parameter deformation, source-render comparison |
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
  qa/
    pass/
    fail/
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
          view candidate generation
                   |
                   v
             cross-view QA
            /             \
         PASS             FAIL
          |                 |
          |          region/view repair
          |                 |
          +--------<--------+
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
- a written character-fact checklist for face, hair, ears, accessories, clothing, and asymmetries.

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

### Phase M4 — One-angle A/B/C experiment: Aka 90 degrees

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

Keep the target crop/angle/output contract identical across A/B/C.

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

Use adjacent accepted views as additional references.

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

Then establish the same semantic part IDs across views.

Acceptance:

- one part can be traced across visible views;
- disappearance/reappearance is explicit, not accidental;
- overlap and front/back ordering are recorded.

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
- silhouette discontinuity.

Acceptance requires decoded video and extracted-frame inspection, not merely successful encoding.

### Phase M9 — Rig, weights, IK, then motion

Only after the static/multi-view/turn path is accepted:

1. head/neck;
2. ear and hair controls;
3. facial controls;
4. torso/shoulder/arm/hand/leg;
5. IK;
6. reusable motion references.

Rigging research projects such as UniRig, Make-It-Animatable, and DRiVE may provide reference skeletons/weights, but must be fitted and visually verified against the accepted Koma character asset.

### Phase M10 — Automation last

Only now convert proven manual actions into:

- prompt/reference templates;
- provider adapters;
- retry policies;
- semantic schemas;
- deterministic rendering jobs;
- automated QA;
- `koma character build ...` orchestration.

The Agent may choose a repair strategy, but it must not invent the production process ad hoc.

## QA hierarchy

QA is layered:

1. **Human visual acceptance** — final authority for character identity and artistic correctness.
2. **Reference comparison** — pass/fail examples for each operation.
3. **Structural checks** — yaw, camera, silhouette, depth, landmarks, semantic masks, part ordering.
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
metadata describing the exact task
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
- distinguish code license from checkpoint/data license.

## What is deliberately NOT decided yet

The following remain experimental until the manual path proves them:

- See-through as the final production semantic decomposer;
- MV-Adapter as the final production multi-view generator;
- any specific GPT/image-edit model as a permanent provider;
- exact number of final production views;
- exact semantic part granularity;
- exact scaffold topology;
- exact automatic rigging system;
- whether SeparateGen or later component-aware methods replace any current candidate.

The architecture intentionally makes these replaceable.

## Immediate CORE-021 experiment sequence

The next work should be ordered as follows:

1. inventory and provenance for Aka/Midori + small VRM/VRoid reference bank;
2. render nine-yaw structural references with fixed camera metadata;
3. benchmark Aka flatten -> semantic decomposition -> compare with real PSD/INX;
4. prepare one accepted generic 90-degree task example;
5. run Aka 90-degree A/B/C comparison;
6. inspect actual images and select the strongest path;
7. only then generate 45/135/180 and create a five-view contact sheet;
8. only after five-view acceptance begin semantic correspondence and spatial scaffold work.

**Do not proceed to rig/IK automation before this chain is visually demonstrated.**

## Promotion criterion

This ADR moves from PROPOSED to ACCEPTED FOR CHARACTER-BUILD RESEARCH only after the repository contains reproducible evidence for:

- one deterministic Reference Factory structural render set;
- one Aka semantic-decomposition comparison against real source layers;
- one A/B/C Aka 90-degree comparison;
- an accepted five-view Aka reference set;
- documented failure cases and the chosen repair strategy.

Production promotion remains a separate gate in `tims-SP/koma-motion`.
