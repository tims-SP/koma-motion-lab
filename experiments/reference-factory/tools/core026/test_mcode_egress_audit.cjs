'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const https = require('node:https');
const tls = require('node:tls');
const { classify, logfile } = require('./mcode_egress_audit.cjs');

(async () => {
  let requests = 0, connections = 0;
  const server = http.createServer((req, res) => { requests++; res.end('unexpected'); });
  server.on('connection', () => { connections++; });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const local = `http://127.0.0.1:${server.address().port}/not-authorized`;
  await assert.rejects(fetch(local, { method: 'POST', body: 'PUBLIC_DUMMY' }), /KOMA_MCODE_EGRESS_BLOCKED/);
  assert.throws(() => http.request(local), /KOMA_MCODE_EGRESS_BLOCKED/);
  const storage = 'matrix-internal-cn.oss-cn-shanghai.aliyuncs.com';
  const form = new FormData(); form.append('file', new Blob(['PUBLIC_DUMMY'], { type: 'image/png' }), 'agent-avatar');
  await assert.rejects(fetch(`https://${storage}/`, { method: 'POST', body: form }), /KOMA_MCODE_EGRESS_BLOCKED/);
  assert.throws(() => https.request(`https://${storage}/`, { method: 'POST' }), /KOMA_MCODE_EGRESS_BLOCKED/);
  assert.throws(() => tls.connect({ host: storage, port: 443, servername: storage }), /KOMA_MCODE_EGRESS_BLOCKED/);
  assert.equal(classify(new URL('https://agent.minimax.cn/test'), 'POST', {}, true), true);
  assert.equal(classify(new URL('https://agent.minimaxi.com/test'), 'POST', {}, true), true);
  const cdn = new URL(`https://filecdn.minimax.chat/public/models-dev/catalog/${'a'.repeat(64)}/api.json`);
  assert.equal(classify(cdn, 'GET', {}, false), true);
  assert.equal(classify(cdn, 'POST', {}, true), false);
  assert.equal(classify(cdn, 'GET', { Authorization: 'DUMMY_NEVER_LOG' }, false), false);
  await new Promise(resolve => setTimeout(resolve, 30));
  assert.equal(requests, 0); assert.equal(connections, 0);
  await new Promise(resolve => server.close(resolve));
  const text = fs.readFileSync(logfile, 'utf8');
  for (const forbidden of ['PUBLIC_DUMMY', 'DUMMY_NEVER_LOG', 'Authorization', 'query=']) assert.equal(text.includes(forbidden), false);
  console.log(JSON.stringify({ status: 'PASS', denied_live_requests: 5,
    local_requests_received: requests, local_connections_received: connections,
    sensitive_values_recorded: false, scope: 'Covered Node request paths only; no external endpoint contacted by test' }));
})().catch(error => { console.error(error.message); process.exitCode = 1; });
