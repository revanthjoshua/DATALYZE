import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeGroupQueryResults } from '../src/utils/groupQueryResults.mjs';

test('normalizes grouped aggregate records for display', () => {
  const rows = normalizeGroupQueryResults({
    success: true,
    group_by: 'region',
    agg_col: 'revenue',
    agg_func: 'sum',
    results: [
      { region: 'North', sum_revenue: 4020, value: 4020 },
      { region: 'South', sum_revenue: 2472, value: 2472 },
    ],
  }, 'region', 'revenue', 'sum');

  assert.deepEqual(rows, [
    { key: 'North:0', label: 'North', value: 4020 },
    { key: 'South:1', label: 'South', value: 2472 },
  ]);
});

test('supports count rows and keeps zero values', () => {
  const rows = normalizeGroupQueryResults({
    group_by: 'region',
    agg_func: 'count',
    results: [
      { region: 'North', count: 0 },
      { region: 'South', value: 2 },
    ],
  }, 'region', 'revenue', 'sum');

  assert.deepEqual(rows.map(({ label, value }) => ({ label, value })), [
    { label: 'North', value: 0 },
    { label: 'South', value: 2 },
  ]);
});

test('returns no rows for a malformed or empty result instead of rendering metadata', () => {
  assert.deepEqual(normalizeGroupQueryResults({ success: true, count: 2 }, 'region', 'revenue', 'sum'), []);
  assert.deepEqual(normalizeGroupQueryResults({ results: [] }, 'region', 'revenue', 'sum'), []);
});
