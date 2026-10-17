import assert from 'node:assert/strict';
import test from 'node:test';
import {
  expiredSessionLoginPath,
  isCurrentSessionAuthorization,
  isCurrentSessionToken,
  loginReturnPath,
  safeReturnPath,
} from '../src/utils/authRedirect.ts';

test('expired report session survives full-page login and either portal choice', () => {
  const destination = '/analysis?report=5&view=forecast#results';
  const loginUrl = new URL(expiredSessionLoginPath(destination), 'https://example.test');
  assert.equal(loginUrl.pathname, '/login');
  assert.equal(loginReturnPath(undefined, loginUrl.search), destination);
  // Both portal buttons carry this resolved path in router state.
  const portalState = { returnTo: loginReturnPath(undefined, loginUrl.search) };
  assert.equal(loginReturnPath(portalState.returnTo, ''), destination);
});

test('clean logged-out navigation keeps router state and the default still opens analysis', () => {
  assert.equal(loginReturnPath('/reports?tab=saved#latest', ''), '/reports?tab=saved#latest');
  assert.equal(loginReturnPath(undefined, ''), '/analysis');
  assert.equal(loginReturnPath(null, '?returnTo=%2Fdata'), '/data');
});

test('router state takes precedence over an unrelated login query', () => {
  assert.equal(loginReturnPath('/reports', '?returnTo=%2Fdata'), '/reports');
  assert.equal(loginReturnPath('https://evil.test', '?returnTo=%2Fdata'), '/analysis');
});

test('local query values and hashes remain intact', () => {
  const destination = '/analysis?label=North%20%26%20South&source=https%3A%2F%2Fexample.test#chart-2';
  assert.equal(safeReturnPath(destination), destination);
  const url = new URL(expiredSessionLoginPath(destination), 'https://example.test');
  assert.equal(loginReturnPath(undefined, url.search), destination);
  assert.equal(safeReturnPath('/data/../analysis?report=5'), '/analysis?report=5');
});

test('external, backslash, control-character, and normalized protocol-relative targets are rejected', () => {
  for (const value of [
    'https://evil.test', 'javascript:alert(1)', '//evil.test', '/\\evil.test',
    '/%5cevil.test', '/%2f%2fevil.test', '/a/..//evil.test',
    '/analysis\n', '/analysis%0a', '/analysis%zz', '', null, 5,
  ]) {
    assert.equal(safeReturnPath(value), '/analysis', String(value));
  }
});

test('auth destinations cannot create login loops, including encoded and mixed-case routes', () => {
  for (const value of [
    '/login', '/login/admin?returnTo=%2Freports', '/LOGIN/employee', '/%6cogin',
    '/login%2fadmin', '/analysis/../login', '/register/admin',
    '/forgot-password/employee', '/accept-invite?token=example',
  ]) {
    assert.equal(safeReturnPath(value), '/analysis', value);
    assert.equal(loginReturnPath(undefined, `?returnTo=${encodeURIComponent(value)}`), '/analysis', value);
  }
});

test('a rejected request only expires the token it actually sent', () => {
  assert.equal(isCurrentSessionAuthorization('Bearer expired-token', 'expired-token'), true);
  assert.equal(isCurrentSessionAuthorization('Bearer expired-token', 'new-login-token'), false);
  assert.equal(isCurrentSessionAuthorization('Bearer expired-token', null), false);
  assert.equal(isCurrentSessionAuthorization(undefined, 'new-login-token'), false);
  assert.equal(isCurrentSessionAuthorization('Basic new-login-token', 'new-login-token'), false);
  assert.equal(isCurrentSessionAuthorization('Bearer ', ''), false);
});

test('background profile responses are accepted only for their original session', () => {
  assert.equal(isCurrentSessionToken('original-token', 'original-token'), true);
  assert.equal(isCurrentSessionToken('original-token', 'new-login-token'), false);
  assert.equal(isCurrentSessionToken('original-token', null), false);
  assert.equal(isCurrentSessionToken(null, null), false);
});
