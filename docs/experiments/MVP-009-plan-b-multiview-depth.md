# MVP-009 · 方案 B — 多视角原画 + 3D 锚点 + 深度分层

Status: **DESIGN COMMITTED / NOT IMPLEMENTED / NOT VISUALLY ACCEPTED**  
Date: 2026-11-01  
Parent: [MVP-009 head360 plan](./MVP-009-head360-representation-plan.md)  
Legacy failure: [MVP-008 architecture audit](./MVP-008-P0-root-cause-geometry-audit.md)

## 1. 产品目标、范围、不可混淆之处

- 本方案以 **真实分层多视角原画** 决定侧脸和衣物外观；3D 锚点提供空间关联/视差/深度/骨骼层次，2D 网格在相邻关键角度提供形变；视角相关遮挡图决定出现、消失和前后关系。
- 可验证目标：**水平 yaw 0–360°** 的同一动漫头部/人物，右侧、左侧、背面都有原画支持并能插值出可信中间角度；最终才合并全身动作。俯仰、任意舞台调度、未知方向大动作不是当前 MVP 保证。
- **不要求完整 3D 头部曲面，也不要求单套连续 UV**。相机朝向的分层 billboard 合法，只要每层有真实已注册的 3D anchor / depth、专用侧视造型和正确遮挡。
- **禁止旧实现的假侧脸**：0° 脸压窄、加单眼鼻嘴细线，再用贴图 alpha 裁剪不能当作 90° 侧脸素材。
- **禁止旧实现的假深度**：全部 face/eyes/fringe 强制 `depthTest=false` 加全局 `renderOrder=100/110/120`，不得拿这种 layer 顺序解释头发与脸的三维层次。
- **禁止验收冒充**：192 帧完成、插值数值正常、头部 yaw 动了、11/11 结构门禁不等于侧脸/头发/深度通过。

## 2. 上游实现参考：直接复用思想，不照搬未经校准的代码

1. Rivers / Igarashi / Durand, SIGGRAPH 2010, [2.5D Cartoon Models](https://alecrivers.com/2.5dcartoonmodels/): **2D stroke/sprite + 3D anchor position + orientation-space drawing interpolation + depth order**，不要求全表面多边形 3D。
2. [without-paper/2.5d_cartoon_model](https://github.com/without-paper/2.5d_cartoon_model): 开放的探索型实现包含 Orientation Space、形状插值、Grouping、3D Anchor。其 README 明确仍有结果问题，作为带参考输入 SVG 的数学/结构对照，**不是经过验收的引擎**。保留其许可证检查与 commit pin。
3. Kitamura / Kanamori / Tsuruno, [2.5D Modeling from Illustrations of Different Views](https://www.jstage.jst.go.jp/article/adada/18/4/18_74/_article/-char/en): *沿深度排列的可形变 billboards*、不同原画 region correspondence、手工关键特征点及被遮挡/新出现区域补画，是 B 的最贴切实现参照。
4. Fukusato / Maejima, [View-Dependent Deformation](https://doi.org/10.1109/MCG.2022.3174202): 允许艺术夸张偏离真实投影，但需要由绘画关键视角给出形状，不能凭空得到缺失的眼/鼻/耳。
5. [Live2D Cubism Drawing Order](https://docs.live2d.com/en/cubism-editor-manual/draworder/) 和 [Clipping](https://docs.live2d.com/en/cubism-editor-manual/clipping-mask/): draw order 可以参数化，多个 ArtMesh 需要清晰 mask ID；但 Cubism 自身的编辑器顺序不是我们的自动 360° 深度解算。

## 3. 最小资产，不先扩成完整角色

### B0: 头部 0 → 90° 可行性

- **三个绘制关键方向**：front 0°、3/4 45°、true right profile 90°；0/45/90 每个独立绘制，不能由 renderer 按宽度生成。
- **三个独立留出参考方向**：30/60/75°（检查而不参与运行时插值），避免只在训练关键帧“完美”。
- 最小分层（数量按真实遮挡决定而非生硬限定）：rearHair, sideHair.L/R, ear.L/R, faceBase, noseProfile, mouth/chin, eye.L/R, brows, fringe/frontHair, neck。一个层若从前穿到后造成深度循环，必须拆成互相遮挡的多个子层。
- 侧脸必须真实具有鼻梁/鼻尖、嘴唇/下巴、耳根/耳廓、眼眶与发际线的正确轮廓；同角色发型、肤色和左右耳不对称特征要一致。
- 每个 key 的 **alpha RGBA、轮廓/mesh、2D 语义点、显示/隐藏、独立内侧发际线、前后层约束** 必须可验证。颜色风格可以很简单，但结构不可省略。
- 资源输入可由自制矢量参考或同角色的真实分层合法资产提供。真实动漫风格素材升级在 B0 验收之后；不把第三方游戏原画提交公开仓库。AI 生图时先锁正面角色，按侧面/3/4 多视角参考做图并独立审查，而非无约束地生四张不同人物。

### B1: 扩到水平 360°

- 先有 180° 独立后脑/头发和 270° 独立左侧 profile，再补 135/225/315° 关键姿态。
- **头部八个推荐关键角度** 0,45,90,135,180,225,270,315，按角度和部件设置可变 key count；身体可以 4~8 个，不强迫每个隐形部件全方向存在。
- 通过 B0 的插值质量和补图成本决定是否必须八关键视角；否则每 15° 重画角色并非有效技术路线。

## 4. 标准资产结构（TypeScript Schema / JSON）

```ts
type YawKey = 0|45|90|135|180|225|270|315;
type ViewState = 'visible'|'hidden'|'enter'|'exit'|'split'|'merge';
interface PartKey {
  yaw:YawKey;
  rgbaAsset:{path:string;sha256:string;license:string};
  // Relative to the unique part anchor, not arbitrary canvas pixel position.
  drawingPivotXY:[number,number];
  mesh:{uv:[number,number][];positions2D:[number,number][];triangles:number[]};
  landmarks:Record<string,[number,number]>;
  occlusionMaskAsset?:string;
  viewState:ViewState;
  depthBias:number;
  coveragePriority?:number;
}
interface Part2p5D {
  id:string;parentBoneId:string;localAnchorXYZ:[number,number,number];
  handedness?:'left'|'right'|'center';
  keys:Partial<Record<YawKey,PartKey>>;
}
interface HeadAsset {
  cameraCalibration:{projection:'orthographic';orthoScale:number;headOriginXY:[number,number]};
  bones:{id:string;parentId:string|null;restXYZ:[number,number,number]}[];
  parts:Part2p5D[];
  perViewOcclusion:{yaw:YawKey;frontId:string;behindId:string;region?:string}[];
}
```

Semantic IDs are stable *within one anatomical part*, but topology may differ across views; stable IDs are not license to morph one eye into a different ear. Explicit split/merge, start/end-of-visibility, and occlusion masks needed for key changes.

## 5. Rendering algorithm — B differs from the old MVP

```text
camera + rootBone + headBone
       ↓  local view direction per animated part, angle wrap
choose genuine neighbor keyviews for each part (not one body-wide yaw)
       ↓
project calibrated 3D anchor and parent bone into camera
       ↓
fit/interpolate semantic 2D landmarks relative to projected anchor
       ↓
construct registered 2D ArtMesh / local warp; choose view-specific texture
       ↓
apply visibility/topology-specific correction and a view-dependent depth graph
       ↓
shared coverage/discard+clip for Beauty / Part-ID / Depth / Alpha
       ↓
screen render → independent screenshots and QA
```

### 3D anchor projection

For character-local anchor `A_i=(x_i,y_i,z_i)`, head/bone transform `M_b(t)` and camera view-projection `P V`:

`screenAnchor_i(t,θ)=project(P V M_b(t) A_i)`.

In orthographic horizontal rotation, local X/Z affect screen X and camera depth differently. For typical 0/90° calibration, front-view X and right-view X provide independent evidence for underlying local X/Z. Fit these from authored landmark correspondences; report reprojection error; DO NOT just store an arbitrary 3D location that never influences rendered pixels.

View-specific residual `Δ_{i,k}` accounts for intentional stylization in the keyed drawing, and can interpolate between valid keyviews. `worldDepth_i = cameraDepth(M_b A_i)+interpolatedDepthBias_i(θ)` controls z testing/sorting.

### Spatial layer order and masking

- Use both **numeric camera-relative depth** and explicit per-key *front/behind* constraints, e.g. 90° `frontHair > face > rearHair`, ear visible between side strands if reference shows it. These constraints are **region-specific**, NOT one fixed global total order.
- If constraints form a cycle within a part, **split the part** into visible semantic sublayers; no algorithmic tie-break forced by arbitrary renderOrder.
- Opaque/alpha-tested cutout meshes with depthTest=true, correct depth prepass where needed. Semi-transparent painting blends separately; alpha coverage still shares the same clip rule. No blanket disabled face depth testing.
- Beauty/ID/depth/alpha use the SAME geometry, alpha cutoff, masks and semantics. A single shared fragment coverage function or literal shared shader source must be validated for parity. In the old MVP, `turn360-runtime.ts idShader` used obsolete straight `wipeBounds` after beauty switched to a curved profile; MUST NOT inherit that test bug.

### View morphing

- Only interpolate corresponding same-anatomy vertices and contours; warp both registered source images to one agreed geometry when valid.
- Do not use naive full-image `mix(texA,texB,t)` when eyes/nose/lines move relative to the contour: ghost lines invalidate quality. On topology transition, redraw/reveal sublayers, use masked switch, or add another keyview.
- If an intermediate view diverges from independent reference, add that angle as a real authored key only for the affected part; record repair cost.
- Shadows/highlights are part of keyed art by default; lighting effects are LAST, not a substitute for correct flat-depth occlusion.

## 6. Sequential tasks with strict gates

| ID | Goal | Hard evidence | Pass to next? |
|---|---|---|---|
| B00 | Freeze MVP-008 failures & separated demo | old SHA / side frame 40/132 / baseline JSON | No inherited visual PASS |
| B01 | New shared coverage QA & fault injection | beauty/ID/depth/alpha parity PNGs; deliberately broken depth and stale mask each FAIL | 100% negative controls detect defect |
| B02 | Three real 0/45/90 layered head keys + held-out 30/60/75 | source hashes, view-wise part sheet, landmark/occlusion graph + independent reference | Real side profile exists and approved in source |
| B03 | 3D anchors from two-view correspondences | 3D anchor overlay, X/Z reprojection traces and error; different depth across view | Anchors influence both pixel position and depth |
| B04 | View-dependent depth + visibility engine | per-angle ID/depth/mask/beauty, wrong-order injections | 0/45/75/90 overlapping face/ear/hair PASS (nonzero overlap) |
| B05 | 0→90° art interpolation | 0,15,30,45,60,75,90 angle board; held-out refs | 90 true profile + intermediate visual pass, no split face/ghost line |
| B06 | Extend LEFT and rear keyviews | 0…360 key art + 13-angle independent probes + 90/270 transition strips | Both side profiles, rear and 0/360 seam pass |
| B07 | Local head yaw / blink / minor movement | one 4–8 s dynamic **head-only** clip + masks | Independently moving head doesn't break layer order |
| B08 | Full-body and pose | after B07: torso/arms/legs + 3D joint IK, pose-aware key art, foot contact | 8 s /192 frames **full-body** visual pass |

B01 → B05 MUST finish with visual approval before B06. If B05 FAILS, do not begin a full 360 movie.

## 7. Machine/vision acceptance matrix

1. **Reference independence**: keys and held-out angle references are art assets with their own SHA; cannot come from the renderer being graded. Layer IDs map correctly to semantic anatomy. Missing asset = BLOCKED.
2. **Side geometry**: 90° and 270° show anatomical profile (nose tip and bridge, lips/chin, ear, one visible eye, hairstyle, mirrored errors absent). Model-eye and human review veto machine PASS.
3. **True depth**: 3D anchor XY reprojection tracks the view; its depth changes as yaw changes. For 90/270, any impossible face-hair-ears ordering or zero-overlap "test" is FAIL/UNTESTED. 2.5D layers may be flat: nonzero per-vertex Z span is **NOT** mandatory in B; correct view-dependent part depth and occlusion IS mandatory.
4. **Pass parity**: actual Beauty/ID/Depth/Alpha coverage agreement; target <=0.5% non-edge opaque region mismatches, 1 px tolerance edges; negative controls must trigger FAIL. These are *provisional measurable budgets* to be calibrated to output resolution.
5. **Key reconstruction**: each authored key compared with its independent source at aligned resolution; initial threshold silhouette IoU >=0.93 and semantic landmark position <=2% of head bounding-box height, plus independent visual approval. Held-out 30/60/75 require reported errors and visual assessment; thresholds aren't a substitute for real profile and hair contact.
6. **Continuity**: 0° and 360° same-pose agree; no disconnected eye/nose/face islands in dense sequences near 90/270; per-frame delta peak can locate a bug but cannot alone pass quality.
7. **Video truth**: full MP4 / every sample / all diagnostic passes bound to exact Git SHA and same renderer function. Do not consume cached old run or claims with mismatched render passes.
8. **Scope**: head pass ≠ full-body pose pass, horizontal 360 ≠ free camera pitch or arbitrary 3D interactions.

## 8. Stop / escalate criteria and production separation

- If B02 cannot provide a true same-character 90° profile, **stop asset research**; do not attempt interpolation.
- If B04 can't represent occlusion with 2D piecewise layers, split that part; if repeated split/merge still fails, compare a **limited local 3D depth patch/hybrid A** rather than the full head model. Do not silently switch project-wide architecture.
- If B05 needs continuous hand-painted in-between images to avoid every ghost/jump, B has failed its efficiency premise; record why and compare A/hybrid. Repeated manual per-shot patches are not a viable generic workflow.
- Stage goal is **visual 0–90°, then 360°, then dynamics**, not "192 encoded frames".
- Stay in `tims-SP/koma-motion-lab` until B06+B07 independently accepted; production `tims-SP/koma-motion` remains untouched.
- Commit code and text-only manifests per stage, keep large originals and MP4/PNG in Actions artifacts or private Draft Releases, status `PASS / FAIL / BLOCKED / NOT_TESTED` as evidence demands.

**Immediate execution target:** B00+B01+B02, then B03–B05. Avoid authoring full-body or high-fidelity hair painting until the 0→90 profile works.
