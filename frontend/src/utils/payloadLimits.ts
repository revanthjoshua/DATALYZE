export type DataCapabilities = {
  max_upload_bytes: number;
  max_request_bytes: number | null;
  max_response_bytes: number | null;
  editor_max_rows: number;
};

export const formatByteLimit = (bytes: number): string => `${Number((bytes / 1_000_000).toFixed(2))} MB`;

export function assertFileWithinLimit(file: Pick<File, 'size'>, limits: DataCapabilities): void {
  if (file.size > limits.max_upload_bytes) {
    throw new Error(`This deployment accepts files up to ${formatByteLimit(limits.max_upload_bytes)} (${limits.max_upload_bytes.toLocaleString()} bytes). Choose a smaller file. The active dataset is unchanged.`);
  }
}

export function assertJsonWithinLimit(payload: unknown, limits: DataCapabilities): void {
  if (limits.max_request_bytes !== null && new TextEncoder().encode(JSON.stringify(payload)).byteLength > limits.max_request_bytes) {
    throw new Error(`This request exceeds the ${formatByteLimit(limits.max_request_bytes)} hosting limit. Reduce the pasted data or edits before trying again. The active dataset is unchanged.`);
  }
}

// Some hosts reject the request before FastAPI can return its usual JSON error.
// Downloads arrive as Blob even on failure; convert only error details, not successful files.
export async function payloadErrorDetail(data: unknown, status?: number): Promise<string | null> {
  let parsed = data;
  if (typeof Blob !== 'undefined' && data instanceof Blob && data.size < 65536) {
    try { parsed = JSON.parse(await data.text()); } catch { /* Use the host fallback below. */ }
  }
  if (parsed && typeof parsed === 'object' && 'detail' in parsed && typeof parsed.detail === 'string') return parsed.detail;
  if (status === 413) return 'This transfer exceeds the hosting limit. Use a smaller file or request. If saving, refresh the dataset before retrying to check whether the change was applied.';
  return null;
}
