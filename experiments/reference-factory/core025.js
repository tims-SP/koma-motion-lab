// CORE-025 M2-A2: layered source-surface prototype renderer.
// Fixed API consumed by the capture (B) and QA (C) orders.
// source RGB is used as-is in the source sRGB numeric domain: no lighting,
// no colorspace round trip, no second alpha multiply.
import * as THREE from 'three';

const CANVAS = 1630;
const CENTER = 815;
const GRID_STEP = 12;
const ALPHA_CORE_CUT = 0.9999;
const PASSES = ['beauty', 'silhouette', 'part_id', 'wireframe'];
const MODES = { beauty: 0, silhouette: 1, part_id: 2, wireframe: 3 };

const VERT = `
precision highp float;
uniform mat4 projectionMatrix;
uniform mat4 modelViewMatrix;
attribute vec3 position;
attribute vec2 uv;
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;

const FRAG = `
precision highp float;
uniform sampler2D uMap;
uniform float uAlphaCut;
uniform float uIsCore;
uniform float uMode;
uniform vec3 uColor;
varying vec2 vUv;
void main() {
  vec4 t = texture2D(uMap, vUv);
  float a = t.a;
  if (uIsCore > 0.5) {
    if (a < uAlphaCut) discard;
  } else {
    if (a <= 0.0 || a >= uAlphaCut) discard;
  }
  vec3 rgb;
  float outA;
  if (uMode < 0.5) {
    rgb = t.rgb;
    outA = (uIsCore > 0.5) ? 1.0 : a;
  } else if (uMode < 1.5) {
    rgb = vec3(a);
    outA = a;
  } else if (uMode < 2.5) {
    rgb = uColor * a;
    outA = a;
  } else {
    float k = (uIsCore > 0.5) ? 1.0 : a;
    rgb = uColor * k;
    outA = (uIsCore > 0.5) ? 1.0 : a;
  }
  gl_FragColor = vec4(rgb, outA);
}`;

function hsv2rgb(h, s, v) {
  const ch = (n) => { const k = (n + Math.min(h, 1 - h) * 6) % 6; return v - v * s * Math.max(0, Math.min(k, 4 - k, 1)); };
  return [ch(5), ch(3), ch(1)];
}

function layerColor(order) {
  const h = (order * 0.6180339887498949) % 1.0;
  return hsv2rgb(h, 0.65, 0.95);
}

function gridAxis(from, to) {
  const out = [];
  for (let v = from; v < to; v += GRID_STEP) out.push(v);
  out.push(to);
  return out;
}

function makeGeometry(layer, depthCfg) {
  const [left, top, right, bottom] = layer.bounds;
  const width = right - left;
  const height = bottom - top;
  const xs = gridAxis(left, right);
  const ys = gridAxis(top, bottom);
  const cols = xs.length;
  const rows = ys.length;
  const n = cols * rows;
  const curved = new Float32Array(n * 3);
  const flat = new Float32Array(n * 3);
  const uv = new Float32Array(n * 2);
  const d = depthCfg;
  let p = 0;
  let q = 0;
  for (let r = 0; r < rows; r++) {
    const sy = ys[r];
    for (let c = 0; c < cols; c++) {
      const sx = xs[c];
      const X = (sx - CENTER) / CENTER;
      const Y = (CENTER - sy) / CENTER;
      const h = d.a1 * Math.exp(-Math.pow(X / d.sx1, 2) - Math.pow((Y + d.yoffset1) / d.sy1, 2))
        + d.a2 * Math.exp(-Math.pow(X / d.sx2, 2) - Math.pow((Y + d.yoffset2) / d.sy2, 2));
      const zc = h + layer.order * d.layer_offset;
      const zf = layer.order * d.layer_offset;
      curved[p] = X; curved[p + 1] = Y; curved[p + 2] = zc;
      flat[p] = X; flat[p + 1] = Y; flat[p + 2] = zf;
      p += 3;
      uv[q] = (sx - left) / width;
      uv[q + 1] = 1.0 - (sy - top) / height;
      q += 2;
    }
  }
  const idx = new Uint32Array((cols - 1) * (rows - 1) * 6);
  let t = 0;
  for (let r = 0; r < rows - 1; r++) {
    for (let c = 0; c < cols - 1; c++) {
      const a = r * cols + c;
      const b = r * cols + c + 1;
      const e = (r + 1) * cols + c;
      const f = (r + 1) * cols + c + 1;
      idx[t++] = a; idx[t++] = e; idx[t++] = b;
      idx[t++] = b; idx[t++] = e; idx[t++] = f;
    }
  }
  const geo = new THREE.BufferGeometry();
  const curvedAttr = new THREE.BufferAttribute(curved, 3);
  const flatAttr = new THREE.BufferAttribute(flat, 3);
  geo.setAttribute('position', curvedAttr);
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geo.setIndex(new THREE.BufferAttribute(idx, 1));
  geo.userData.curvedAttr = curvedAttr;
  geo.userData.flatAttr = flatAttr;
  geo.userData.uvArray = Array.from(uv);
  geo.userData.indexArray = Array.from(idx);
  geo.userData.curvedArray = Array.from(curved);
  geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 0, 0.2), 2.0);
  return geo;
}

function makeMaterial(map, isCore, color) {
  const mat = new THREE.RawShaderMaterial({
    vertexShader: VERT,
    fragmentShader: FRAG,
    uniforms: {
      uMap: { value: map },
      uAlphaCut: { value: ALPHA_CORE_CUT },
      uIsCore: { value: isCore ? 1 : 0 },
      uMode: { value: 0 },
      uColor: { value: new THREE.Vector3(color[0], color[1], color[2]) }
    },
    transparent: !isCore,
    depthTest: true,
    depthWrite: isCore,
    blending: THREE.NormalBlending,
    premultipliedAlpha: true,
    side: THREE.DoubleSide,
    forceSinglePass: true
  });
  return mat;
}

async function loadTexture(url) {
  const tex = await new THREE.TextureLoader().loadAsync(url);
  tex.colorSpace = THREE.NoColorSpace;
  tex.premultiplyAlpha = true;
  tex.flipY = true;
  tex.minFilter = THREE.LinearFilter;
  tex.magFilter = THREE.LinearFilter;
  tex.generateMipmaps = false;
  tex.wrapS = THREE.ClampToEdgeWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.needsUpdate = true;
  return tex;
}

async function main() {
  const cfgRes = await fetch('/config/core025-render.json');
  if (!cfgRes.ok) throw new Error(`config fetch failed: ${cfgRes.status}`);
  const cfg = await cfgRes.json();
  const asmRes = await fetch(cfg.source_assembly);
  if (!asmRes.ok) throw new Error(`assembly fetch failed: ${asmRes.status}`);
  const asm = await asmRes.json();
  if (cfg.canvas[0] !== CANVAS || cfg.canvas[1] !== CANVAS) throw new Error('canvas must be 1630x1630');
  if (!Array.isArray(asm.layers) || asm.layers.length !== 62) throw new Error('assembly must contain 62 layers');
  THREE.ColorManagement.enabled = false;
  const canvasEl = document.getElementById('stage') || document.createElement('canvas');
  if (!canvasEl.parentNode) document.body.appendChild(canvasEl);
  const renderer = new THREE.WebGLRenderer({
    canvas: canvasEl,
    antialias: false,
    alpha: false,
    preserveDrawingBuffer: true
  });
  renderer.setPixelRatio(1);
  renderer.setSize(CANVAS, CANVAS, false);
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  renderer.setClearColor(0xffffff, 1);
  renderer.autoClear = true;
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(
    cfg.camera.left, cfg.camera.right, cfg.camera.top, cfg.camera.bottom,
    cfg.camera.near, cfg.camera.far
  );
  camera.position.set(cfg.camera.position[0], cfg.camera.position[1], cfg.camera.position[2]);
  camera.lookAt(cfg.camera.target[0], cfg.camera.target[1], cfg.camera.target[2]);
  camera.updateMatrixWorld(true);
  scene.add(camera);
  const head = new THREE.Group();
  scene.add(head);
  // 62 shared geometries, 248 cached meshes (2 versions x 2 passes x 62).
  const geometries = [];
  const versionMeshes = { source: [], clean: [] };
  const layerRecords = [];
  for (const layer of asm.layers) {
    const geo = makeGeometry(layer, cfg.depth);
    geometries.push(geo);
    const color = layerColor(layer.order);
    const rec = { layer, geo, color };
    layerRecords.push(rec);
    for (const version of ['source', 'clean']) {
      const tex = await loadTexture('/' + layer[`${version}_texture`].file);
      const coreMat = makeMaterial(tex, true, color);
      const fringeMat = makeMaterial(tex, false, color);
      const core = new THREE.Mesh(geo, coreMat);
      const fringe = new THREE.Mesh(geo, fringeMat);
      core.frustumCulled = false;
      fringe.frustumCulled = false;
      core.renderOrder = layer.order;
      fringe.renderOrder = layer.order;
      core.userData = { version, kind: 'core', layer, color };
      fringe.userData = { version, kind: 'fringe', layer, color };
      head.add(core);
      head.add(fringe);
      versionMeshes[version].push(core, fringe);
    }
  }
  const state = { version: 'clean', depth: 'curved', pass: 'beauty', size: CANVAS, yaw: 0 };
  function applyPass(pass) {
    for (const version of ['source', 'clean']) {
      for (const mesh of versionMeshes[version]) {
        const isWire = pass === 'wireframe';
        mesh.material.wireframe = isWire;
        mesh.material.uniforms.uMode.value = MODES[pass];
        mesh.material.uniforms.uIsCore.value = mesh.userData.kind === 'core' ? 1 : 0;
        mesh.material.uniforms.uColor.value.set(
          mesh.userData.color[0], mesh.userData.color[1], mesh.userData.color[2]
        );
        mesh.material.needsUpdate = true;
      }
    }
  }
  function applyDepth(mode) {
    for (const rec of layerRecords) {
      rec.geo.setAttribute('position', mode === 'curved' ? rec.geo.userData.curvedAttr : rec.geo.userData.flatAttr);
    }
  }
  function landmarkLocal(anchor, mode) {
    const [sx, sy] = anchor.source_xy;
    const X = (sx - CENTER) / CENTER;
    const Y = (CENTER - sy) / CENTER;
    const d = cfg.depth;
    const h = d.a1 * Math.exp(-Math.pow(X / d.sx1, 2) - Math.pow((Y + d.yoffset1) / d.sy1, 2))
      + d.a2 * Math.exp(-Math.pow(X / d.sx2, 2) - Math.pow((Y + d.yoffset2) / d.sy2, 2));
    const z = mode === 'curved' ? h + anchor.order * d.layer_offset : anchor.order * d.layer_offset;
    return new THREE.Vector3(X, Y, z);
  }
  function render(opts) {
    if (!opts || typeof opts !== 'object') throw new Error('render(options) required');
    const { version, yaw_deg, depth, background, pass, size } = opts;
    if (version !== 'source' && version !== 'clean') throw new Error('version must be source|clean');
    if (typeof yaw_deg !== 'number' || !Number.isFinite(yaw_deg)
      || yaw_deg < cfg.yaw_range[0] || yaw_deg > cfg.yaw_range[1]) throw new Error('yaw_deg must be finite within [-15,15]');
    if (depth !== 'curved' && depth !== 'flat') throw new Error('depth must be curved|flat');
    if (background !== 'white' && background !== 'black') throw new Error('background must be white|black');
    if (!PASSES.includes(pass)) throw new Error('pass must be beauty|silhouette|part_id|wireframe');
    if (size !== 1630 && size !== 640) throw new Error('size must be 640|1630');
    state.version = version;
    state.depth = depth;
    state.pass = pass;
    state.size = size;
    state.yaw = yaw_deg;
    for (const v of ['source', 'clean']) {
      const active = v === version;
      for (const mesh of versionMeshes[v]) mesh.visible = active;
    }
    applyDepth(depth);
    applyPass(pass);
    head.rotation.y = THREE.MathUtils.degToRad(yaw_deg);
    head.updateMatrixWorld(true);
    renderer.setPixelRatio(1);
    renderer.setSize(size, size, false);
    renderer.setClearColor(background === 'white' ? 0xffffff : 0x000000, 1);
    camera.updateMatrixWorld(true);
    renderer.render(scene, camera);
    const landmarks = {};
    for (const anchor of cfg.anchors) {
      const local = landmarkLocal(anchor, depth);
      const world = local.clone().applyMatrix4(head.matrixWorld);
      const ndc = world.clone().project(camera);
      landmarks[anchor.name] = {
        source_xy: [anchor.source_xy[0], anchor.source_xy[1]],
        world_xyz: [world.x, world.y, world.z],
        pixel_xy: [(ndc.x * 0.5 + 0.5) * size, (-ndc.y * 0.5 + 0.5) * size],
        visibility: 'NOT_VISIBILITY_TESTED'
      };
    }
    return {
      camera_matrix: Array.from(camera.matrixWorld.elements),
      projection_matrix: Array.from(camera.projectionMatrix.elements),
      group_matrix: Array.from(head.matrixWorld.elements),
      landmarks,
      geometry_count: geometries.length,
      active_draw_mesh_count: versionMeshes[version].length,
      version, yaw_deg, depth, background, pass, size
    };
  }
  function exportGeometry() {
    const layers = layerRecords.map((rec) => ({
      order: rec.layer.order,
      name: rec.layer.name,
      bounds: rec.layer.bounds.slice(),
      positions: rec.geo.userData.curvedArray.slice(),
      uv: rec.geo.userData.uvArray.slice(),
      indices: rec.geo.userData.indexArray.slice()
    }));
    return { canvas: [CANVAS, CANVAS], layers };
  }
  const gl = renderer.getContext();
  let rendererName = 'WebGLRenderer';
  try {
    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    if (dbg) rendererName = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
  } catch (err) {
    rendererName = 'WebGLRenderer';
  }
  const metadata = {
    three_revision: THREE.REVISION,
    renderer: rendererName,
    geometry_count: geometries.length,
    active_draw_mesh_count: versionMeshes.source.length,
    transport: 'PNG',
    authority: 'DERIVED_REFERENCE'
  };
  window.core025 = { render, exportGeometry, metadata };
  render({ version: 'clean', yaw_deg: 0, depth: 'curved', background: 'white', pass: 'beauty', size: CANVAS });
  window.core025Ready = true;
}

main().catch((err) => {
  window.core025Error = String((err && err.stack) || err);
  throw err;
});
