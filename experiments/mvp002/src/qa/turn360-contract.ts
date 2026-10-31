/**
 * MVP-006: QA data contract for REAL 360° cartoon-model acceptance.
 *
 * This file is types + policy only. It does NOT assert that current
 * MVP-005 integrated.ts already emits it or has passed any new gate.
 * Future implementation must instrument the SAME evaluated character,
 * never fabricate an independent shadow state for validation.
 */
export type XYZ = readonly [number,number,number];
export type XY = readonly [number,number];
export type YawDeg = number;
export type QASeverity = 'P0'|'P1'|'P2';
export type AcceptanceStatus =
  | 'NOT_RUN'
  | 'FAIL_STRUCTURE'
  | 'PASS_STRUCTURE_PENDING_VISUAL'
  | 'FAIL_VISUAL'
  | 'NEEDS_HUMAN_REVIEW'
  | 'PASS_360_CORE';

export const TURN360_PROFILE = {
  fps:24,
  durationSeconds:8,
  videoFrames:192,
  width:960,
  height:540,
  sampleDegrees:Array.from({length:25},(_,i)=>i*15),
  criticalDegrees:[0,45,90,135,180,225,270,315,360],
  transitionBoundaries:[0,90,180,270],
  boundaryOffsetDegrees:1,
  // First render is a static pose; light and camera must not vary.
  fixedPose:true,
  fixedCamera:true,
  fixedLight:true,
  requiredIndependentKeyviews:[0,90,180,270],
  maxDefaultVisionBoards:2,
  maxSupplementalVisionCrops:4,
  maxTemporalReviewWindows:5
} as const;

export type ViewKey = {
  yawDegrees:number;
  sourceHash:string;
  independentlyAuthored:boolean;
  topologyId:string;
};

export type Visibility = 'visible'|'occluded'|'absent'|'crossfade';
export type TopologyTransition = 'none'|'split'|'merge'|'maskSwitch';

export interface PartTrace {
  id:string;
  anatomicalSide?:'left'|'right'|'center';
  parentBoneId:string|null;
  worldAnchorXYZ:XYZ;
  projectedAnchorXY:XY;
  vddOffsetXY:XY;
  keyA:ViewKey;
  keyB:ViewKey;
  keyWeight:number;
  geometryVerticesXY:readonly XY[];
  textureUV:readonly XY[];
  triangleIndices:readonly number[];
  visibility:Visibility;
  topologyTransition:TopologyTransition;
  depthMin:number;
  depthMax:number;
  expectedOccluders:readonly string[];
  actualVisibleAreaPixels:number;
  visiblePixelCountFromIdPass:number;
  sourceTextureHash:string;
  warningCodes:readonly string[];
}

export interface FrameTrace {
  frameIndex:number;
  timeSeconds:number;
  yawDegrees:number;
  poseHash:string;
  cameraHash:string;
  lightHash:string;
  characterAssetHash:string;
  rendererCommit:string;
  parts:readonly PartTrace[];
  actualVisiblePartIds:readonly string[];
  characterBoundingBoxPixels:readonly [number,number,number,number];
  geometryWarnings:readonly string[];
  imageDiagnostics:readonly {
    code:string;
    normalizedMagnitude?:number;
    affectedPartIds?:readonly string[];
  }[];
}

export interface RenderPassEvidence {
  yawDegrees:number;
  frameIndex:number|null;
  characterAssetHash:string;
  cameraHash:string;
  poseHash:string;
  rendererCommit:string;
  beautyImage:string;
  partIdImage:string;
  depthImage:string;
  alphaMaskImage:string;
  meshOverlayImage:string;
}

export type GateId =
  | 'S01_ANGLE_COVERAGE'
  | 'S02_CYCLIC_SEAM'
  | 'S03_ANCHOR_VDD_DECOMPOSITION'
  | 'S04_ARTMESH_UV_TOPOLOGY'
  | 'S05_PART_TRAJECTORY_CONTINUITY'
  | 'S06_OCCLUSION_ACTUAL_RENDER'
  | 'S07_ANATOMICAL_ASYMMETRY'
  | 'S08_RENDER_FRAME_INTEGRITY';

export interface AcceptanceIssue {
  id:string;
  gateId:GateId|'VISUAL'|'TEMPORAL';
  severity:QASeverity;
  yawDegrees?:number;
  frameIndex?:number;
  partIds:readonly string[];
  observation:string;
  evidenceFile:string;
  suggestedFix:string;
  reviewer:'ts-structural'|'vision-model'|'human';
  confidence?:number;
  status:'open'|'fixed'|'needs_review';
}

export interface GateResult {
  id:GateId;
  status:'PASS'|'FAIL'|'BLOCKED';
  evidenceFiles:readonly string[];
  issueIds:readonly string[];
}

export interface Turn360AcceptanceReport {
  schemaVersion:'MVP-006-360-V1';
  characterAssetHash:string;
  rendererCommit:string;
  runUrl:string;
  videoFile:string;
  videoFrameCount:number;
  sampledAngleImages:readonly string[];
  frameTraceFile:string;
  renderPassEvidenceFiles:readonly string[];
  gateResults:readonly GateResult[];
  issues:readonly AcceptanceIssue[];
  visualReviewedBy?:string;
  fullVideoReviewedBy?:string;
  coreStatus:AcceptanceStatus;
  highFidelityAnimeArtAccepted:false; // separate phase; never inferred from 360 PASS.
}
