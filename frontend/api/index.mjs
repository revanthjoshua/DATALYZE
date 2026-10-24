import { getVercelOidcToken } from '@vercel/oidc';
import { createApiProxy } from '../server/apiProxy.mjs';

const proxy = createApiProxy({ getOidcToken: getVercelOidcToken });

export default { fetch: proxy };
