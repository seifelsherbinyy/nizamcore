/**
 * Contract: PFOS Contract 14 section 11 - task NIZAM-SLACK-FINANCE-007, track_r.
 * Phase: tests for the retrieval integrity guards.
 *
 * These guards are the reason a source count can be trusted, so they are tested on the cases that
 * actually occurred during real retrieval rather than on invented ones. Importing this module performs
 * no network access: retrieve.mjs only runs main() when it is the process entry point.
 *
 * ALL FIXTURE DATA IS SYNTHETIC apart from the URL shapes and body snippets reproduced from observed
 * responses, which contain no secret, no deployment particular and no financial data.
 */
import assert from 'node:assert/strict';
import test from 'node:test';
import { excerptFor, redirectStub, softNotFound, stamp, textOf, titleOf } from './retrieve.mjs';

test('stamp produces an ISO-8601 instant with milliseconds that round-trips', () => {
  const s = stamp(new Date(Date.UTC(2026, 8, 21, 1, 2, 3, 45)));
  assert.equal(s, '2026-09-21T01:02:03.045Z');
  assert.equal(new Date(s).toISOString(), s);
  assert.match(s, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
});

test('stamp refuses an invalid date rather than emitting a malformed instant', () => {
  assert.throws(() => stamp(new Date(Number.NaN)));
});

test('softNotFound catches a deep path redirected to a site root', () => {
  assert.equal(softNotFound('https://example.org/a/b/c', 'https://example.org/'), true);
  assert.equal(softNotFound('https://example.org/a/b', 'https://example.org/'), true);
});

test('softNotFound catches a deep path collapsed to a single shallow segment', () => {
  assert.equal(softNotFound('https://example.org/a/b/c', 'https://example.org/index'), true);
});

test('softNotFound does not fire on a legitimate same-depth or deeper redirect', () => {
  // The real case: api.slack.com/apis/socket-mode resolved to a deeper docs.slack.dev path.
  assert.equal(
    softNotFound('https://api.slack.com/apis/socket-mode', 'https://docs.slack.dev/apis/events-api/using-socket-mode/'),
    false,
  );
  assert.equal(softNotFound('https://example.org/a', 'https://example.org/'), false);
});

test('redirectStub catches the observed 200-status redirect notice', () => {
  // Verbatim shape of what both top10.owasp.org pages returned with status 200.
  assert.equal(redirectStub('Redirecting... Redirecting to OWASP Top 10:2021 ...'), true);
  assert.equal(redirectStub('  redirecting to somewhere else  '), true);
});

test('redirectStub does not fire on a real document that merely mentions redirection', () => {
  const long = `A guide to HTTP redirection semantics. ${'Redirecting is discussed below. '.repeat(30)}`;
  assert.equal(redirectStub(long), false);
  assert.equal(redirectStub('The server may issue a redirect when the resource has moved permanently, and the client is expected to follow it.'), false);
});

test('textOf strips script and style content rather than inlining it as prose', () => {
  const html = '<html><head><style>.a{color:red}</style><script>var x=1;</script></head><body><p>Real&nbsp;prose &amp; more</p></body></html>';
  const text = textOf(Buffer.from(html, 'utf8'));
  assert.ok(!text.includes('color:red'));
  assert.ok(!text.includes('var x'));
  assert.ok(text.includes('Real prose & more'));
});

test('titleOf recovers the document title and tolerates its absence', () => {
  assert.equal(titleOf(Buffer.from('<title>  A  Title </title>', 'utf8')), 'A Title');
  assert.equal(titleOf(Buffer.from('<p>no title here</p>', 'utf8')), '');
});

test('excerptFor reports whether the claim-bearing literal was actually located', () => {
  const body = Buffer.from(`<p>${'x'.repeat(300)} the located phrase ${'y'.repeat(300)}</p>`, 'utf8');
  const found = excerptFor(body, 'the located phrase');
  assert.equal(found.probeFound, true);
  assert.ok(found.probeOffset > 0);
  assert.ok(found.excerpt.includes('the located phrase'));

  const missing = excerptFor(body, 'a phrase that is absent');
  assert.equal(missing.probeFound, false);
  assert.equal(missing.probeOffset, -1);
});

test('excerptFor locating a literal is NOT evidence of a supporting passage', () => {
  // The finding that reshaped the evidence base: a probe hit lands in navigation chrome far more often
  // than in prose, so probeFound must never be used to assign ASSESSED depth.
  const nav = Buffer.from('<nav>Guides Reference Samples Tools Changelog alert Overview Pagination Rate limits</nav>', 'utf8');
  const hit = excerptFor(nav, 'alert');
  assert.equal(hit.probeFound, true);
  assert.ok(hit.excerpt.includes('Changelog'), 'the located window is a menu, not a passage');
});

test('excerptFor bounds the excerpt', () => {
  const body = Buffer.from(`<p>${'z'.repeat(5000)}</p>`, 'utf8');
  assert.ok(excerptFor(body, null).excerpt.length <= 400);
});
