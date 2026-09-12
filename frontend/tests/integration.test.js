import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { analyzeRequirement, analyzePdf } from '../src/api.js';
import { relevanceLabel } from '../src/relevance.js';

test('PDF analysis sends the actual file through FormData to the backend', async () => {
  const file = new File(['%PDF-1.4 test content'], 'tender.pdf', { type: 'application/pdf' });
  await analyzePdf(file, async (url, options) => {
    assert.equal(url, 'http://localhost:8000/api/analyze-pdf');
    assert.ok(options.body instanceof FormData);
    assert.equal(options.body.get('file').name, 'tender.pdf');
    assert.equal(await options.body.get('file').text(), '%PDF-1.4 test content');
    assert.equal(options.body.get('limit'), '5');
    assert.equal(options.body.get('embedding_mode'), 'multilingual');
    assert.equal(options.headers, undefined);
    return { ok: true, json: async () => ({ recommendations: [] }) };
  }, 'multilingual');
});

test('PDF backend errors remain visible', async () => {
  await assert.rejects(analyzePdf(new File(['pdf'], 'tender.pdf'), async () => ({
    ok: false, status: 422, json: async () => ({ detail: 'Could not read this PDF' }),
  })), /Could not read this PDF/);
});

test('selector mode passes through the backend only', async () => {
  for (const mode of ['english', 'multilingual']) {
    await analyzeRequirement('11 kV transformer', async (url, options) => {
      assert.equal(url, 'http://localhost:8000/api/analyze');
      assert.equal(JSON.parse(options.body).embedding_mode, mode);
      return { ok: true, json: async () => ({}) };
    }, mode);
  }
});

test('frontend calls the backend with the existing contract', async () => {
  const result = await analyzeRequirement('water pump', async (url, options) => {
    assert.equal(url, 'http://localhost:8000/api/analyze');
    assert.deepEqual(JSON.parse(options.body), { description: 'water pump', limit: 5 });
    return { ok: true, json: async () => ({ recommendation_source: 'ai_service' }) };
  });
  assert.equal(result.recommendation_source, 'ai_service');
});

test('service failures and validation failures are visible', async () => {
  await assert.rejects(analyzeRequirement('water pump', async () => ({ ok: false, status: 503,
    json: async () => ({ detail: 'AI service is unavailable' }) })), /AI service is unavailable/);
  await assert.rejects(analyzeRequirement('x', async () => ({ ok: false, status: 422,
    json: async () => ({ detail: [{ msg: 'invalid' }] }) })), /2,000 characters/);
});

test('raw scores never become confidence percentages', () => {
  for (const score of [-11, 0.02, 0.95, 7.91]) {
    assert.equal(relevanceLabel({ is_mock: true, score, reranker_score: score }), 'Recommended Standard');
    assert.equal(relevanceLabel({ is_mock: false, score }), 'Recommended Standard');
  }
  const component = readFileSync(new URL('../src/ResultsPage.jsx', import.meta.url), 'utf8');
  assert.ok(component.includes('relevanceLabel(primary)'));
  assert.ok(!component.includes('% match'));
  assert.ok(!component.includes('Math.round'));
});

import { presentationText, statusLabel } from '../src/resultPresentation.js';

test('presentation removes boilerplate and retains source content and scope limits', () => {
  assert.equal(presentationText('Fictional fixture scope: PVC pipes for water. Abstract: Pressure resistance.'), 'Scope: PVC pipes for water. Abstract: Pressure resistance.');
  assert.equal(presentationText('Only the first 2,000 extracted PDF characters were checked. A mention is not proof that a specification is adequate or compliant.'), 'Only the first 2,000 extracted PDF characters were checked.');
  assert.equal(presentationText('Demo metadata only. Verify current BIS/QCO applicability from official BIS sources.'), '');
  assert.equal(presentationText('4 of 5 topics mentioned. This is not a compliance verdict. Based on fictional demo metadata.'), '4 of 5 topics mentioned.');
  assert.equal(statusLabel('unverified'), 'Verification pending');
  assert.equal(relevanceLabel(null), 'No recommendation available');
});
