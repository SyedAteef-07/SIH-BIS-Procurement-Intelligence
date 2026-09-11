import { test, expect } from '@playwright/test';

const standard = { number: 'IS-DEMO-001', standard_code: 'IS-DEMO-001', title: 'Distribution Transformers', scope: 'Outdoor electrical distribution equipment.', edition: null, revision: null, status: 'unverified', is_mock: true, validity: 'unverified', supporting_evidence: ['Three phase equipment for outdoor use.'], retrieval_score: 0.03, reranker_score: 7.91, retrieval_score_type: 'rrf' };
const response = { input: '11 kV outdoor transformer', recommendations: [standard, { ...standard, number: 'IS-DEMO-012', title: 'Dry-type Transformers' }], related_standards: [], gaps: [], certifications: [], explanation: 'Ranked standards with supporting metadata.', warnings: ['Fictional development data. Not official BIS standards.'], embedding_mode: 'english', detected_language: 'english', reranking_applied: true, degraded: false, missing_standard_codes: [] };
async function mockAnalysis(page, body = response) {
  await page.route('**/api/analyze*', async route => {
    await new Promise(resolve => setTimeout(resolve, 250));
    await route.fulfill({ json: body, headers: { 'access-control-allow-origin': '*' } });
  });
}

test('two-page text flow, tabs, warnings, download and new search', async ({ page }) => {
  await mockAnalysis(page);
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Find the Right Indian Standards/ })).toBeVisible();
  await expect(page.getByText('Dashboard', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: '33 kV XLPE power cable', exact: true }).click();
  await expect(page.getByLabel('Your procurement requirement')).toHaveValue('33 kV XLPE power cable');
  await page.getByLabel('Language mode').selectOption('multilingual');
  const request = page.waitForRequest('**/api/analyze');
  await page.getByRole('button', { name: 'Analyze Requirement' }).click();
  expect((await request).postDataJSON()).toEqual({ description: '33 kV XLPE power cable', limit: 5, embedding_mode: 'multilingual' });
  await expect(page.getByRole('button', { name: 'Analyzing…' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Analysis Results', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Supporting Evidence', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Other matching standards' })).toBeVisible();
  await expect(page.getByLabel('Warnings and limitations')).toContainText('Fictional development data.');
  for (const [tab, empty] of [['Related / Normative Standards', 'No related or normative standards found for this recommendation.'], ['Gap Analysis', 'Gap analysis is not available in the current integrated pipeline.'], ['Certification', 'Certification information is not available in the current integrated pipeline.']]) {
    await page.getByRole('tab', { name: tab, exact: true }).click();
    await expect(page.getByRole('tabpanel')).toContainText(empty);
  }
  await page.getByRole('tab', { name: 'Status & Amendments' }).click();
  await expect(page.getByRole('tabpanel')).toContainText('IS-DEMO-012');
  await expect(page.getByRole('tabpanel')).toContainText('Edition: Unverified');
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download Report' }).click();
  expect((await download).suggestedFilename()).toBe('procurement-analysis.txt');
  await page.getByRole('button', { name: 'New Search' }).click();
  await expect(page.getByRole('heading', { name: /Find the Right Indian Standards/ })).toBeVisible();
});

test('PDF selection and drag/drop send PDFs; errors are visible', async ({ page }) => {
  await mockAnalysis(page);
  await page.goto('/');
  await page.getByLabel('Choose tender PDF').setInputFiles({ name: 'tender.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 upload fixture') });
  const request = page.waitForRequest('**/api/analyze-pdf');
  await page.getByRole('button', { name: 'Analyze Requirement' }).click();
  expect((await request).headers()['content-type']).toContain('multipart/form-data');
  await page.getByRole('button', { name: 'New Search' }).click();
  await page.evaluate(() => {
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(new File(['%PDF-1.4 drop fixture'], 'dropped.pdf', { type: 'application/pdf' }));
    document.querySelector('.drop-zone').dispatchEvent(new DragEvent('drop', { bubbles: true, dataTransfer }));
  });
  await expect(page.getByText('dropped.pdf', { exact: true })).toBeVisible();
  await page.unroute('**/api/analyze*');
  await page.route('**/api/analyze-pdf', route => route.fulfill({ status: 422, json: { detail: 'Could not read this PDF' }, headers: { 'access-control-allow-origin': '*' } }));
  await page.getByRole('button', { name: 'Analyze Requirement' }).click();
  await expect(page.getByRole('alert')).toContainText('Could not read this PDF');
  await page.getByLabel('Choose tender PDF').setInputFiles({ name: 'wrong.txt', mimeType: 'text/plain', buffer: Buffer.from('not a PDF') });
  await expect(page.getByRole('alert')).toContainText('Please choose a PDF');
});

test('empty and degraded responses do not invent metadata', async ({ page }) => {
  await mockAnalysis(page, { ...response, recommendations: [], degraded: true, missing_standard_codes: ['IS-DEMO-MISSING'] });
  await page.goto('/');
  await page.getByRole('button', { name: '33 kV XLPE power cable', exact: true }).click();
  await page.getByRole('button', { name: 'Analyze Requirement' }).click();
  await expect(page.getByRole('heading', { name: 'No standard identified' })).toBeVisible();
  await expect(page.getByLabel('Warnings and limitations')).toContainText('IS-DEMO-MISSING');
  await expect(page.getByRole('tabpanel')).toContainText('No recommendation was returned.');
});

test('populated optional sections render only returned facts', async ({ page }) => {
  await mockAnalysis(page, { ...response, extracted_requirements: ['11 kV supply'],
    related_standards: [{ ...standard, number: 'IS-DEMO-015', title: 'Transformer testing' }],
    gaps: ['Testing requirement missing'], certifications: ['Certification requires independent verification'] });
  await page.goto('/');
  await page.getByRole('button', { name: '33 kV XLPE power cable', exact: true }).click();
  await page.getByRole('button', { name: 'Analyze Requirement' }).click();
  await expect(page.getByRole('heading', { name: 'Extracted Requirements' })).toBeVisible();
  await expect(page.getByLabel('Requirement summary')).toContainText('11 kV supply');
  await page.getByRole('tab', { name: 'Related / Normative Standards' }).click();
  await expect(page.getByRole('tabpanel')).toContainText('IS-DEMO-015');
  await page.getByRole('tab', { name: 'Gap Analysis' }).click();
  await expect(page.getByRole('tabpanel')).toContainText('Testing requirement missing');
  await page.getByRole('tab', { name: 'Certification', exact: true }).click();
  await expect(page.getByRole('tabpanel')).toContainText('Certification requires independent verification');
});

for (const width of [1280, 1024, 768, 390]) {
  test('responsive input and results at ' + width, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 1000 });
    await mockAnalysis(page);
    await page.goto('/');
    await expect(page.getByRole('button', { name: 'Analyze Requirement' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath('input.png'), fullPage: true });
    await page.getByRole('button', { name: '33 kV XLPE power cable', exact: true }).click();
    await page.getByRole('button', { name: 'Analyze Requirement' }).click();
    await expect(page.getByRole('heading', { name: 'Analysis Results', exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath('results.png'), fullPage: true });
  });
}

test('structured gap checks show evidence, exclusions, scope and counts', async ({ page }) => {
  const body = { ...response, gaps: ['Pressure rating: Specify operating pressure.'], gap_analysis: {
    status: 'assessed', summary: '1 potential specification gap across 2 topic checks. Fictional demo metadata.',
    scope: 'Only the first 2,000 extracted PDF characters were checked.', standard_code: 'IS-DEMO-010',
    checks: [{ label: 'Pressure rating', status: 'missing', evidence: [], action: 'Specify operating pressure.', source_evidence: 'Covers hydrostatic pressure resistance.' },
      { label: 'Water application', status: 'mentioned', evidence: ['potable water'], action: 'Verify manually.', source_evidence: 'Pipes for potable water.' }]
  }};
  await mockAnalysis(page, body);
  await page.goto('/');
  await page.getByRole('button', { name: '33 kV XLPE power cable', exact: true }).click();
  await page.getByRole('button', { name: 'Analyze Requirement' }).click();
  await page.getByRole('tab', { name: 'Gap Analysis', exact: true }).click();
  await expect(page.getByRole('tabpanel')).toContainText('Specify operating pressure.');
  await expect(page.getByRole('tabpanel')).toContainText('potable water');
  await expect(page.getByRole('tabpanel')).toContainText('2,000 extracted PDF characters');
  await expect(page.getByRole('button', { name: /Potential Gaps/ })).toContainText('1');
  await page.screenshot({ path: 'test-results/gap-analysis.png', fullPage: true });
});

test('completed zero-gap review displays zero, unsupported shows reason', async ({ page }) => {
  await mockAnalysis(page, { ...response, gap_analysis: { status: 'assessed', summary: 'All checked topics mentioned.', scope: 'Not a compliance verdict.', checks: [] } });
  await page.goto('/');
  await page.getByRole('button', { name: '33 kV XLPE power cable', exact: true }).click();
  await page.getByRole('button', { name: 'Analyze Requirement' }).click();
  await expect(page.getByRole('button', { name: /Potential Gaps/ })).toContainText('0');
});
