import * as THREE from 'three';

// MVP-001 M0 infrastructure fixture: original procedural geometry only.
// This is deliberately not claimed to be an anime character or a 360° model.
const canvas = document.querySelector('#viewport');
const renderer = new THREE.WebGLRenderer({
  canvas, antialias: true, alpha: false, preserveDrawingBuffer: true
});
renderer.setPixelRatio(1);
renderer.setSize(640, 360, false);
renderer.setClearColor(0x151922, 1);

const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(-3.36, 3.36, 1.89, -1.89, 0.1, 20);
camera.position.set(0, 1.65, 7.0);
camera.lookAt(0, 1.65, 0);
const actor = new THREE.Group();
scene.add(actor);
const names = [];

function flat(name, parent, x, y, z, w, h, color) {
  const geometry = new THREE.PlaneGeometry(w, h, 2, 2);
  const material = new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(x, y, z);
  mesh.name = name;
  parent.add(mesh);
  names.push(name);
  return mesh;
}

const navy = 0x556b92, blue = 0x6d8dc0, skin = 0xe8bba0, hair = 0x42354b;
flat('hair.back', actor, 0, 2.64, -0.12, 0.81, 1.04, hair);
flat('body.torso', actor, 0, 1.60, 0.0, 0.78, 1.07, navy);
flat('body.pelvis', actor, 0, 0.92, 0.02, 0.71, 0.34, blue);
flat('neck', actor, 0, 2.21, 0.05, 0.20, 0.27, skin);

const legL = new THREE.Group(), legR = new THREE.Group();
legL.position.set(-0.19, 0.85, 0); legR.position.set(0.19, 0.85, 0);
actor.add(legL, legR);
for (const [side, group] of [['l',legL],['r',legR]]) {
  flat('thigh.'+side, group, 0, -0.33, 0, 0.29, 0.66, blue);
  const knee = new THREE.Group(); knee.position.y=-0.67; group.add(knee);
  flat('calf.'+side, knee, 0, -0.27, 0, 0.24, 0.56, navy);
  flat('shoe.'+side, knee, 0, -0.58, 0.04, 0.34, 0.17, hair);
}

const shoulderL = new THREE.Group(), shoulderR = new THREE.Group();
shoulderL.position.set(-0.47, 1.96, 0); shoulderR.position.set(0.47, 1.96, 0);
actor.add(shoulderL, shoulderR);
for (const [side, group] of [['l',shoulderL],['r',shoulderR]]) {
  flat('upperarm.'+side, group, 0, -0.27, 0, 0.23, 0.55, navy);
  const elbow = new THREE.Group(); elbow.position.y = -0.55; group.add(elbow);
  flat('forearm.'+side, elbow, 0, -0.22, 0.01, 0.20, 0.46, skin);
  flat('hand.'+side, elbow, 0, -0.49, 0.02, 0.19, 0.19, skin);
}
const head = new THREE.Group(); head.position.set(0, 2.69, 0.05); actor.add(head);
flat('face', head, 0, 0, 0.08, 0.65, 0.75, skin);
flat('bangs.left', head, -0.19, 0.27, 0.15, 0.28, 0.20, hair);
flat('bangs.right', head, 0.16, 0.27, 0.15, 0.35, 0.17, hair);
flat('eye.left', head, -0.15, 0.01, 0.17, 0.085, 0.11, 0x304264);
flat('eye.right', head, 0.15, 0.01, 0.17, 0.085, 0.11, 0x304264);
flat('mouth', head, 0, -0.23, 0.175, 0.11, 0.025, 0xa06a6c);

// Orthogonal component views prove WebGL can render parts at side-on angles.
// Still a primitive cross-view fixture, not interpolated high-fidelity art.
for (const [name,y,w,h,color] of [
  ['body.torso.side',1.60,0.43,1.07,0x556b92],
  ['head.face.side',2.69,0.39,0.75,0xe8bba0],
  ['hair.back.side',2.70,0.49,1.04,0x42354b]
]) {
  const sidePart = flat(name, actor, 0, y, 0, w, h, color);
  sidePart.rotation.y = Math.PI / 2;
}

const gl = renderer.getContext();
const pixels = new Uint8Array(4);
const metadata = {
  testOnly: true, label: 'M0 engineering smoke, not fidelity proof',
  partNames: names,
  glVersion: gl.getParameter(gl.VERSION),
  renderer: gl.getParameter(gl.RENDERER)
};
window.m0Metadata = metadata;

window.renderFrame = function renderFrame(frameIndex) {
  if (!Number.isInteger(frameIndex) || frameIndex < 0 || frameIndex > 24) {
    throw new Error('frameIndex must be an integer in 0..24');
  }
  const t = frameIndex/24;
  actor.rotation.y = t * Math.PI*2;
  shoulderR.rotation.z = -0.12 - 0.28*Math.sin(t*Math.PI*2);
  shoulderL.rotation.z = 0.12 + 0.22*Math.sin(t*Math.PI*2);
  head.rotation.z = 0.035*Math.sin(t*Math.PI*2);
  renderer.render(scene, camera);
  gl.readPixels(320, 180, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
  return {
    frameIndex, yawDeg:360*t, partCount:names.length,
    sampleRGBA:Array.from(pixels),
    viewMatrix:Array.from(actor.matrixWorld.elements),
    glVersion:metadata.glVersion
  };
};

window.renderFrame(0);
