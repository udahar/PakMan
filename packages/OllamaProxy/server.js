/**
 * Updated-On: 2026-03-05
 * Updated-By: Codex
 * PM-Ticket: UNTRACKED
 *
 * OllamaBot (Simplified)
 *
 * Design goals (per Richard):
 * - behave like a port forwarder with light routing
 * - 1 inbound port, 2 upstream Ollama instances
 * - "pick the empty one"
 * - DO NOT flood upstream; run strictly 1 request at a time per upstream
 * - benchmarking must be serialized (local=1, cloud=1) and should WAIT (not hard-reject)
 *
 * Key fix vs previous implementation:
 * - do NOT create a new proxy middleware per request (that causes socket churn/TIME_WAIT storms)
 */

import 'dotenv/config';
import express from 'express';
import PQueue from 'p-queue';
import http from 'http';
import https from 'https';
import { URL, pathToFileURL } from 'url';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';

// --- CONFIGURATION ---
const OLLAMA_TARGETS = (process.env.OLLAMA_TARGETS || process.env.OLLAMA_TARGET || 'http://localhost:11434,http://localhost:11436')
  .split(',')
  .map(t => t.trim());

const PORT = Number(process.env.PORT || '11435');
const PROXY_TIMEOUT_MS = Number(process.env.PROXY_TIMEOUT_MS || '300000');
const LOCAL_CONCURRENCY = Math.max(1, Number(process.env.OLLAMABOT_LOCAL_CONCURRENCY || '2'));
const CLOUD_CONCURRENCY = Math.max(1, Number(process.env.OLLAMABOT_CLOUD_CONCURRENCY || '1'));
const EMBEDDING_CONCURRENCY = Math.max(1, Number(process.env.OLLAMABOT_EMBEDDING_CONCURRENCY || '1'));
const IDEMPOTENCY_TTL_MS = Math.max(5_000, Number(process.env.OLLAMABOT_IDEMPOTENCY_TTL_MS || '45000'));
const MAX_ATTEMPTS_PER_REQUEST = Math.max(0, Number(process.env.OLLAMABOT_MAX_ATTEMPTS || '2'));
const RETRY_BACKOFF_BASE_MS = Math.max(100, Number(process.env.OLLAMABOT_RETRY_BACKOFF_BASE_MS || '1200'));
const DEAD_LETTER_MAX = Math.max(10, Number(process.env.OLLAMABOT_DEAD_LETTER_MAX || '200'));
const DEBUG_QUEUE_KEY = String(process.env.OLLAMABOT_DEBUG_KEY || '').trim();

const LOG_PATH = process.env.OLLAMABOT_LOG_PATH || path.join(process.cwd(), 'ollamabot.log');
const LOCAL_TARGET = OLLAMA_TARGETS[0];
const CLOUD_TARGET = OLLAMA_TARGETS[1] || OLLAMA_TARGETS[0];
const EMBEDDING_TARGET =
  String(process.env.OLLAMA_EMBEDDING_TARGET || process.env.OLLAMA_EMBEDDING_URL || OLLAMA_TARGETS[2] || 'http://127.0.0.1:11437').trim();

function ts() {
  return new Date().toISOString();
}

function logLine(line) {
  const msg = String(line);
  console.log(msg);
  try {
    fs.appendFileSync(LOG_PATH, msg + '\n', { encoding: 'utf8' });
  } catch {}
}

function safeJsonFromBody(req) {
  try {
    const ct = String(req.headers['content-type'] || '');
    if (!ct.includes('application/json')) return null;
    if (!req.body || !Buffer.isBuffer(req.body) || req.body.length === 0) return null;
    // Protect logs from huge bodies
    if (req.body.length > 256 * 1024) return { _note: 'body_too_large_to_log', bytes: req.body.length };
    return JSON.parse(req.body.toString('utf8'));
  } catch {
    return null;
  }
}

const app = express();

// --- STATE & METRICS ---
// Per-target strict serialization: concurrency=1 for each upstream.
const perTargetQueues = new Map();
for (const target of Array.from(new Set([LOCAL_TARGET, CLOUD_TARGET, EMBEDDING_TARGET].filter(Boolean)))) {
  const lc = String(target || '').trim().toLowerCase();
  const concurrency = lc === String(LOCAL_TARGET || '').trim().toLowerCase()
    ? LOCAL_CONCURRENCY
    : lc === String(CLOUD_TARGET || '').trim().toLowerCase()
      ? CLOUD_CONCURRENCY
      : EMBEDDING_CONCURRENCY;
  perTargetQueues.set(target, new PQueue({ concurrency }));
}
const localBenchQueue = new PQueue({ concurrency: 1 });

// Lightweight stats (no ticketing/pooling semantics; just visibility)
const targetStats = {};
for (const target of perTargetQueues.keys()) {
  targetStats[target] = { inFlight: 0, totalProcessed: 0, avgResponseTime: 0, lastUsed: Date.now() };
}

let totalRequests = 0;
let totalWaitTimeMs = 0;
let maxWaitTimeMs = 0;
let duplicateInFlightRejected = 0;
let duplicateRecentRejected = 0;

const inFlightRequestKeys = new Map();
const recentlyCompletedKeys = new Map();
const deadLetter = [];

// --- UTILITIES ---
function getPurpose(req) {
  return String(req.headers['x-ollamabot-purpose'] || '').toLowerCase();
}

function isCloudBenchRequest(req) {
  const purpose = getPurpose(req);
  return purpose === 'cloud-bench' || purpose === 'cloudbench';
}

function isLocalBenchRequest(req) {
  const purpose = getPurpose(req);
  // local benchmark / llm-bench: treat as serialized low-priority traffic
  return purpose === 'llm-bench' || purpose === 'llmbench' || purpose === 'benchmark' || purpose === 'local-bench' || purpose === 'localbench';
}

function isEmbeddingBenchRequest(req) {
  const purpose = getPurpose(req);
  if (purpose === 'embedding-bench' || purpose === 'embed-bench' || purpose === 'embedding' || purpose === 'embed') return true;
  return String(req.path || '').toLowerCase() === '/api/embed';
}

function isSystemTaskRequest(req) {
  const purpose = getPurpose(req);
  return purpose === 'system-task' || purpose === 'system' || purpose === 'worker';
}

function isChatLikePath(req) {
  const p = String(req.path || '');
  return (
    p === '/api/chat' ||
    p === '/api/generate' ||
    p.startsWith('/v1/chat/') ||
    p.includes('/completions')
  );
}

function isInfoPath(req) {
  const p = String(req.path || '');
  return p === '/api/tags' || p === '/api/version' || p === '/api/ps' || p === '/v1/models';
}

function resolvePriorityLevel(req) {
  const requested = Number(req.headers['x-ollamabot-priority'] || 0);
  if ([1, 2, 3, 4].includes(requested)) return requested;
  if (isCloudBenchRequest(req) || isLocalBenchRequest(req) || isEmbeddingBenchRequest(req)) return 4;
  if (isChatLikePath(req)) return 1;
  if (isSystemTaskRequest(req)) return 2;
  return 3;
}

function queuePriority(level) {
  const l = Number(level || 3);
  if (l <= 1) return 400;
  if (l === 2) return 300;
  if (l === 3) return 200;
  return 100;
}

function requestAttempt(req) {
  const h = Number(req.headers['x-ollamabot-attempt'] || 0);
  if (Number.isFinite(h) && h >= 0) return Math.floor(h);
  return 0;
}

function shouldRetryByBudget(req) {
  return requestAttempt(req) <= MAX_ATTEMPTS_PER_REQUEST;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, ms)));
}

async function waitForLocalBenchDrain() {
  while ((localBenchQueue.pending || 0) > 0 || (localBenchQueue.size || 0) > 0) {
    await sleep(100);
  }
}

function cleanupRecentCompletions() {
  const now = Date.now();
  for (const [k, ts] of recentlyCompletedKeys.entries()) {
    if ((now - ts) > IDEMPOTENCY_TTL_MS) recentlyCompletedKeys.delete(k);
  }
}

function requestFingerprint(req) {
  const hKey = String(req.headers['x-idempotency-key'] || '').trim();
  if (hKey) return `hdr:${hKey.slice(0, 256)}`;
  const bodyHash = crypto
    .createHash('sha1')
    .update(req.body && Buffer.isBuffer(req.body) ? req.body.subarray(0, 131072) : Buffer.from(''))
    .digest('hex');
  const purpose = getPurpose(req) || '';
  return `auto:${req.method}:${String(req.path || '')}:${purpose}:${bodyHash}`;
}

function pushDeadLetter(entry) {
  deadLetter.unshift({
    at: new Date().toISOString(),
    ...entry
  });
  if (deadLetter.length > DEAD_LETTER_MAX) deadLetter.length = DEAD_LETTER_MAX;
}

function validateDebugKey(req, res) {
  if (!DEBUG_QUEUE_KEY) return true;
  const supplied = String(req.headers['x-ollamabot-debug-key'] || req.query?.api_key || '').trim();
  if (supplied && supplied === DEBUG_QUEUE_KEY) return true;
  res.status(403).json({ error: 'debug_access_denied' });
  return false;
}

function pickTarget(req) {
  const local = LOCAL_TARGET;
  const cloud = CLOUD_TARGET;
  const embed = EMBEDDING_TARGET;

  // Always pin info endpoints to local so apps see a consistent model list.
  if (isInfoPath(req)) return local;

  if (isEmbeddingBenchRequest(req)) return embed;

  // Pin benchmark classes to predictable upstreams.
  if (isCloudBenchRequest(req)) return cloud;
  if (isLocalBenchRequest(req)) return local;

  // Default for chat-like endpoints: local.
  // (Prevents "model not found" 404s when cloud/local don't have identical model sets.)
  if (isChatLikePath(req)) return local;

  // Everything else: "pick the empty one".
  const qa = perTargetQueues.get(local);
  const qb = perTargetQueues.get(cloud);
  const aDepth = (qa?.pending || 0) + (qa?.size || 0);
  const bDepth = (qb?.pending || 0) + (qb?.size || 0);

  if (aDepth === 0) return local;
  if (bDepth === 0) return cloud;
  return aDepth <= bDepth ? local : cloud;
}

function proxyOnce(req, res, target, next) {
  const stats = targetStats[target];
  if (stats) {
    stats.inFlight++;
    stats.lastUsed = Date.now();
  }

  const reqBodyJson = safeJsonFromBody(req);
  const model = reqBodyJson && typeof reqBodyJson === 'object' ? reqBodyJson.model : undefined;
  const purpose = getPurpose(req) || undefined;

  const upstream = new URL(target);
  const isHttps = upstream.protocol === 'https:';
  const client = isHttps ? https : http;

  // Copy headers but let Node set Host appropriately.
  const headers = { ...req.headers };
  delete headers.host;

  // If we have a buffered body, set content-length.
  if (req.body && req.body.length != null) {
    headers['content-length'] = String(req.body.length);
  }

  const upReq = client.request(
    {
      protocol: upstream.protocol,
      hostname: upstream.hostname,
      port: upstream.port,
      method: req.method,
      path: (req.originalUrl || req.url || '/'),
      headers,
      timeout: PROXY_TIMEOUT_MS,
    },
    (upRes) => {
      // Forward status + headers
      res.statusCode = upRes.statusCode || 502;
      for (const [k, v] of Object.entries(upRes.headers)) {
        if (v !== undefined) res.setHeader(k, v);
      }

      const responseStart = Date.now();
      upRes.on('end', () => {
        const ms = Date.now() - responseStart;
        if (stats) {
          stats.totalProcessed++;
          stats.avgResponseTime = (stats.avgResponseTime * (stats.totalProcessed - 1) + ms) / stats.totalProcessed;
          stats.inFlight = Math.max(0, stats.inFlight - 1);
        }
      });

      upRes.pipe(res);
    }
  );

  upReq.on('timeout', () => {
    const err = new Error('upstream timeout');
    logLine(`[OllamaBot] ${ts()} ERROR timeout target=${target} ${req.method} ${req.path}` +
      (purpose ? ` purpose=${purpose}` : '') +
      (model ? ` model=${model}` : '')
    );
    upReq.destroy(err);
  });

  upReq.on('error', (err) => {
    if (stats) stats.inFlight = Math.max(0, stats.inFlight - 1);

    logLine(`[OllamaBot] ${ts()} ERROR proxy target=${target} ${req.method} ${req.path} msg=${JSON.stringify(err?.message || String(err))}` +
      (purpose ? ` purpose=${purpose}` : '') +
      (model ? ` model=${model}` : '')
    );

    if (!res.headersSent) {
      res.status(502).json({ error: err?.message || String(err) });
    }
    try { res.end(); } catch {}
    next?.(err);
  });

  try {
    if (req.body && req.body.length) {
      upReq.write(req.body);
    }
  } catch {}
  upReq.end();
}

// --- MIDDLEWARE ---

// Body parser for raw proxying
app.use(express.raw({ type: '*/*', limit: '25mb' }));

// Request Logger (Pre-Queue)
app.use((req, res, next) => {
  if (['/health', '/api/tags', '/api/version', '/api/ps', '/favicon.ico'].includes(req.path)) return next();

  const bodyJson = safeJsonFromBody(req);
  const model = bodyJson && typeof bodyJson === 'object' ? bodyJson.model : undefined;
  const purpose = getPurpose(req) || undefined;

  logLine(`[OllamaBot] ${ts()} incoming ${req.method} ${req.path}` +
    (purpose ? ` purpose=${purpose}` : '') +
    (model ? ` model=${model}` : '')
  );

  // Log response summary (especially useful for failures)
  res.on('finish', () => {
    if (res.statusCode >= 400) {
      logLine(`[OllamaBot] ${ts()} response ${res.statusCode} ${req.method} ${req.path}` +
        (purpose ? ` purpose=${purpose}` : '') +
        (model ? ` model=${model}` : '')
      );
    }
  });

  next();
});

// --- ENDPOINTS ---

// NOTE: Removed circuit-breaker logic.
// The desired behavior is simple serialization (cloud bench=1 at a time) and waiting,
// not opening/closing circuits or rejecting traffic at the proxy layer.

// Health / metrics endpoint
app.get('/health', (req, res) => {
  const q = {};
  for (const t of perTargetQueues.keys()) {
    const qt = perTargetQueues.get(t);
    const lc = String(t || '').trim().toLowerCase();
    const concurrency = lc === String(LOCAL_TARGET || '').trim().toLowerCase()
      ? LOCAL_CONCURRENCY
      : lc === String(CLOUD_TARGET || '').trim().toLowerCase()
        ? CLOUD_CONCURRENCY
        : EMBEDDING_CONCURRENCY;
    q[t] = {
      concurrency,
      active: qt?.pending || 0,
      queued: qt?.size || 0,
    };
  }

  res.json({
    status: 'ok',
    targets: {
      local: LOCAL_TARGET,
      cloud: CLOUD_TARGET,
      embedding: EMBEDDING_TARGET
    },
    target_stats: targetStats,
    queues: q,
    dead_letter_count: deadLetter.length,
    analytics: {
      totalRequests,
      duplicateInFlightRejected,
      duplicateRecentRejected,
      avgWaitMs: totalRequests > 0 ? (totalWaitTimeMs / totalRequests).toFixed(2) : 0,
      maxWaitTimeMs: maxWaitTimeMs || null,
    },
  });
});

app.get('/debug/queue', (req, res) => {
  if (!validateDebugKey(req, res)) return;
  const queueSnapshot = {};
  for (const [target, q] of perTargetQueues.entries()) {
    queueSnapshot[target] = {
      active: q.pending || 0,
      queued: q.size || 0
    };
  }
  queueSnapshot.local_bench_exclusive = {
    active: localBenchQueue.pending || 0,
    queued: localBenchQueue.size || 0
  };

  res.json({
    status: 'ok',
    now: new Date().toISOString(),
    targets: {
      local: LOCAL_TARGET,
      cloud: CLOUD_TARGET,
      embedding: EMBEDDING_TARGET
    },
    queues: queueSnapshot,
    in_flight_keys: inFlightRequestKeys.size,
    recent_completion_keys: recentlyCompletedKeys.size,
    dead_letter_count: deadLetter.length,
    dead_letter_preview: deadLetter.slice(0, 20),
    analytics: {
      totalRequests,
      duplicateInFlightRejected,
      duplicateRecentRejected,
      avgWaitMs: totalRequests > 0 ? (totalWaitTimeMs / totalRequests).toFixed(2) : 0,
      maxWaitTimeMs: maxWaitTimeMs || null
    },
    policy: {
      local_concurrency: LOCAL_CONCURRENCY,
      cloud_concurrency: CLOUD_CONCURRENCY,
      embedding_concurrency: EMBEDDING_CONCURRENCY,
      local_bench_exclusive: true,
      max_attempts: MAX_ATTEMPTS_PER_REQUEST,
      backoff_base_ms: RETRY_BACKOFF_BASE_MS,
      idempotency_ttl_ms: IDEMPOTENCY_TTL_MS,
      debug_key_required: Boolean(DEBUG_QUEUE_KEY)
    }
  });
});

// Pass-through endpoints (stable information)
app.get('/api/version', (req, res, next) => proxyOnce(req, res, OLLAMA_TARGETS[0], next));
app.get('/api/tags', (req, res, next) => proxyOnce(req, res, OLLAMA_TARGETS[0], next));
app.get('/v1/models', (req, res, next) => proxyOnce(req, res, OLLAMA_TARGETS[0], next));
app.get('/api/ps', (req, res, next) => proxyOnce(req, res, OLLAMA_TARGETS[0], next));

// --- REQUEST HANDLER (serialized per upstream) ---
app.all('*', async (req, res, next) => {
  const arrivalTs = Date.now();
  totalRequests += 1;
  cleanupRecentCompletions();

  const priorityLevel = resolvePriorityLevel(req);
  const attempt = requestAttempt(req);
  const reqKey = requestFingerprint(req);

  if (!shouldRetryByBudget(req)) {
    pushDeadLetter({
      reason: 'retry_budget_exhausted',
      key: reqKey,
      method: req.method,
      path: req.path,
      attempt
    });
    res.status(429).json({
      error: 'retry_budget_exhausted',
      attempt,
      max_attempts: MAX_ATTEMPTS_PER_REQUEST
    });
    return;
  }

  if (inFlightRequestKeys.has(reqKey)) {
    duplicateInFlightRejected += 1;
    res.status(202).json({ status: 'duplicate_inflight', key: reqKey });
    return;
  }
  if (recentlyCompletedKeys.has(reqKey)) {
    duplicateRecentRejected += 1;
    res.status(202).json({ status: 'duplicate_recent', key: reqKey, ttl_ms: IDEMPOTENCY_TTL_MS });
    return;
  }

  const target = pickTarget(req);
  const targetQueue = perTargetQueues.get(target);
  if (!targetQueue) {
    res.status(502).json({ error: `No queue/proxy configured for target: ${target}` });
    return;
  }

  const localBenchExclusive = target === LOCAL_TARGET && isLocalBenchRequest(req);
  if (target === LOCAL_TARGET && !localBenchExclusive) {
    await waitForLocalBenchDrain();
  }

  const q = localBenchExclusive ? localBenchQueue : targetQueue;

  if (attempt > 0) {
    const backoffMs = RETRY_BACKOFF_BASE_MS * Math.pow(2, Math.max(0, attempt - 1));
    await sleep(backoffMs);
  }

  inFlightRequestKeys.set(reqKey, Date.now());

  // We WAIT. No hard reject here.
  try {
    await q.add(() => new Promise((resolve, reject) => {
      const startTs = Date.now();
      const waitMs = startTs - arrivalTs;
      totalWaitTimeMs += waitMs;
      maxWaitTimeMs = Math.max(maxWaitTimeMs, waitMs);

      let done = false;
      const finish = (err) => {
        if (done) return;
        done = true;
        if (err) return reject(err);
        resolve();
      };

      // When response completes/terminates, resolve the queue task.
      res.once('finish', () => finish(null));
      res.once('close', () => finish(null));

      proxyOnce(req, res, target, (err) => {
        if (err) {
          if (!res.headersSent) {
            res.status(502).json({ error: err.message || String(err) });
          }
          finish(err);
        }
      });
    }), { priority: queuePriority(priorityLevel) });
  } catch (err) {
    pushDeadLetter({
      reason: 'proxy_failed',
      key: reqKey,
      method: req.method,
      path: req.path,
      priority: priorityLevel,
      target,
      error: err?.message || String(err)
    });
  } finally {
    inFlightRequestKeys.delete(reqKey);
    recentlyCompletedKeys.set(reqKey, Date.now());
  }
});

// --- SERVER START ---

process.on('uncaughtException', (err) => {
  logLine(`[OllamaBot] ${ts()} FATAL uncaughtException: ${err?.stack || err}`);
  process.exit(1);
});
process.on('unhandledRejection', (reason) => {
  logLine(`[OllamaBot] ${ts()} FATAL unhandledRejection: ${reason?.stack || reason}`);
  process.exit(1);
});
process.on('exit', (code) => {
  try { logLine(`[OllamaBot] ${ts()} exiting code=${code}`); } catch {}
});

export function startOllamaProxyServer() {
  if (globalThis.__pakmanOllamaProxyServer) {
    return globalThis.__pakmanOllamaProxyServer;
  }

  const server = app.listen(PORT, () => {
    logLine(`\n[OllamaBot] 🚀 Server started: http://localhost:${PORT}`);
    logLine(`[OllamaBot] 🎯 Upstreams: ${LOCAL_TARGET}, ${CLOUD_TARGET}, embed=${EMBEDDING_TARGET}`);
    logLine(`[OllamaBot] ✅ Concurrency: local=${LOCAL_CONCURRENCY}, cloud=${CLOUD_CONCURRENCY}, embed=${EMBEDDING_CONCURRENCY}`);
    logLine(`[OllamaBot] ✅ Queue policy: priority lanes enabled (1 chat > 2 system > 3 default > 4 bench), retry budget=${MAX_ATTEMPTS_PER_REQUEST}, local bench exclusive lane=ON`);
    logLine(`[OllamaBot] ✅ Dedupe: in-flight + ${IDEMPOTENCY_TTL_MS}ms completion cache`);
    logLine('[OllamaBot] ✅ Default routing: chat/generate + model listing pinned to upstream[0] to prevent model 404s');
    logLine(`[OllamaBot] 📝 Log: ${LOG_PATH}`);
  });

  server.on('error', (err) => {
    if (err && err.code === 'EADDRINUSE') {
      console.error(`[OllamaBot] Port ${PORT} is already in use.`);
      console.error(`[OllamaBot] Stop the existing instance or change PORT in .env.`);
      process.exit(2);
    }
    console.error('[OllamaBot] Fatal server error:', err);
    process.exit(1);
  });

  globalThis.__pakmanOllamaProxyServer = server;
  return server;
}

const entryArg = process.argv[1] ? path.resolve(process.argv[1]) : '';
if (entryArg && import.meta.url === pathToFileURL(entryArg).href) {
  startOllamaProxyServer();
}
