export function toUtcMidnight(value) {
  if (!value) return '';
  const date = String(value).slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(date) ? `${date}T00:00:00Z` : '';
}
