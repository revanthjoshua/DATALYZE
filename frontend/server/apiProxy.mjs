// Server-only: this module must never be imported into src/ or a Vite client bundle.
export const MAX_REQUEST_BYTES = 4_250_000;
export const MAX_RESPONSE_BYTES = 4_000_000;
const MAX_UPSTREAM_MS = 280_000;
const ORIGINS = Object.freeze({
  preview: 'https://datalyze-git-codex-analyst-works-fdfde5-revanthjoshuas-projects.vercel.app',
  production: 'https://datalyze-gray.vercel.app',
});
const METHODS = new Set(['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE']);
const REQUEST_HEADERS = ['accept', 'content-type', 'authorization'];
const RESPONSE_HEADERS = ['content-type', 'content-disposition', 'retry-after', 'x-request-id', 'www-authenticate'];

class ProxyError extends Error {
  constructor(status, detail) {
    super(detail);
    this.status = status;
  }
}

function failure(status, detail) {
  return Response.json({ detail }, {
    status,
    headers: { 'cache-control': 'private, no-store', 'x-content-type-options': 'nosniff' },
  });
}

function upstreamOrigin(env) {
  const configured = env.DATALYZE_API_ORIGIN;
  const expected = ORIGINS[env.VERCEL_ENV];
  // An explicit exact allowlist also prevents preview accidentally reaching production.
  if (!expected || configured !== expected) {
    throw new ProxyError(503, 'The API connection is not configured for this environment.');
  }
  return expected;
}

function upstreamPath(request) {
  const url = new URL(request.url);
  // Never reinterpret an encoded slash or backslash as an API route boundary.
  // Ordinary encoded Unicode and spaces in column names remain supported.
  if (/%(?:2f|5c)/i.test(url.pathname)) {
    throw new ProxyError(404, 'API route not found.');
  }
  let path;
  try {
    path = decodeURIComponent(url.pathname);
  } catch {
    throw new ProxyError(400, 'Invalid API path.');
  }
  if (!path.startsWith('/api/v1/') ||
      /[%\\?#\u0000-\u001f\u007f]/u.test(path) ||
      path.includes('//') ||
      path.split('/').some(segment => segment === '.' || segment === '..')) {
    throw new ProxyError(404, 'API route not found.');
  }
  if (/^\/api\/v1\/internal(?:\/|$)/i.test(path)) {
    throw new ProxyError(404, 'API route not found.');
  }
  // Encode segments independently: column names can contain spaces and Unicode.
  return path.split('/').map(encodeURIComponent).join('/') + url.search;
}

async function boundedBody(message, maxBytes, status, detail) {
  const length = message.headers.get('content-length');
  if (length && (!/^\d+$/.test(length) || Number(length) > maxBytes)) {
    await message.body?.cancel();
    throw new ProxyError(status, detail);
  }
  if (!message.body) return null;
  const reader = message.body.getReader();
  const chunks = [];
  let bytes = 0;
  try {
    while (true) {
      const result = await reader.read();
      if (result.done) break;
      bytes += result.value.byteLength;
      if (bytes > maxBytes) {
        await reader.cancel();
        throw new ProxyError(status, detail);
      }
      chunks.push(result.value);
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(bytes);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

export function createApiProxy({ getOidcToken, env = process.env, fetchUpstream = fetch }) {
  return async function proxy(request) {
    try {
      const path = upstreamPath(request);
      const origin = upstreamOrigin(env);
      if (!METHODS.has(request.method)) return failure(405, 'Method not supported.');
      if (request.headers.has('content-encoding')) {
        return failure(415, 'Compressed request bodies are not supported.');
      }
      const body = await boundedBody(request, MAX_REQUEST_BYTES, 413,
        'This request exceeds the hosted upload limit. Use a smaller dataset.');
      // Resolve on every invocation: Vercel rotates this short-lived workload token.
      let token;
      try {
        token = await getOidcToken();
      } catch {
        return failure(503, 'The secure API connection is unavailable.');
      }
      if (!token) return failure(503, 'The secure API connection is unavailable.');
      const headers = new Headers();
      for (const name of REQUEST_HEADERS) {
        const value = request.headers.get(name);
        if (value) headers.set(name, value);
      }
      // Never forward caller cookies, Host, forwarding headers, or any Vercel token.
      headers.set('x-vercel-trusted-oidc-idp-token', token);
      headers.set('accept-encoding', 'identity');
      const response = await fetchUpstream(origin + path, {
        method: request.method,
        headers,
        body: ['GET', 'HEAD'].includes(request.method) ? undefined : body,
        redirect: 'manual',
        signal: AbortSignal.any([request.signal, AbortSignal.timeout(MAX_UPSTREAM_MS)]),
      });
      // A redirect could expose credentials or be Vercel's SSO login. Never follow it.
      if (response.status >= 300 && response.status < 400) {
        await response.body?.cancel();
        return failure(502, 'The secure API connection could not be established.');
      }
      const responseBody = await boundedBody(response, MAX_RESPONSE_BYTES, 413,
        'This result exceeds the hosted response limit. Request a smaller result. Your operation may have completed; refresh before retrying.');
      const responseHeaders = new Headers({
        'cache-control': 'private, no-store',
        'x-content-type-options': 'nosniff',
      });
      for (const name of RESPONSE_HEADERS) {
        const value = response.headers.get(name);
        if (value) responseHeaders.set(name, value);
      }
      // In particular, never relay Set-Cookie, Location, or platform auth headers.
      return new Response(
        request.method === 'HEAD' || [204, 205, 304].includes(response.status) ? null : responseBody,
        { status: response.status, headers: responseHeaders },
      );
    } catch (error) {
      if (error instanceof ProxyError) return failure(error.status, error.message);
      if (error?.name === 'TimeoutError' || error?.name === 'AbortError') {
        return failure(504, 'The API request timed out. Refresh before retrying a change.');
      }
      // Do not log URLs, raw errors, request bodies, app tokens, or OIDC tokens.
      console.error('DATALYZE_API_PROXY_REQUEST_FAILED');
      return failure(502, 'The API is temporarily unavailable.');
    }
  };
}
