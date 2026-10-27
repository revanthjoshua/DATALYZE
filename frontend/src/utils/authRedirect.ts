const RETURN_ORIGIN = 'https://datalyze.invalid';
const AUTH_PATH = /^\/(login|register|forgot-password|accept-invite)(?:\/|$)/i;
const UNSAFE_CHARACTERS = /[\\\u0000-\u001f\u007f]/;

/** Keep authenticated deep links local and prevent login redirect loops. */
export const safeReturnPath = (value: unknown): string => {
  if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//') || UNSAFE_CHARACTERS.test(value)) return '/analysis';
  try {
    const parsed = new URL(value, RETURN_ORIGIN);
    const decodedPath = decodeURIComponent(parsed.pathname);
    if (parsed.origin !== RETURN_ORIGIN || decodedPath.startsWith('//') || UNSAFE_CHARACTERS.test(decodedPath) || AUTH_PATH.test(decodedPath)) return '/analysis';
    return parsed.pathname + parsed.search + parsed.hash;
  } catch {
    return '/analysis';
  }
};

/** Router state handles clean logouts; the query survives a full-page 401 redirect. */
export const loginReturnPath = (stateReturnTo: unknown, search: string): string =>
  safeReturnPath(stateReturnTo ?? new URLSearchParams(search).get('returnTo'));

export const expiredSessionLoginPath = (currentPath: string): string =>
  `/login?${new URLSearchParams({ returnTo: safeReturnPath(currentPath) })}`;

/** A delayed request from a previous login must not invalidate the current one. */
export const isCurrentSessionToken = (requestToken: string | null, currentToken: string | null): boolean =>
  Boolean(requestToken && currentToken && requestToken === currentToken);

export const isCurrentSessionAuthorization = (authorization: unknown, currentToken: string | null): boolean =>
  typeof authorization === 'string' && authorization.startsWith('Bearer ') &&
  isCurrentSessionToken(authorization.slice(7), currentToken);
