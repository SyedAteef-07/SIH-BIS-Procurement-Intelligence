import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { analyzeRequirement } from '../src/api.js';
import { relevanceLabel } from '../src/relevance.js';

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
    assert.equal(relevanceLabel({ is_mock: true, score, reranker_score: score }), 'Demo recommendation · Unverified');
    assert.equal(relevanceLabel({ is_mock: false, score }), 'Recommended · Unverified');
  }
  const component = readFileSync(new URL('../src/ResultsPage.jsx', import.meta.url), 'utf8');
  assert.ok(component.includes('relevanceLabel(primary)'));
  assert.ok(!component.includes('% match'));
  assert.ok(!component.includes('Math.round'));
});
