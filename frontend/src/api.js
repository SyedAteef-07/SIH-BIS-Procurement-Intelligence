const baseUrl = (import.meta.env?.VITE_API_BASE_URL || import.meta.env?.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function parseResponse(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(
      typeof body.detail === 'string'
        ? body.detail
        : response.status === 422
          ? 'Enter a meaningful requirement of at most 2,000 characters, or upload a readable PDF.'
          : 'Analysis is unavailable. Please try again later.'
    );
  }
  return body;
}

export async function analyzeRequirement(description, fetchImpl = fetch, embeddingMode) {
  const response = await fetchImpl(`${baseUrl}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description,
      limit: 5,
      ...(embeddingMode ? { embedding_mode: embeddingMode } : {}),
    }),
  });
  return parseResponse(response);
}

export async function analyzePdf(file, fetchImpl = fetch, embeddingMode = 'english') {
  const form = new FormData();
  form.append('file', file);
  form.append('limit', '5');
  form.append('embedding_mode', embeddingMode);

  const response = await fetchImpl(`${baseUrl}/api/analyze-pdf`, {
    method: 'POST',
    body: form,
  });
  return parseResponse(response);
}
