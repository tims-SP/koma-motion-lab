// CORE-025 M3: turntable video capture (97 real frames) via the fixed core025 API.
// Usage: node capture_core025_video.mjs        (no extra arguments accepted)
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {mkdir, writeFile, readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const args = process.argv.slice(2);
if (args.length !== 0) {
  console.error('usage: node capture_core025_video.mjs');
  process.exit(2);
}

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.join(ROOT, 'out/core025/turntable');
const FRAMES_DIR = path.join(OUT_DIR, 'frames');
const sha = b => createHash('sha256').update(b).digest('hex');
const fileSha = async p => sha(await readFile(p));

const SIZE = 640;
const FRAME_COUNT = 97;
const FPS = 24;

const yawAt = i => {
  const y = 15 * Math.sin((2 * Math.PI * i) / (FRAME_COUNT - 1));
  return Math.abs(y) < 1e-10 ? 0 : y;
};

const paramsFor = (yaw_deg, background) => ({
  version: 'clean', yaw_deg, depth: 'curved', background, pass: 'beauty', size: SIZE,
});

await mkdir(FRAMES_DIR, {recursive: true});

const server = await createServer({root: ROOT, server: {host: '127.0.0.1', port: 4175, strictPort: true}});
await server.listen();
let browser;
let failed = false;
try {
  browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  const page = await browser.newPage({viewport: {width: SIZE, height: SIZE}, deviceScaleFactor: 1});

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

  const canvas = page.locator('canvas#stage');
  const frames = [];
  for (let i = 0; i < FRAME_COUNT; i++) {
    const yaw_deg = yawAt(i);
    const params = paramsFor(yaw_deg, 'white');
    const pose = await page.evaluate(p => window.core025.render(p), params);
    if (!pose) throw new Error(`render returned nothing at frame ${i}`);
    const png = await canvas.screenshot();
    const file = `frames/${String(i).padStart(4, '0')}.png`;
    await writeFile(path.join(OUT_DIR, file), png);
    frames.push({index: i, file, yaw_deg, params, pose, sha256: sha(png)});
    if (errors.length) throw new Error(`page errors during capture:\n${errors.join('\n')}`);
  }

  const black_specs = [
    {file: 'black-minus15.png', yaw_deg: -15},
    {file: 'black-plus15.png', yaw_deg: 15},
  ];
  const black_checks = [];
  for (const spec of black_specs) {
    const params = paramsFor(spec.yaw_deg, 'black');
    const pose = await page.evaluate(p => window.core025.render(p), params);
    if (!pose) throw new Error(`render returned nothing for ${spec.file}`);
    const png = await canvas.screenshot();
    await writeFile(path.join(OUT_DIR, spec.file), png);
    black_checks.push({file: spec.file, params, pose, sha256: sha(png)});
  }
  if (errors.length) throw new Error(`page errors during capture:\n${errors.join('\n')}`);

  const manifest = {
    schema: 'koma-core025-video-capture/1',
    fps: FPS,
    width: SIZE,
    height: SIZE,
    frame_count: FRAME_COUNT,
    inputs: {
      assembly_sha256: await fileSha(path.join(ROOT, 'out/core025/assembly/assembly.json')),
      config_sha256: await fileSha(path.join(ROOT, 'config/core025-render.json')),
      scene_sha256: await fileSha(path.join(ROOT, 'core025.js')),
      anchor_manifest_sha256: await fileSha(path.join(ROOT, 'out/core025/render/manifest.json')),
      video_capture_sha256: await fileSha(path.join(ROOT, 'capture_core025_video.mjs')),
    },
    environment: {
      three_revision: metadata?.three_revision ?? null,
      renderer: metadata?.renderer ?? null,
      node: process.version,
      chromium: browser.version(),
      platform: process.platform,
    },
    frames,
    black_checks,
  };
  await writeFile(path.join(OUT_DIR, 'video-manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  console.log(JSON.stringify({status: 'PASS', frames: frames.length, black_checks: black_checks.length}));
} catch (err) {
  failed = true;
  console.error(String(err?.stack ?? err));
} finally {
  await browser?.close();
  await server.close();
}
process.exit(failed ? 1 : 0);
