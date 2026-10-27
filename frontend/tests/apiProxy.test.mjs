import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createApiProxy, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES } from '../server/apiProxy.mjs';

const origin = 'https://datalyze-git-codex-analyst-works-fdfde5-revanthjoshuas-projects.vercel.app';
const env = { VERCEL_ENV: 'preview', DATALYZE_API_ORIGIN: origin };
const incoming = 'https://frontend.vercel.app';
const request = (path, init) => new Request(incoming + path, init);
const makeProxy = (fetchUpstream, options = {}) => createApiProxy({
  env, getOidcToken: async () => 'server-workload-token', fetchUpstream, ...options,
});

test('preserves app authentication and JSON while stripping cookies and caller platform tokens', async () => {
  let seen;
  const proxy = makeProxy(async (url, init) => {
    seen = { url, init };
    return Response.json({ id: 12 }, { status: 201, headers: {
      'set-cookie': 'secret=upstream', 'x-vercel-oidc-token': 'never-client',
      'cache-control': 'public, max-age=60', 'x-request-id': 'request-12',
    } });
  });
  const result = await proxy(request('/api/v1/analysis/records?limit=5', {
    method: 'POST', body: '{"name":"Report"}', headers: {
      authorization: 'Bearer application-jwt', 'content-type': 'application/json',
      cookie: 'vercel_sso=private', host: 'attacker.example', 'x-forwarded-host': 'attacker.example',
      'x-vercel-trusted-oidc-idp-token': 'caller-token', 'x-vercel-protection-bypass': 'caller-bypass',
    },
  }));
  assert.equal(result.status, 201);
  assert.equal(seen.url, origin + '/api/v1/analysis/records?limit=5');
  assert.equal(new TextDecoder().decode(seen.init.body), '{"name":"Report"}');
  assert.equal(seen.init.headers.get('authorization'), 'Bearer application-jwt');
  assert.equal(seen.init.headers.get('x-vercel-trusted-oidc-idp-token'), 'server-workload-token');
  for (const header of ['cookie', 'host', 'x-forwarded-host', 'x-vercel-protection-bypass']) {
    assert.equal(seen.init.headers.get(header), null);
  }
  assert.equal(result.headers.get('set-cookie'), null);
  assert.equal(result.headers.get('x-vercel-oidc-token'), null);
  assert.equal(result.headers.get('cache-control'), 'private, no-store');
  assert.equal(result.headers.get('x-request-id'), 'request-12');
});

test('passes multipart bytes and boundary unchanged; does not parse or reserialize', async () => {
  const form = new FormData();
  form.set('file', new Blob(['date,revenue\n2026-01-01,50\n'], { type: 'text/csv' }), 'sales.csv');
  const req = request('/api/v1/data/upload', { method: 'POST', body: form });
  const expected = new Uint8Array(await req.clone().arrayBuffer());
  const proxy = makeProxy(async (_url, init) => {
    assert.deepEqual(init.body, expected);
    assert.equal(init.headers.get('content-type'), req.headers.get('content-type'));
    return Response.json({ rows: 1 });
  });
  assert.equal((await proxy(req)).status, 200);
});

test('blocks internal routes, encoded separators, traversal and non-API routes before token/fetch', async () => {
  const proxy = makeProxy(() => assert.fail('must not fetch'), {
    getOidcToken: () => assert.fail('must not read credentials'),
  });
  for (const path of ['/api/v1/internal/cron', '/api/v1/%69nternal/cron',
    '/api/v1/internal%2fcron', '/api/v1/%2569nternal/cron', '/api/v1/x%5c..%5cinternal/cron',
    '/api/v1/x/../../health', '/api/v1//internal/cron', '/api/v1/auth%2fme',
    '/api/v1/data/dataset/column/a%2Fb', '/api/v1/data/dataset/column/a%5Cb',
    '/health', '/api', '/api/proxy']) {
    assert.equal((await proxy(request(path))).status, 404, path);
  }
});

test('allows spaces and Unicode in a column path without changing the upstream', async () => {
  const proxy = makeProxy(async (url) => {
    assert.equal(url, origin + '/api/v1/data/dataset/column/Net%20Revenue%20%E2%82%B9?format=json');
    return Response.json({ values: [] });
  });
  assert.equal((await proxy(request('/api/v1/data/dataset/column/Net%20Revenue%20%E2%82%B9?format=json'))).status, 200);
});

test('rejects arbitrary targets, credentials, query and preview-to-production misconfiguration', async () => {
  for (const target of ['https://attacker.example', 'http://127.0.0.1', origin + '/',
    origin + '?url=https://attacker.example', origin.replace('https://', 'https://user:pass@'),
    'https://datalyze-gray.vercel.app']) {
    const proxy = makeProxy(() => assert.fail('must not fetch'), { env: { ...env, DATALYZE_API_ORIGIN: target } });
    assert.equal((await proxy(request('/api/v1/auth/me'))).status, 503, target);
  }
});

test('fails closed without the server OIDC credential', async () => {
  for (const getOidcToken of [async () => undefined, async () => { throw new Error('sensitive'); }]) {
    const proxy = makeProxy(() => assert.fail('must not fetch'), { getOidcToken });
    const response = await proxy(request('/api/v1/auth/me'));
    assert.equal(response.status, 503);
    assert.ok(!(await response.text()).includes('sensitive'));
  }
});

test('never follows redirects or relays login locations/cookies', async () => {
  const proxy = makeProxy(async (_url, init) => {
    assert.equal(init.redirect, 'manual');
    return new Response(null, { status: 302, headers: {
      location: 'https://attacker.example/steal', 'set-cookie': 'secret=1',
    } });
  });
  const response = await proxy(request('/api/v1/auth/me'));
  assert.equal(response.status, 502);
  assert.equal(response.headers.get('location'), null);
  assert.equal(response.headers.get('set-cookie'), null);
});

test('bounds actual request bytes even if content-length is absent or understated', async () => {
  for (const headers of [{}, { 'content-length': '1' }]) {
    const proxy = makeProxy(() => assert.fail('oversized body must not reach API'));
    const response = await proxy(request('/api/v1/data/ingest-raw', {
      method: 'POST', headers, body: new Uint8Array(MAX_REQUEST_BYTES + 1),
    }));
    assert.equal(response.status, 413);
  }
});

test('allows request at the configured boundary', async () => {
  const proxy = makeProxy(async (_url, init) => {
    assert.equal(init.body.byteLength, MAX_REQUEST_BYTES);
    return Response.json({ ok: true });
  });
  assert.equal((await proxy(request('/api/v1/data/upload', {
    method: 'POST', body: new Uint8Array(MAX_REQUEST_BYTES),
  }))).status, 200);
});

test('bounds actual response bytes and returns a truthful retry warning', async () => {
  const proxy = makeProxy(async () => new Response(new Uint8Array(MAX_RESPONSE_BYTES + 1)));
  const response = await proxy(request('/api/v1/analysis/run', { method: 'POST', body: '{}' }));
  assert.equal(response.status, 413);
  assert.match((await response.json()).detail, /may have completed/);
});

test('passes application 401 and file download headers without caching user data', async () => {
  const unauthorized = makeProxy(async () => Response.json({ detail: 'Session expired' }, { status: 401 }));
  assert.equal((await unauthorized(request('/api/v1/auth/me'))).status, 401);
  const download = makeProxy(async () => new Response('a,b\n1,2\n', { headers: {
    'content-type': 'text/csv', 'content-disposition': 'attachment; filename="data.csv"',
  } }));
  const response = await download(request('/api/v1/data/dataset/download'));
  assert.equal(response.headers.get('content-disposition'), 'attachment; filename="data.csv"');
  assert.equal(await response.text(), 'a,b\n1,2\n');
});

test('resolves a fresh token for each request and sanitizes timeout errors', async () => {
  let tokens = 0;
  const proxy = makeProxy(async () => Response.json({ ok: true }), { getOidcToken: async () => `token-${++tokens}` });
  await proxy(request('/api/v1/auth/me'));
  await proxy(request('/api/v1/auth/me'));
  assert.equal(tokens, 2);
  const timeout = makeProxy(async () => { throw new DOMException('secret URL', 'TimeoutError'); });
  const response = await timeout(request('/api/v1/auth/me'));
  assert.equal(response.status, 504);
  assert.ok(!(await response.text()).includes('secret URL'));
});

test('routing query parameters cannot override the original path or fixed origin', async () => {
  let seen;
  const proxy = makeProxy(async (url) => { seen = url; return Response.json({ ok: true }); });
  const query = '?path=internal%2Fcron&url=https%3A%2F%2Fattacker.example&limit=2&limit=3';
  assert.equal((await proxy(request('/api/v1/analysis/records' + query))).status, 200);
  assert.equal(seen, origin + '/api/v1/analysis/records' + query);
  // A rewritten destination URL by itself is deliberately not trusted to supply
  // the route via a user-controlled query or forwarded header.
  const blocked = makeProxy(() => assert.fail('must not use query as route'));
  assert.equal((await blocked(request('/api?path=auth%2Fme', {
    headers: { 'x-forwarded-uri': '/api/v1/auth/me' },
  }))).status, 404);
});

test('production only reaches production, while missing and development environments fail closed', async () => {
  const productionOrigin = 'https://datalyze-gray.vercel.app';
  const proxy = makeProxy(async (url) => {
    assert.equal(url, productionOrigin + '/api/v1/auth/me');
    return Response.json({ ok: true });
  }, { env: { VERCEL_ENV: 'production', DATALYZE_API_ORIGIN: productionOrigin } });
  assert.equal((await proxy(request('/api/v1/auth/me'))).status, 200);
  for (const invalid of [{}, { VERCEL_ENV: 'development', DATALYZE_API_ORIGIN: origin },
    { VERCEL_ENV: 'production', DATALYZE_API_ORIGIN: origin },
    { VERCEL_ENV: 'preview', DATALYZE_API_ORIGIN: productionOrigin }]) {
    const blocked = makeProxy(() => assert.fail('must not cross environment'), { env: invalid });
    assert.equal((await blocked(request('/api/v1/auth/me'))).status, 503);
  }
});

test('passes role denials and bodyless mutations with their status intact', async () => {
  const denied = makeProxy(async () => Response.json({ detail: 'Insufficient permission' }, { status: 403 }));
  const denial = await denied(request('/api/v1/data/dataset', { method: 'DELETE' }));
  assert.equal(denial.status, 403);
  assert.equal((await denial.json()).detail, 'Insufficient permission');
  const deleted = makeProxy(async (_url, init) => {
    assert.equal(init.method, 'DELETE');
    return new Response(null, { status: 204 });
  });
  const response = await deleted(request('/api/v1/data/dataset', { method: 'DELETE' }));
  assert.equal(response.status, 204);
  assert.equal(await response.text(), '');
});
