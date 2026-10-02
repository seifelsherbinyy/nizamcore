// Contract: PFOS Contract 14 (research evidence machinery) - task NIZAM-SLACK-FINANCE-007, track_r.
// Phase: research retrieval harness. Additive tool; changes no existing validator behaviour.
//
// Purpose: retrieve candidate sources over HTTPS, hash the EXACT retrieved bytes, and emit a
// machine-checkable retrieval record. A source that this harness does not retrieve does not exist
// and must never be written into an evidence artifact by hand.
//
// Integrity properties this harness enforces, because the whole value of a hashed source base is
// that padding is detectable rather than merely discouraged:
//   - the sha256 is over the exact response bytes, never over a re-encoded or extracted rendering
//   - the recorded url is the FINAL url after redirects, so the hash always corresponds to the
//     document actually cited
//   - a redirect that lands on a site root while the request had a deep path is reported as a
//     SOFT_404 and is NOT retrievable, because a 200 from a homepage is not the document requested
//   - retrievedAt is ISO-8601 with milliseconds and a Z suffix, and is asserted to round-trip
//   - nothing is written for a failed fetch; failures are reported so the real count can be stated
//
// Usage: node scripts/kiro/retrieve.mjs <candidates.json> <out.json>

import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const CONCURRENCY = 6;
const TIMEOUT_MS = 25_000;
const EXCERPT_MAX = 400;

/** ISO-8601 with milliseconds and Z, asserted to round-trip. */
export function stamp(date = new Date()) {
  const iso = date.toISOString();
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(iso)) {
    throw new Error(`RETRIEVE_STAMP_SHAPE: ${iso}`);
  }
  if (new Date(iso).toISOString() !== iso) {
    throw new Error(`RETRIEVE_STAMP_ROUNDTRIP: ${iso}`);
  }
  return iso;
}

/**
 * A redirect to a shallower path than requested means the document was not served.
 * Treating that 200 as a retrieval is how a source base acquires entries nobody can read.
 */
export function softNotFound(requested, final) {
  const a = new URL(requested);
  const b = new URL(final);
  const requestedDepth = a.pathname.split('/').filter(Boolean).length;
  const finalDepth = b.pathname.split('/').filter(Boolean).length;
  if (requestedDepth >= 2 && finalDepth === 0) return true;
  return requestedDepth >= 3 && finalDepth <= 1;
}

/**
 * A 200 response whose whole body is a redirect notice is not the document requested. Both
 * top10.owasp.org pages returned exactly this during real retrieval: status 200, a body reading
 * "Redirecting to OWASP Top 10:2021 ...", and a path deep enough that softNotFound could not see it.
 * Hashing that and citing it would record a stub as a standard.
 */
export function redirectStub(bodyText) {
  const t = String(bodyText).trim();
  return t.length < 400 && /^redirect(ing)?\b/i.test(t);
}

/** Strip tags for a readable excerpt. The hash is over the raw bytes, never over this. */
export function textOf(buf) {
  return buf
    .toString('utf8')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

export function titleOf(buf) {
  const m = /<title[^>]*>([\s\S]{0,300}?)<\/title>/i.exec(buf.toString('utf8'));
  return m && m[1] ? m[1].replace(/\s+/g, ' ').trim() : '';
}

/**
 * Locate the excerpt that carries the candidate's claim. `probe` is a literal the caller expects
 * to appear in the document; when it does, the excerpt is the window around it and the locator is
 * precise. When it does not, that is itself reported so the source is not marked ASSESSED on a
 * passage nobody confirmed.
 */
export function excerptFor(buf, probe) {
  const text = textOf(buf);
  if (probe) {
    const at = text.toLowerCase().indexOf(String(probe).toLowerCase());
    if (at >= 0) {
      const from = Math.max(0, at - 120);
      return { excerpt: text.slice(from, from + EXCERPT_MAX), probeFound: true, probeOffset: at };
    }
  }
  return { excerpt: text.slice(0, EXCERPT_MAX), probeFound: false, probeOffset: -1 };
}

async function one(candidate) {
  const started = Date.now();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(candidate.url, {
      redirect: 'follow',
      signal: controller.signal,
      headers: { 'user-agent': 'nizam-research-retrieval/1 (+local, no credentials)' },
    });
    const buf = Buffer.from(await res.arrayBuffer());
    const soft = softNotFound(candidate.url, res.url);
    const stub = redirectStub(textOf(buf));
    const { excerpt, probeFound, probeOffset } = excerptFor(buf, candidate.probe);
    clearTimeout(timer);
    return {
      ...candidate,
      requestedUrl: candidate.url,
      url: res.url,
      status: res.status,
      redirected: res.url !== candidate.url,
      softNotFound: soft,
      redirectStub: stub,
      retrievable: res.ok && !soft && !stub && buf.length > 0,
      bytes: buf.length,
      sha256: createHash('sha256').update(buf).digest('hex'),
      contentType: res.headers.get('content-type') || '',
      title: titleOf(buf),
      excerpt,
      probeFound,
      probeOffset,
      retrievedAt: stamp(),
      ms: Date.now() - started,
    };
  } catch (err) {
    clearTimeout(timer);
    return {
      ...candidate,
      requestedUrl: candidate.url,
      retrievable: false,
      error: String((err && err.message) || err),
      ms: Date.now() - started,
    };
  }
}

async function main() {
  const [, , inPath, outPath] = process.argv;
  if (!inPath || !outPath) {
    console.error('usage: node scripts/kiro/retrieve.mjs <candidates.json> <out.json>');
    process.exit(2);
  }
  const candidates = JSON.parse(await readFile(inPath, 'utf8'));
  const results = new Array(candidates.length);
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(CONCURRENCY, candidates.length) }, async () => {
      for (; ;) {
        const i = next++;
        if (i >= candidates.length) return;
        results[i] = await one(candidates[i]);
      }
    }),
  );

  const ok = results.filter((r) => r.retrievable);
  const bad = results.filter((r) => !r.retrievable);
  const hosts = new Map();
  for (const r of ok) {
    const h = new URL(r.url).hostname;
    hosts.set(h, (hosts.get(h) || 0) + 1);
  }
  const domains = new Map();
  for (const r of ok) domains.set(r.domain, (domains.get(r.domain) || 0) + 1);

  await writeFile(outPath, `${JSON.stringify(results, null, 2)}\n`, 'utf8');
  console.log(
    JSON.stringify(
      {
        candidates: candidates.length,
        retrievable: ok.length,
        failed: bad.length,
        probeFound: ok.filter((r) => r.probeFound).length,
        hosts: Object.fromEntries([...hosts].sort((a, b) => b[1] - a[1])),
        domains: Object.fromEntries([...domains].sort()),
        failures: bad.map((r) => ({
          url: r.requestedUrl,
          status: r.status,
          soft: r.softNotFound,
          stub: r.redirectStub,
          error: r.error,
        })),
      },
      null,
      2,
    ),
  );
}

// Same guard shape as research.mjs, so importing this module for a test never triggers a network run.
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
