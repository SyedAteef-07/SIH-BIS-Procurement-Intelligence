# Two-page procurement frontend

The running app is InputPage → ResultsPage → New Search. Dashboard, analytics,
reports, settings, standards-page and AppShell/sidebar imports were removed from
the active flow. Their old source files remain unused. A static BrandHeader
replaces dashboard navigation. No backend, AI, database or root files were changed.

## Contract

The existing `src/api.js` is unchanged. Text uses `/api/analyze`, with
`description`, `limit: 5`, and the selected `embedding_mode`. PDF uses
`analyzePdf()` and `/api/analyze-pdf`, sending the actual file, limit and mode
through FormData. No FileReader text conversion or direct AI :8001 request is used.
Backend errors are displayed as returned. PDF extraction itself remains the
backend's responsibility; frontend tests mock the HTTP boundary.

Response fields consumed:

- `recommendations`, `related_standards`: `number`, `standard_code`, `title`,
  `scope`, `edition`, `revision`, `status`, `is_mock`, `validity`,
  `supporting_evidence`, and optional `source_url`.
- `input`, `gaps`, `certifications`, `explanation`, `warnings`, `degraded`,
  `missing_standard_codes`, `match_status`, `embedding_mode`,
  `detected_language`, `reranking_applied`.
- Optional string lists `extracted_requirements` and leading recommendation
  `requirements` are used only when present and nonempty; otherwise the summary
  explicitly says Supporting Evidence and uses `supporting_evidence`.

No model score is converted to a probability or rendered as a percentage.
`relevanceLabel(primary)` and the existing `relevance.js` are retained. Missing
revisions stay unverified. Empty related/gap/certification sections explain
their availability; no facts are generated to populate the UI.

## Files

Reworked `src/App.jsx`, `InputPage.jsx`, `ResultsPage.jsx`, `index.css`,
`styles.css`, `input.css`, and `results.css`. Added
`src/components/BrandHeader.jsx`. Old dashboard-specific CSS and AppShell are
not imported. Other unused dashboard components were left intact.

Added browser testing through `@playwright/test`, `playwright.config.js`,
`tests/browser/flow.spec.js`, and `npm run test:ui`. Updated package/lock files,
expanded `tests/integration.test.js` for actual PDF FormData and PDF error
propagation, and ignored browser artifacts in the frontend `.gitignore`.

## Verification

From `frontend/`:

```powershell
npm test
npm run build
npm run test:ui
```

Browser tests use installed Microsoft Edge by default. Set
`PLAYWRIGHT_CHANNEL=chrome` if using installed Chrome. Vite runs temporarily on
127.0.0.1:5179 for tests, with backend responses mocked; normal development
continues to use the existing `npm run dev` command and configured backend URL.

Tests cover text and file requests, drag/drop, visible errors/loading, populated
and empty result tabs, download, New Search, and responsive pages at 1280, 1024,
768 and 390 pixels. Screenshots are saved under ignored `test-results/` folders.
The visual design follows the supplied description: pale blue backgrounds,
navy headings, blue calls to action, rounded cards and subtle decorative circles.

Gap analysis now consumes AI-extracted evidence through the backend. The backend checks supported product profiles against database scope/abstract text, preserving AI ranking. Initial demo profiles cover PVC water pipes (dimensions, pressure rating, joints, water application), distribution transformers and insulated power cables. Each topic is marked mentioned, missing, or needs_review (negated wording). Mentioned does not mean adequate or compliant. Gap counts include missing and needs_review topics; zero is distinct from not assessed.

The response adds gap_analysis (status, summary, scope, standard_code, checks) and extracted_requirements; gaps remains a compatible string list. Older AI responses explicitly return not_assessed. Unsupported products/languages, absent metadata and no matches do not produce fabricated findings. PDF findings apply only to analyzed text; truncation is called out in the panel. Related/normative links and certification obligations remain unverified because the fixture does not establish them.

Restart both AI and backend services after updating, and rerun the analysis (old results are not refreshed automatically). No model download, database migration or retrieval configuration change is needed for this feature.
