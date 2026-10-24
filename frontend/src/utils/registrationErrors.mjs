const fallback = 'Failed to register administrator account. Please check your details.';

export function registrationErrorMessage(error) {
  const detail = error?.response?.data?.detail;

  if (Array.isArray(detail)) {
    const emailIssue = detail.some((item) =>
      Array.isArray(item?.loc) && item.loc.includes('email') && /email|address/i.test(item?.msg || ''),
    );
    if (emailIssue) return 'Enter a valid email address.';

    const messages = detail.map((item) => item?.msg).filter((message) => typeof message === 'string' && message.length < 240);
    return messages.length ? messages.join(' ') : fallback;
  }

  if (typeof detail !== 'string' || !detail.trim()) return fallback;
  if (/\b(email|e-mail)\b/i.test(detail) && /(valid|special-use|reserved|not a valid)/i.test(detail)) {
    return 'Enter a valid email address.';
  }
  if (detail.length > 300 || /Traceback|File ["']?\/var\/task|POST \/api\/v\d/i.test(detail)) {
    return fallback;
  }

  return detail;
}
