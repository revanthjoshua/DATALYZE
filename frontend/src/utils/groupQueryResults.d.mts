export type GroupQueryRow = {
  key: string;
  label: string;
  value: number | string;
};

export function normalizeGroupQueryResults(
  queryResults: unknown,
  groupBy: string,
  aggCol: string,
  aggFunc: string,
): GroupQueryRow[];
