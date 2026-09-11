import { useState } from 'react';
import {
  ArrowLeft,
  Award,
  CheckCircle2,
  Download,
  ExternalLink,
  FileCheck2,
  Info,
  Link2,
  Share2,
  ShieldCheck,
} from 'lucide-react';
import AppShell from './components/AppShell';
import { relevanceLabel } from './relevance';
import './results.css';

const tabs = [
  { id: 'recommended', label: 'Recommended Standards' },
  { id: 'related', label: 'Related Standards' },
  { id: 'amendments', label: 'Status & Revisions' },
  { id: 'gaps', label: 'Gap Analysis' },
  { id: 'certification', label: 'Certification' },
];

function EmptyState({ children }) {
  return <p className="results-empty-state">{children}</p>;
}

function StandardCard({ standard, primary = false }) {
  const label = relevanceLabel(standard);
  return (
    <article className={primary ? 'result-standard-card is-primary' : 'result-standard-card'}>
      <div className="result-standard-topline">
        <span className="result-standard-icon"><Award size={18} /></span>
        <div className="result-standard-heading">
          <span className="results-kicker">{primary ? 'Primary recommendation' : 'Alternative recommendation'}</span>
          <h3>{standard.number}</h3>
          <p>{standard.title}</p>
        </div>
        <span className="results-match-badge"><CheckCircle2 size={14} /> {label}</span>
      </div>

      {standard.scope ? <p className="result-standard-scope">{standard.scope}</p> : null}

      <div className="result-standard-meta">
        <span><strong>Status:</strong> {standard.status || 'unverified'}</span>
        <span><strong>Edition:</strong> {standard.edition || standard.revision || 'unverified'}</span>
        <span><strong>Validity:</strong> {standard.validity || 'unverified'}</span>
      </div>

      {standard.supporting_evidence?.length ? (
        <div className="standard-requirements">
          <strong>Why it matched</strong>
          <ul>{standard.supporting_evidence.map((item, index) => <li key={index}>{item}</li>)}</ul>
        </div>
      ) : null}
    </article>
  );
}

export default function ResultsPage({ result, onNewSearch, onNavigate, initialQuery }) {
  const [activeTab, setActiveTab] = useState('recommended');

  const recommendations = result?.recommendations ?? [];
  const relatedStandards = result?.related_standards ?? [];
  const gaps = result?.gaps ?? [];
  const certifications = result?.certifications ?? [];
  const warnings = result?.warnings ?? [];
  const primary = recommendations[0] ?? null;
  const analyzedInput = result?.input || initialQuery || 'Requirement analysis';
  const requirements = primary?.requirements ?? [];

  function handleDownloadReport() {
    const lines = [
      'BIS Procurement Intelligence — Demo Analysis',
      '=============================================',
      '',
      `Input: ${analyzedInput}`,
      '',
      'Recommended standards:',
      ...recommendations.map((item, index) => `${index + 1}. ${item.number} — ${item.title}`),
      '',
      'Warnings:',
      ...warnings.map((warning) => `- ${warning}`),
      '',
      'Verify all cited standards and editions against official BIS sources.',
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'bis-procurement-analysis.txt';
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function handleShare() {
    const text = primary
      ? `BIS Procurement Analysis: ${primary.number} — ${primary.title}. ${relevanceLabel(primary)}.`
      : 'BIS Procurement Analysis: no recommendation available.';
    if (navigator.share) {
      navigator.share({ title: 'BIS Procurement Analysis', text }).catch(() => {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => {});
    }
  }

  return (
    <AppShell activePage="analyze" currentPage="Analysis Results" onNavigate={onNavigate}>
      <main className="results-workspace" id="results-top">
        <div className="results-toolbar">
          <button className="results-back-button" type="button" onClick={onNewSearch}>
            <ArrowLeft size={15} /> New Search
          </button>
          <div className="results-toolbar-actions">
            <button className="results-secondary-button" type="button" onClick={handleDownloadReport}>
              <Download size={15} /> Download Report
            </button>
            <button className="results-secondary-button" type="button" onClick={handleShare}>
              <Share2 size={15} /> Share
            </button>
          </div>
        </div>

        <header className="results-page-header">
          <div>
            <span className="results-kicker">PROCUREMENT INTELLIGENCE REPORT</span>
            <h1>Analysis Results</h1>
            <p>{analyzedInput}</p>
          </div>
          <div className="results-header-status">
            <span>{result?.degraded ? 'Analysis incomplete' : 'Analysis complete'}</span>
            <CheckCircle2 size={16} />
          </div>
        </header>

        <section className="results-summary-grid" aria-label="Analysis summary">
          <article className="results-summary-card results-requirement-card">
            <span className="results-kicker">Top recommendation</span>
            <h2>{primary ? `${primary.number} — ${primary.title}` : 'No reliable standard identified'}</h2>
            <p>{relevanceLabel(primary)}</p>
          </article>
          <article className="results-summary-card">
            <span className="results-kicker">Standards identified</span>
            <strong>{recommendations.length}</strong>
            <p>Ranked candidates returned by the AI service</p>
          </article>
          <article className="results-summary-card">
            <span className="results-kicker">Language</span>
            <strong style={{ fontSize: '18px' }}>{result?.detected_language || 'english'}</strong>
            <p>{result?.reranking_applied ? 'CrossEncoder reranking applied' : 'Semantic ranking only'}</p>
          </article>
        </section>

        <section className="results-requirements-panel">
          <div>
            <h2><FileCheck2 size={18} /> Supporting evidence</h2>
            <p>Evidence attached to the leading recommendation.</p>
          </div>
          {primary?.supporting_evidence?.length ? (
            <ul>{primary.supporting_evidence.map((item, index) => <li key={index}>{item}</li>)}</ul>
          ) : (
            <EmptyState>No supporting evidence was returned.</EmptyState>
          )}
        </section>

        <nav className="results-tabs" aria-label="Analysis result sections" role="tablist">
          {tabs.map((tab) => (
            <button
              className={activeTab === tab.id ? 'results-tab is-active' : 'results-tab'}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {activeTab === 'recommended' ? (
          <section className="results-section">
            <div className="results-section-heading">
              <div><span className="results-kicker">Ranked recommendations</span><h2>Recommended Standards</h2></div>
              <span className="results-count">{recommendations.length} found</span>
            </div>
            {recommendations.length ? (
              <div className="standards-list">
                {recommendations.map((standard, index) => (
                  <StandardCard key={`${standard.number}-${index}`} standard={standard} primary={index === 0} />
                ))}
              </div>
            ) : <EmptyState>No recommendation was returned for this requirement.</EmptyState>}
          </section>
        ) : null}

        {activeTab === 'related' ? (
          <section className="results-section">
            <div className="results-section-heading"><div><h2><Link2 size={18} /> Related Standards</h2></div></div>
            {relatedStandards.length ? (
              <div className="related-list">{relatedStandards.map((standard) => <StandardCard key={standard.number} standard={standard} />)}</div>
            ) : <EmptyState>Related/normative relationships are not available in this demo response.</EmptyState>}
          </section>
        ) : null}

        {activeTab === 'amendments' ? (
          <section className="results-section">
            <div className="results-section-heading"><div><h2>Status & Revisions</h2></div></div>
            {recommendations.length ? (
              <div className="amendments-list">
                {recommendations.map((standard) => (
                  <div className="amendment-row" key={standard.number}>
                    <div><strong>{standard.number}</strong><span>{standard.title}</span></div>
                    <span className="amendment-status">{standard.status || 'unverified'}</span>
                    <span className="amendment-edition">{standard.edition || standard.revision || 'unverified'}</span>
                  </div>
                ))}
              </div>
            ) : <EmptyState>No revision information was returned.</EmptyState>}
          </section>
        ) : null}

        {activeTab === 'gaps' ? (
          <section className="results-section">
            <div className="results-section-heading"><div><h2>Gap Analysis</h2></div></div>
            {gaps.length ? (
              <ul className="results-gap-list">{gaps.map((gap, index) => <li key={index}><Info size={15} /><span>{gap}</span></li>)}</ul>
            ) : <EmptyState>Gap analysis is not performed by the current integrated pipeline.</EmptyState>}
          </section>
        ) : null}

        {activeTab === 'certification' ? (
          <section className="results-section">
            <div className="results-section-heading"><div><h2><ShieldCheck size={18} /> Certification</h2></div></div>
            {certifications.length ? (
              <ul className="certification-list">{certifications.map((item, index) => <li key={index}><ShieldCheck size={17} /><span>{item}</span></li>)}</ul>
            ) : <EmptyState>Certification checks are not performed by the current integrated pipeline.</EmptyState>}
          </section>
        ) : null}

        <section className="results-evidence-panel">
          <div>
            <h2><ExternalLink size={18} /> Explanation</h2>
            <p>{result?.explanation || 'No explanation was returned.'}</p>
          </div>
          <span className="evidence-note">Verify standard numbers, editions and status against official BIS sources before procurement.</span>
        </section>

        {warnings.length ? (
          <aside className="results-disclaimer">
            <Info size={17} />
            <div>
              <strong>Demo warnings</strong>
              {warnings.map((warning, index) => <p key={index}>{warning}</p>)}
            </div>
          </aside>
        ) : null}
      </main>
    </AppShell>
  );
}
