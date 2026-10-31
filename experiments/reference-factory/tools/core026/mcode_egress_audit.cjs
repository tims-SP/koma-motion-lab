'use strict';
// Per-process Node request guard, not an OS firewall or a packet capture.
// Never records headers, query strings, body contents, tokens or file bytes.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const https = require('node:https');
const tls = require('node:tls');
const { syncBuiltinESMExports } = require('node:module');

const base = path.resolve(__dirname, '../../out/core026/mcode-egress-audit');
const logfile = path.resolve(process.env.KOMA_MCODE_AUDIT_LOG || path.join(base, 'trace.jsonl'));
if (!logfile.startsWith(base + path.sep)) throw new Error('Audit log must stay in the task output directory');
fs.mkdirSync(base, { recursive: true, mode: 0o700 });
const firstParty = new Set(['agent.minimax.cn', 'agent.minimaxi.com']);
const authHost = 'account.minimax.cn'; // Existing official login/refresh only.
const publicCatalog = /^\/public\/models-dev\/catalog\/[a-f0-9]{64}\/api\.json$/;
const publicAvatar = '/public/d92edcbe-2404-417b-a133-b770b0b9bf61.svg';

function hasPrivateHeader(headers) {
  if (!headers) return false;
  const names = ['authorization', 'cookie', 'proxy-authorization'];
  if (typeof headers.has === 'function') return names.some(name => headers.has(name));
  const keys = Array.isArray(headers) ? headers.map(row => row[0]) : Object.keys(headers);
  return keys.some(key => names.includes(String(key).toLowerCase()));
}
function classify(url, method, headers, bodyPresent) {
  if (url.protocol !== 'https:' || url.username || url.password || (url.port && url.port !== '443')) return false;
  // Command-only work orders never require SDK file/avatar upload preparation.
  // Deny preparation before the SDK can obtain an object-storage instruction.
  if (/\/uploads(?:\/|$)/i.test(url.pathname)) return false;
  if (firstParty.has(url.hostname)) return true;
  if (url.hostname === authHost) return ['GET', 'POST', 'CONNECT'].includes(method);
  return url.hostname === 'filecdn.minimax.chat' && method === 'GET' && !bodyPresent &&
    !url.search && !url.hash && !hasPrivateHeader(headers) &&
    (publicCatalog.test(url.pathname) || url.pathname === publicAvatar);
}

function routeKind(url) {
  if (url.hostname === authHost) return 'official-auth-redacted';
  if (url.hostname === 'filecdn.minimax.chat') return 'public-catalog-or-avatar';
  if (url.pathname.includes('/uploads/prepare')) return 'upload-prepare';
  if (url.pathname.includes('/eval/steps/report')) return 'step-report';
  if (url.pathname.includes('/llm/')) return 'model-api';
  if (url.pathname.includes('/models-dev/')) return 'model-catalog-descriptor';
  return 'other-path-redacted';
}

function bodyMetadata(body, url) {
  const out = { body_kind: 'none' };
  if (url.hostname === authHost) return { body_kind: 'auth-omitted' };
  if (body === undefined || body === null) return out;
  if (typeof body === 'string') {
    out.body_kind = 'string'; out.body_bytes = Buffer.byteLength(body);
    // Only these four non-secret upload-description fields, at this exact route.
    if (url.pathname === '/minimax-cloud/api/v1/uploads/prepare') {
      try {
        const v = JSON.parse(body);
        out.upload_purpose = Number.isInteger(v.purpose) ? v.purpose : 'other';
        out.upload_name_class = v.file_name === 'agent-avatar' ? 'agent-avatar' : 'other';
        out.upload_size = Number.isSafeInteger(v.size_bytes) ? v.size_bytes : null;
        out.upload_mime = /^image\/[a-z0-9.+-]+$/i.test(v.mime_type || '') ? v.mime_type : 'other';
      } catch (_) { out.upload_metadata_parse = 'unavailable'; }
    }
  } else if (typeof FormData !== 'undefined' && body instanceof FormData) {
    out.body_kind = 'form-data';
    const file = body.get('file');
    if (file && typeof file !== 'string') {
      out.file_name_class = file.name === 'agent-avatar' ? 'agent-avatar' : 'other';
      out.file_size = file.size;
      out.file_mime = /^image\/[a-z0-9.+-]+$/i.test(file.type || '') ? file.type : 'other';
    }
  } else if (Buffer.isBuffer(body) || body instanceof Uint8Array) {
    out.body_kind = 'bytes'; out.body_bytes = body.byteLength;
  } else { out.body_kind = 'stream-or-object'; }
  return out;
}

function record(data) {
  fs.appendFileSync(logfile, JSON.stringify({ timestamp: new Date().toISOString(), ...data }) + '\n', { mode: 0o600 });
}

function deny(host) {
  const error = new Error(`KOMA_MCODE_EGRESS_BLOCKED: ${host}`);
  error.code = 'KOMA_MCODE_EGRESS_BLOCKED';
  return error;
}

function enforce(layer, url, method, headers, body) {
  method = String(method || 'GET').toUpperCase();
  const allowed = classify(url, method, headers, body !== undefined && body !== null);
  record({ layer, decision: allowed ? 'allow' : 'block-before-request', hostname: url.hostname,
           method, route_kind: routeKind(url), ...bodyMetadata(body, url) });
  if (!allowed) throw deny(url.hostname);
}

const originalFetch = globalThis.fetch;
globalThis.fetch = function (input, init) {
  try {
    const request = typeof input === 'string' || input instanceof URL ? null : input;
    const url = new URL(request ? request.url : String(input));
    enforce('fetch', url, init?.method || request?.method || 'GET',
            init?.headers || request?.headers, init?.body ?? request?.body);
  } catch (error) { return Promise.reject(error); }
  return originalFetch.call(this, input, init);
};

function protectRequests(module, protocol) {
  const original = module.request;
  module.request = function (...args) {
    const first = args[0];
    let url, options;
    if (typeof first === 'string' || first instanceof URL) {
      url = new URL(first); options = typeof args[1] === 'object' ? args[1] : {};
    } else {
      options = first || {};
      const hostname = options.hostname || options.host || 'localhost';
      url = new URL(`${options.protocol || protocol}//${hostname}`);
      if (options.port) url.port = String(options.port);
      const target = String(options.path || '/');
      if (/^https?:\/\//.test(target)) url = new URL(target);
      else { const u = new URL(target, url); url.pathname = u.pathname; url.search = u.search; }
    }
    // A managed proxy's CONNECT is routing metadata; authorize the tunnel's
    // final TLS endpoint, not arbitrary requests to the proxy itself.
    if (String(options.method).toUpperCase() === 'CONNECT') {
      url = new URL(`https://${options.path || ''}`);
    }
    enforce(protocol === 'https:' ? 'https.request' : 'http.request', url,
            options.method || 'GET', options.headers, undefined);
    return original.apply(this, args);
  };
  module.get = function (...args) { const req = module.request(...args); req.end(); return req; };
}
protectRequests(http, 'http:');
protectRequests(https, 'https:');

const originalTls = tls.connect;
tls.connect = function (...args) {
  const options = args.find(arg => arg && typeof arg === 'object') || {};
  const host = options.servername || options.host || (typeof args[1] === 'string' ? args[1] : 'localhost');
  const hostname = String(host).toLowerCase();
  const port = options.port || (typeof args[0] === 'number' ? args[0] : 443);
  // TLS sees host/port, not HTTP method or contents. SDK direct transports are
  // therefore covered only at hostname level here, not by a full HTTP firewall.
  const allowed = (firstParty.has(hostname) || hostname === authHost || hostname === 'filecdn.minimax.chat') &&
                  String(port) === '443' && options.rejectUnauthorized !== false;
  record({ layer: 'tls.connect', decision: allowed ? 'allow' : 'block-before-tls',
           hostname, method: 'TLS', route_kind: 'transport-no-payload' });
  if (!allowed) throw deny(hostname);
  return originalTls.apply(this, args);
};
syncBuiltinESMExports();
record({ layer: 'guard', decision: 'installed', policy: 'authorized-first-party-and-public-cdn; upload-preparation-and-object-storage-denied',
         scope: 'Node fetch/http/https/tls hooks; no OS-firewall or historical-traffic claim' });
module.exports = { classify, logfile };
