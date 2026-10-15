/** Keep authenticated deep links local and prevent login redirect loops. */
export const safeReturnPath = (value: unknown): string => {
  if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//') || /[\\\u0000-\u001f\u007f]/.test(value)) return '/analysis';
  try {
    const parsed = new URL(value, window.location.origin);
    if (parsed.origin !== window.location.origin || /^\/(login|register|forgot-password|accept-invite)(?:\/|$)/.test(parsed.pathname)) return '/analysis';
    return parsed.pathname + parsed.search + parsed.hash;
  } catch {
    return '/analysis';
  }
};
