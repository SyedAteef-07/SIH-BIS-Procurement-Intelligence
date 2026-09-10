const baseUrl = (import.meta.env?.VITE_API_BASE_URL || import.meta.env?.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export async function analyzeRequirement(description, fetchImpl = fetch) {
  const response = await fetchImpl(`${baseUrl}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description, limit: 5 }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail
      : response.status === 422 ? 'Enter a meaningful requirement of at most 2,000 characters.'
      : 'Analysis is unavailable. Please try again later.');
  }
  return body;
}
