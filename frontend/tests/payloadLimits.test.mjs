import assert from 'node:assert/strict';
import test from 'node:test';
import { assertFileWithinLimit, assertJsonWithinLimit, payloadErrorDetail } from '../src/utils/payloadLimits.ts';

const limits = { max_upload_bytes: 4_000_000, max_request_bytes: 4_250_000, max_response_bytes: 4_000_000, editor_max_rows: 10000 };

test('upload preflight accepts the full advertised file limit and rejects one extra byte', () => {
  assert.doesNotThrow(() => assertFileWithinLimit({ size: 4_000_000 }, limits));
  assert.throws(() => assertFileWithinLimit({ size: 4_000_001 }, limits), /4 MB/);
});

test('JSON preflight counts UTF-8 bytes including the envelope, not characters', () => {
  const payload = { records: [{ text: '₹😀' }] };
  const size = new TextEncoder().encode(JSON.stringify(payload)).byteLength;
  assert.doesNotThrow(() => assertJsonWithinLimit(payload, { ...limits, max_request_bytes: size }));
  assert.throws(() => assertJsonWithinLimit(payload, { ...limits, max_request_bytes: size - 1 }), /active dataset is unchanged/);
  assert.doesNotThrow(() => assertJsonWithinLimit(payload, { ...limits, max_request_bytes: null }));
});

test('a rejected CSV download retains its server explanation even when Axios returns a Blob', async () => {
  const detail = 'The stored dataset is unchanged. Use a local deployment to access the complete data.';
  assert.equal(await payloadErrorDetail(new Blob([JSON.stringify({ detail })]), 413), detail);
  assert.equal(await payloadErrorDetail({ detail: 'Permission denied.' }, 403), 'Permission denied.');
});

test('a platform HTML 413 is understandable without claiming a rejected response did not save', async () => {
  const detail = await payloadErrorDetail(new Blob(['<html>FUNCTION_PAYLOAD_TOO_LARGE</html>']), 413);
  assert.match(detail, /hosting limit/);
  assert.match(detail, /check whether the change was applied/);
  assert.equal(await payloadErrorDetail('ordinary error', 500), null);
});
