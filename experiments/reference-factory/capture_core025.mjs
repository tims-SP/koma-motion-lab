// CORE-025 M2-B capture: fixed API from docs/plans/CORE-025-M2-split-orders.md
// Usage: node capture_core025.mjs --anchors
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {mkdir, writeFile, readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const args = process.argv.slice(2);
if (args.length !== 1 || args[0] !== '--anchors') {
  console.error('usage: node capture_core025.mjs --anchors');
  process.exit(2);
}

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const RENDER_DIR = path.join(ROOT, 'out/core025/render');
const sha = b => createHash('sha256').update(b).digest('hex');
const fileSha = async p => sha(await readFile(p));

const CANVAS = 1630;
const PASSES = ['beauty', 'silhouette', 'part_id', 'wireframe'];

// --- capture plan: 17 entries (4 zero-degree anchors + 12 diagnostics + 1 flat ablation)
const PLAN = [];
for (const version of ['source', 'clean']) {
  for (const background of ['white', 'black']) {
    PLAN.push({version, yaw_deg: 0, depth: 'curved', background, pass: 'beauty', repeat: true});
  }
}
for (const yaw_deg of [-15, 0, 15]) {
  for (const pass of PASSES) {
    PLAN.push({
      version: 'clean', yaw_deg, depth: 'curved',
      background: pass === 'silhouette' ? 'black' : 'white',
      pass, repeat: false,
    });
  }
}
PLAN.push({version: 'clean', yaw_deg: 15, depth: 'flat', background: 'white', pass: 'beauty', repeat: false});
if (PLAN.length !== 17) throw new Error(`capture plan must hold 17 entries, got ${PLAN.length}`);

await mkdir(RENDER_DIR, {recursive: true});

const server = await createServer({root: ROOT, server: {host: '127.0.0.1', port: 4175, strictPort: true}});
await server.listen();
let browser;
let failed = false;
try {
  browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  const page = await browser.newPage({viewport: {width: CANVAS, height: CANVAS}, deviceScaleFactor: 1});

  const errors = [];
  page.on('pageerror', e => errors.push(`pageerror: ${e.message}`));
  page.on('console', m => { if (m.type() === 'error') errors.push(`console.error: ${m.text()}`); });
  page.on('requestfailed', r => {
    const u = r.url();
    if (u.includes('favicon')) return;
    errors.push(`requestfailed: ${u} ${r.failure()?.errorText ?? ''}`);
  });
  page.on('response', r => {
    const u = r.url();
    if (u.includes('favicon')) return;
    if (r.status() >= 400) errors.push(`http ${r.status()}: ${u}`);
  });

  await page.goto('http://127.0.0.1:4175/core025.html', {waitUntil: 'load'});
  await page.waitForFunction(() => window.core025Ready === true, {}, {timeout: 60000});
  if (errors.length) throw new Error(`page errors during load:\n${errors.join('\n')}`);

  const metadata = await page.evaluate(() => window.core025.metadata);
  if (!metadata) throw new Error('window.core025.metadata missing');
  const geometry = await page.evaluate(() => window.core025.exportGeometry());
  const geometryFile = 'geometry.json';
  await writeFile(path.join(RENDER_DIR, geometryFile), JSON.stringify(geometry, null, 2) + '\n');

  const captures = [];
  const mismatches = [];
  for (const [i, spec] of PLAN.entries()) {
    const params = {
      version: spec.version, yaw_deg: spec.yaw_deg, depth: spec.depth,
      background: spec.background, pass: spec.pass, size: CANVAS,
    };
    const id = `c${String(i).padStart(2, '0')}_${spec.version}_${spec.depth}_y${spec.yaw_deg}_${spec.background}_${spec.pass}`;
    const file = `${id}.png`;
    const pose = await page.evaluate(p => window.core025.render(p), params);
    if (!pose) throw new Error(`render returned nothing for ${id}`);
    const png = await page.locator('canvas#stage').screenshot();
    await writeFile(path.join(RENDER_DIR, file), png);
    const digest = sha(png);
    let repeat_sha256 = null;
    if (spec.repeat) {
      await page.evaluate(p => window.core025.render(p), params);
      const repeatPng = await page.locator('canvas#stage').screenshot();
      repeat_sha256 = sha(repeatPng);
      if (repeat_sha256 !== digest) mismatches.push(`${id}: ${digest} != ${repeat_sha256}`);
    }
    captures.push({id, file, params, sha256: digest, repeat_sha256, pose});
    if (errors.length) throw new Error(`page errors during capture:\n${errors.join('\n')}`);
  }

  const manifest = {
    schema: 'koma-core025-capture/1',
    inputs: {
      assembly_sha256: await fileSha(path.join(ROOT, 'out/core025/assembly/assembly.json')),
      config_sha256: await fileSha(path.join(ROOT, 'config/core025-render.json')),
      scene_sha256: await fileSha(path.join(ROOT, 'core025.js')),
      capture_sha256: await fileSha(path.join(ROOT, 'capture_core025.mjs')),
    },
    environment: {
      ...metadata,
      node: process.version,
      chromium: browser.version(),
      platform: process.platform,
      renderer: metadata?.renderer ?? null,
    },
    geometry: {file: geometryFile, sha256: await fileSha(path.join(RENDER_DIR, geometryFile))},
    captures,
  };
  await writeFile(path.join(RENDER_DIR, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  if (mismatches.length) throw new Error(`non-deterministic repeat renders:\n${mismatches.join('\n')}`);
  console.log(JSON.stringify({status: 'PASS', captures: captures.length, geometry: geometryFile}));
} catch (err) {
  failed = true;
  console.error(String(err?.stack ?? err));
} finally {
  await browser?.close();
  await server.close();
}
process.exit(failed ? 1 : 0);
