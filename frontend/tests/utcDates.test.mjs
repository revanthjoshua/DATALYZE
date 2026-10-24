import test from 'node:test';
import assert from 'node:assert/strict';
import { toUtcMidnight } from '../src/utils/utcDates.mjs';

test('converts a date-only boundary to midnight UTC', () => {
  assert.equal(toUtcMidnight('2026-01-12'), '2026-01-12T00:00:00Z');
});

test('does not invent an optional boundary for an empty value', () => {
  assert.equal(toUtcMidnight(''), '');
});

test('rejects malformed date-only boundaries', () => {
  assert.equal(toUtcMidnight('not-a-date'), '');
});
