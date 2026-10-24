export function normalizeGroupQueryResults(queryResults, groupBy, aggCol, aggFunc) {
  if (!queryResults || !Array.isArray(queryResults.results)) return [];

  const groupField = queryResults.group_by || groupBy;
  const valueField = queryResults.agg_col && queryResults.agg_func
    ? `${queryResults.agg_func}_${queryResults.agg_col}`
    : `${aggFunc}_${aggCol}`;

  return queryResults.results.map((row, index) => {
    const groupValue = row?.[groupField] ?? row?.label ?? '(missing)';
    const value = row?.value ?? row?.[valueField] ?? row?.count ?? '—';
    const label = String(groupValue);

    return {
      key: `${label}:${index}`,
      label,
      value,
    };
  });
}
