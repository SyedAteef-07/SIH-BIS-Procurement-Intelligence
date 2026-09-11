import { useState } from 'react';
import { ArrowLeft, Award, CheckCircle2, Download, ExternalLink, FileCheck2, Info, Link2, Share2, ShieldCheck } from 'lucide-react';
import AppShell from './components/AppShell';
import './results.css';

const tabs = [
  { id: 'recommended', label: 'Recommended Standards' },
  { id: 'related', label: 'Related / Normative Standards' },
  { id: 'amendments', label: 'Revisions & Amendments' },
  { id: 'gaps', label: 'Gap Analysis' },
  { id: 'certification', label: 'Certification' },
];

function MatchBadge({ score }) {
  return <span className="results-match-badge"><CheckCircle2 size={14} /> {Math.round((score || 0) * 100)}% match</span>;
}

function EmptyState({ children }) {
  return <p className="results-empty-state">{children}</p>;
}

function StandardCard({ standard, primary = false }) {
  return (
    <article className={primary ? 'result-standard-card is-primary' : 'result-standard-card'}>
      <div className="result-standard-topline">
        <div className="result-standard-icon"><Award size={19} /></div>
        <div className="result-standard-heading">
          <span className="results-kicker">{primary ? 'Primary recommended standard' : 'Related standard'}</span>
          <h3>{standard.number}</h3>
          <p>{standard.title}</p>
        </div>
        <MatchBadge score={standard.score} />
      </div>
      <div className="result-standard-meta"><span><strong>Edition</strong> {standard.edition || 'Not available'}</span><span><strong>Status</strong> {standard.status || 'Not available'}</span></div>
      {standard.scope ? <p className="result-standard-scope">{standard.scope}</p> : null}
      {standard.requirements?.length ? <div className="standard-requirements"><strong>Requirements covered</strong><ul>{standard.requirements.map((item) => <li key={item}>{item}</li>)}</ul></div> : null}
      {standard.matched_terms?.length ? <div className="matched-terms"><strong>Matched concepts</strong>{standard.matched_terms.map((term) => <span key={term}>{term}</span>)}</div> : null}
      {standard.certification ? <p className="result-certification"><ShieldCheck size={15} /> {standard.certification}</p> : null}
    </article>
  );
}

export default function ResultsPage({ result, onNavigate, onNewSearch, initialQuery }) {
  const [activeTab, setActiveTab] = useState('recommended');
  const recommendations = result?.recommendations ?? [];
  const relatedStandards = result?.related_standards ?? [];
  const gaps = result?.gaps ?? [];
  const certifications = result?.certifications ?? [];
  const primary = recommendations[0] ?? null;
  const requirements = primary?.requirements ?? [];
  const analyzedInput = result?.input || initialQuery || 'Requirement analysis';

  function selectTab(tabId) {
    setActiveTab(tabId);
    document.getElementById(`results-${tabId}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  return (
    <AppShell activePage="analyze" currentPage="Analysis Results" onNavigate={onNavigate}>
      <main className="results-workspace" id="results-top">
        <div className="results-toolbar"><button className="results-back-button" type="button" onClick={onNewSearch}><ArrowLeft size={15} /> New Search</button><div className="results-toolbar-actions"><button className="results-secondary-button" type="button"><Download size={15} /> Download Report</button><button className="results-secondary-button" type="button"><Share2 size={15} /> Share</button></div></div>
        <header className="results-page-header"><div><span className="results-kicker">PROCUREMENT INTELLIGENCE REPORT</span><h1>Analysis Results</h1><p>Review the BIS standards, compliance requirements, gaps, and supporting evidence identified for this procurement requirement.</p></div><div className="results-header-status"><span>Analysis complete</span><CheckCircle2 size={16} /></div></header>
        <section className="results-summary-grid" aria-label="Analysis summary"><article className="results-summary-card results-requirement-card"><span className="results-kicker">Requirement analyzed</span><h2>{analyzedInput}</h2><p>Input received from the tender analysis workflow.</p></article><article className="results-summary-card results-score-card"><span className="results-kicker">Top match score</span><strong>{primary ? `${Math.round((primary.score || 0) * 100)}%` : 'N/A'}</strong><p>{primary ? 'Based on the highest-ranked BIS standard.' : 'No ranked standard was returned.'}</p></article><article className="results-summary-card"><span className="results-kicker">Standards identified</span><strong>{recommendations.length}</strong><p>{relatedStandards.length} related references available</p></article></section>
        <section className="results-requirements-panel" aria-labelledby="extracted-requirements-title"><div><h2 id="extracted-requirements-title"><FileCheck2 size={18} /> Extracted requirements</h2><p>Requirements associated with the leading recommendation.</p></div>{requirements.length ? <ul>{requirements.map((requirement) => <li key={requirement}>{requirement}</li>)}</ul> : <EmptyState>No explicit requirements were returned for the leading recommendation.</EmptyState>}</section>
        <nav className="results-tabs" aria-label="Analysis result sections" role="tablist">{tabs.map((tab) => <button className={activeTab === tab.id ? 'results-tab is-active' : 'results-tab'} type="button" role="tab" aria-selected={activeTab === tab.id} key={tab.id} onClick={() => selectTab(tab.id)}>{tab.label}</button>)}</nav>
        <section className="results-section" id="results-recommended" aria-labelledby="recommended-title"><div className="results-section-heading"><div><span className="results-kicker">Ranked recommendations</span><h2 id="recommended-title">Recommended BIS Standards</h2><p>Standards are shown in the order returned by the analysis service.</p></div>{primary ? <span className="results-count">{recommendations.length} found</span> : null}</div>{recommendations.length ? <div className="standards-list">{recommendations.map((standard, index) => <StandardCard key={`${standard.number}-${index}`} standard={standard} primary={index === 0} />)}</div> : <EmptyState>No recommended standards were found for this requirement.</EmptyState>}</section>
        <section className="results-section" id="results-related" aria-labelledby="related-title"><div className="results-section-heading"><div><span className="results-kicker">Connected references</span><h2 id="related-title"><Link2 size={18} /> Related / Normative Standards</h2><p>Additional standards connected to the returned recommendations.</p></div></div>{relatedStandards.length ? <div className="related-list">{relatedStandards.map((standard) => <StandardCard key={standard.number} standard={standard} />)}</div> : <EmptyState>No related or normative standards were found.</EmptyState>}</section>
        <section className="results-section" id="results-amendments" aria-labelledby="amendments-title"><div className="results-section-heading"><div><span className="results-kicker">Edition information</span><h2 id="amendments-title">Revisions &amp; Amendments</h2><p>Current edition and status information returned for the recommended standards.</p></div></div>{recommendations.length ? <div className="amendments-list">{recommendations.map((standard) => <div className="amendment-row" key={standard.number}><div><strong>{standard.number}</strong><span>{standard.title}</span></div><span className="amendment-status">{standard.status || 'Status not available'}</span><span className="amendment-edition">Edition {standard.edition || 'N/A'}</span></div>)}</div> : <EmptyState>No revision or amendment information was returned.</EmptyState>}</section>
        <section className="results-section" id="results-gaps" aria-labelledby="gaps-title"><div className="results-section-heading"><div><span className="results-kicker">Specification review</span><h2 id="gaps-title">Gap Analysis</h2><p>Potential requirement gaps identified by comparing the input with returned standard requirements.</p></div><span className="results-count">{gaps.length} found</span></div>{gaps.length ? <ul className="results-gap-list">{gaps.map((gap) => <li key={gap}><span className="gap-indicator"><Info size={15} /></span><span>{gap}</span></li>)}</ul> : <EmptyState>No potential gaps were identified.</EmptyState>}</section>
        <section className="results-section" id="results-certification" aria-labelledby="certification-title"><div className="results-section-heading"><div><span className="results-kicker">Compliance guidance</span><h2 id="certification-title"><ShieldCheck size={18} /> Certification</h2><p>Certification guidance associated with the returned standards.</p></div></div>{certifications.length ? <ul className="certification-list">{certifications.map((certification) => <li key={certification}><ShieldCheck size={17} /><span>{certification}</span></li>)}</ul> : <EmptyState>No certification guidance was returned.</EmptyState>}</section>
        <section className="results-evidence-panel" aria-labelledby="evidence-title"><div><h2 id="evidence-title"><ExternalLink size={18} /> Evidence &amp; Sources</h2><p>{result?.explanation || 'No explanation was returned for this analysis.'}</p></div><span className="evidence-note">Verify cited editions with official BIS sources before issuing a tender.</span></section>
        <aside className="results-disclaimer"><Info size={17} /><p><strong>Note:</strong> This is an AI-assisted analysis based on available data. Please verify standards and requirements from official BIS sources.</p></aside>
      </main>
    </AppShell>
  );
}
