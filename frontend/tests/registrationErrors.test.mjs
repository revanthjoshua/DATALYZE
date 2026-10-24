import test from 'node:test';
import assert from 'node:assert/strict';
import { registrationErrorMessage } from '../src/utils/registrationErrors.mjs';

test('turns email validation details into a concise form message', () => {
  assert.equal(registrationErrorMessage({
    response: { data: { detail: "Invalid email: special-use or reserved name" } },
  }), 'Enter a valid email address.');
});

test('does not show server paths or route details in registration errors', () => {
  assert.equal(registrationErrorMessage({
    response: { data: { detail: 'Validation failed. File "/var/task/app/api/v1/auth_routes.py" POST /api/v1/auth/register-admin' } },
  }), 'Failed to register administrator account. Please check your details.');
});

test('uses a short validation message when the API returns structured errors', () => {
  assert.equal(registrationErrorMessage({
    response: { data: { detail: [{ loc: ['body', 'username'], msg: 'Username is already taken.' }] } },
  }), 'Username is already taken.');
});
