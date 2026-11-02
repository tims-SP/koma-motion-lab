import test from 'node:test';
import assert from 'node:assert/strict';
import {interpolateViews,authoredCoverage,projectHeadProxy,smoothstep} from '../src/vdd-keyframes.ts';

const makeKey=(yaw,shape,role='synthetic_fixture',topologyId='head-A')=>({
 yawDeg:yaw,semanticId:'head.silhouette',vertexIds:['chin','brow','forehead'],
 xy:[[0+shape,0],[1+shape,2],[0+shape,4]],anchorXYZ:[shape,2,0.1],
 opacity:1,role,topologyId
});
test('keyframe endpoints and 45-degree key exactly reproduce authored landmarks',()=>{
 const keys=[makeKey(0,0),makeKey(45,2),makeKey(90,4)];
 for(const [a,x] of [[0,0],[45,2],[90,4]]){
  const r=interpolateViews(keys,a);
  assert.equal(r.xy[0][0],x);
 }
});
test('continuous interpolation and monotonic landmark motion',()=>{
 const keys=[makeKey(0,0),makeKey(45,2),makeKey(90,4)];
 let prev=-Infinity;
 for(let yaw=0;yaw<=90;yaw++){
  const r=interpolateViews(keys,yaw);
  assert.ok(r.xy[0][0]>=prev-1e-12);
  assert.ok(r.xy.every(pt=>pt.every(Number.isFinite)));
  prev=r.xy[0][0];
 }
 assert.equal(interpolateViews(keys,22.5).xy[0][0],1);
 assert.equal(interpolateViews(keys,67.5).xy[0][0],3);
 assert.equal(smoothstep(-2),0);assert.equal(smoothstep(2),1);
});
test('reject absent views, invalid topology, missing geometry, and extrapolation',()=>{
 const keys=[makeKey(0,0),makeKey(90,4)];
 assert.throws(()=>interpolateViews(keys,-1),/outside/);
 assert.throws(()=>interpolateViews(keys,91),/outside/);
 assert.throws(()=>interpolateViews([keys[0]],45),/Two views/);
 assert.throws(()=>interpolateViews([keys[0],{...keys[1],topologyId:'other'}],45),/Topology mismatch/);
 assert.throws(()=>interpolateViews([keys[0],{...keys[1],vertexIds:['chin','wrong','forehead']}],45),/Topology mismatch/);
 assert.throws(()=>interpolateViews([keys[0],{...keys[1],xy:[[NaN,0],[0,0],[0,0]]}],45),/Nonfinite/);
});
test('independent visual keys are distinctly labeled from diagnostic samples',()=>{
 const inputs=[makeKey(0,0,'runtime_sample'),makeKey(90,4,'synthetic_fixture')];
 const coverage=authoredCoverage(inputs,[0,45,90]);
 assert.deepEqual(coverage.missing,[0,45,90]);assert.equal(coverage.complete,false);
 assert.equal(interpolateViews(inputs,45).trueViewSupport,false);
 const truth=[makeKey(0,0,'independent_art'),makeKey(90,4,'independent_art')];
 assert.equal(interpolateViews(truth,45).trueViewSupport,true);
 assert.deepEqual(authoredCoverage(truth,[0,45,90]).missing,[45]);
});
test('native front view is an exact identity projection at yaw 0',()=>{
 assert.deepEqual(projectHeadProxy(1,4,[2,2,0.25],[0,3],0),[1,4]);
 assert.deepEqual(projectHeadProxy(1,4,[2,2,0.25],[0,3],90,0),[1,4]);
 const a=projectHeadProxy(1,4,[2,2,0.25],[0,3],30);
 const b=projectHeadProxy(1,4,[2,2,0.25],[0,3],90);
 assert.ok(a[0]!==1 && b[0]!==1);assert.equal(a[1],4);
 assert.throws(()=>projectHeadProxy(NaN,4,[2,2,0.25],[0,3],45),/Nonfinite/);
});
