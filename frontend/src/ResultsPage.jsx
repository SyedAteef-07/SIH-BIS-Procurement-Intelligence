import { useState } from 'react';
import { ArrowLeft, Award, Download, FileCheck2, Info, Link2, Share2, ShieldCheck, Package, CircleAlert } from 'lucide-react';
import BrandHeader from './components/BrandHeader';
import { relevanceLabel } from './relevance';
import './results.css';

const tabs = [['recommended', 'Recommended Standard'], ['related', 'Related / Normative Standards'], ['status', 'Status & Amendments'], ['gaps', 'Gap Analysis'], ['certification', 'Certification']];
const strings = value => Array.isArray(value) ? value.filter(item => typeof item === 'string' && item.trim()) : [];
const code = standard => standard.number || standard.standard_code || 'Identifier unavailable';
function EmptyState({ children }) { return <p className="empty-state">{children}</p>; }
function TextList({ items, empty }) { return items.length ? <ul className="evidence-list">{items.map((item, index) => <li key={index}>{item}</li>)}</ul> : <EmptyState>{empty}</EmptyState>; }
function SafeSource({ url, children }) {
  try { if (!['https:', 'http:'].includes(new URL(url).protocol)) return null; } catch { return null; }
  return <a href={url} target="_blank" rel="noreferrer">{children}</a>;
}
function StandardCard({ standard }) {
  return <article className="other-standard"><div><strong>{code(standard)}</strong><h3>{standard.title}</h3><p>{standard.scope}</p></div><span className="neutral-label">{relevanceLabel(standard)}</span></article>;
}
export default function ResultsPage({ result, initialQuery, onNewSearch }) {
  const [activeTab, setActiveTab] = useState('recommended');
  const [shareNotice, setShareNotice] = useState('');
  const recommendations = result?.recommendations ?? [];
  const relatedStandards = result?.related_standards ?? [];
  const gaps = strings(result?.gaps);
  const gapAnalysis = result?.gap_analysis;
  const certifications = strings(result?.certifications);
  const warnings = strings(result?.warnings);
  const primary = recommendations[0] ?? null;
  const analyzedInput = result?.input || initialQuery || '';
  const requirements = strings(result?.extracted_requirements).length ? strings(result.extracted_requirements) : strings(primary?.requirements);
  const evidence = strings(primary?.supporting_evidence);
  const allStandards = [...new Map([...recommendations, ...relatedStandards].map(s => [code(s), s])).values()];
  function downloadReport() {
    const lines = ['BIS Procurement Intelligence — Analysis', '', analyzedInput, '', ...recommendations.flatMap((s, i) => [`${i + 1}. ${code(s)} — ${s.title}`, relevanceLabel(s), `Status: ${s.status || 'unverified'}; edition: ${s.edition || s.revision || 'unverified'}`, ...strings(s.supporting_evidence), '']), result?.explanation || '', 'Gap Analysis', gapAnalysis?.scope || '', ...(gapAnalysis?.checks || []).flatMap(c => [c.label + ': ' + c.status, c.action, ...c.evidence, 'Metadata context: ' + c.source_evidence]), ...gaps, 'Warnings', ...warnings, 'Metadata validity is unverified.'];
    const url = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'procurement-analysis.txt'; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function share() {
    const text = primary ? `${code(primary)} — ${primary.title}. ${relevanceLabel(primary)}` : 'No recommendation available.';
    try {
      if (navigator.share) { await navigator.share({ title: 'Procurement analysis', text }); setShareNotice('Shared successfully.'); }
      else if (navigator.clipboard) { await navigator.clipboard.writeText(text); setShareNotice('Summary copied to clipboard.'); }
      else setShareNotice('Sharing is unavailable in this browser. Use Download Report instead.');
    } catch (err) { if (err.name !== 'AbortError') setShareNotice('Could not share. Use Download Report instead.'); }
  }
  return <div className="page-shell"><BrandHeader /><main className="results-main">
    <div className="results-toolbar"><button className="text-button" onClick={onNewSearch}><ArrowLeft size={16} />New Search</button><div><button className="outline-button" onClick={downloadReport}><Download size={16} />Download Report</button><button className="outline-button" onClick={share}><Share2 size={16} />Share</button></div></div>
    {shareNotice && <p role="status">{shareNotice}</p>}
    <header className="results-heading"><h1>Analysis Results</h1><p>Here are the relevant Indian Standards and insights based on your requirement.</p></header>
    <section className="product-summary" aria-label="Requirement summary">
      <div className="product-identity"><div className="product-icon"><Package size={48} strokeWidth={1.4} /></div><div><span className="kicker">Product Identified</span><h2>{primary?.title || 'No standard identified'}</h2><span className="neutral-label">{relevanceLabel(primary)}</span><p className="query-preview">{analyzedInput}</p></div></div>
      <div className="summary-evidence"><h3><FileCheck2 size={19} />{requirements.length ? 'Extracted Requirements' : 'Supporting Evidence'}</h3><TextList items={requirements.length ? requirements : evidence} empty="No supporting evidence was returned for this recommendation." /></div>
    </section>
    <nav className="result-tabs" role="tablist" aria-label="Analysis result sections">{tabs.map(([id, label]) => <button key={id} role="tab" id={'tab-' + id} aria-controls="result-panel" aria-selected={activeTab === id} className={activeTab === id ? 'active' : ''} onClick={() => setActiveTab(id)}>{label}</button>)}</nav>
    <section id="result-panel" role="tabpanel" aria-labelledby={'tab-' + activeTab} className="result-panel">
      {activeTab === 'recommended' && (primary ? <>
        <div className="standard-header"><div className="standard-emblem"><Award size={29} /></div><div><span className="kicker">Primary Recommended Standard</span><h2>{code(primary)}</h2><p>{primary.title}</p><small>Edition: {primary.edition || primary.revision || 'Unverified'}</small></div></div>
        <div className="standard-checks"><div><h3>Why this standard?</h3><TextList items={evidence} empty="No supporting evidence was returned." />{primary.scope && <p className="scope"><strong>Scope:</strong> {primary.scope}</p>}</div><div className="status-box"><h3>Standard Status</h3><span className="neutral-label">{primary.status || 'unverified'}</span><p>Edition: {primary.edition || primary.revision || 'Unverified'}</p><p>Validity: {primary.validity || 'unverified'}</p><button className="text-button" onClick={() => setActiveTab('status')}>View status & amendments →</button></div></div>
        {recommendations.length > 1 && <div className="other-standards"><h3>Other matching standards</h3>{recommendations.slice(1).map((s, i) => <StandardCard key={i} standard={s} />)}</div>}
      </> : <EmptyState>No recommendation was returned. Try a more specific requirement.</EmptyState>)}
      {activeTab === 'related' && <><h2>Related / Normative Standards</h2>{relatedStandards.length ? relatedStandards.map((s, i) => <StandardCard key={i} standard={s} />) : <EmptyState>No related or normative standards found for this recommendation.</EmptyState>}</>}
      {activeTab === 'status' && <><h2>Status & Amendments</h2>{allStandards.length ? allStandards.map((s, i) => <article className="status-row" key={i}><div><strong>{code(s)}</strong><p>{s.title}</p></div><div>Status: {s.status || 'unverified'}<br />Edition: {s.edition || s.revision || 'Unverified'}<br /><small>{relevanceLabel(s)}</small></div></article>) : <EmptyState>No standard status information was returned.</EmptyState>}<p className="muted">Amendment history was not provided in this response.</p></>}
      {activeTab === 'gaps' && <><h2>Gap Analysis</h2>{gapAnalysis ? <>
        <p>{gapAnalysis.summary}</p><p className="empty-state">{gapAnalysis.scope}</p>
        {gapAnalysis.standard_code && <p className="muted">Checklist context: {gapAnalysis.standard_code}</p>}
        <div className="gap-checks">{(gapAnalysis.checks || []).map((check, i) => <article className="gap-check" key={i}>
          <div className="gap-check-heading"><h3>{check.label}</h3><span className="neutral-label">{check.status === 'mentioned' ? 'Detail found' : check.status === 'needs_review' ? 'Review exclusion' : 'Not found in analyzed text'}</span></div>
          <p>{check.action}</p>{check.evidence?.length > 0 && <><strong>Tender wording</strong><TextList items={strings(check.evidence)} /></>}
          <p className="muted"><strong>Metadata context:</strong> {check.source_evidence}</p>
        </article>)}</div>
      </> : <TextList items={gaps} empty="Gap analysis is not available in the current integrated pipeline." />}</>}
      {activeTab === 'certification' && <><h2>Certification</h2><TextList items={certifications} empty="Certification information is not available in the current integrated pipeline." /></>}
    </section>
    <section className="insight-grid" aria-label="Analysis summary">{[[Link2, 'Related Standards', relatedStandards.length, 'related'], [CircleAlert, 'Potential Gaps', gapAnalysis?.status === 'assessed' ? gaps.length : gaps.length || 'Not assessed', 'gaps'], [ShieldCheck, 'Certification', certifications.length ? certifications.length + ' returned' : 'Not available', 'certification']].map(([Icon, label, value, id]) => <button key={id} onClick={() => { setActiveTab(id); document.getElementById('result-panel')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }}><span className="feature-icon"><Icon size={24} /></span><span><span className="muted">{label}</span><strong>{value}</strong><small>View details →</small></span></button>)}</section>
    <section className="sources"><h2><Link2 size={19} />Evidence & Sources</h2><p>{result?.explanation || 'No explanation was returned.'}</p><TextList items={evidence} empty="No supporting evidence was returned." />{allStandards.filter(s => s.source_url).map((s, i) => <SafeSource key={i} url={s.source_url}>Source for {code(s)}</SafeSource>)}</section>
    <aside className="disclaimer" aria-label="Warnings and limitations"><Info size={20} /><div><strong>Review before use</strong><p>Recommendation relevance does not verify a standard’s current validity. Demo metadata is not an official BIS publication.</p>{result?.degraded && <p>Results are incomplete. Some standard metadata is unavailable.</p>}{result?.missing_standard_codes?.length > 0 && <p>Missing metadata: {result.missing_standard_codes.join(', ')}</p>}{result?.match_status === 'NO_RELIABLE_MATCH' && <p>No sufficiently reliable match was identified.</p>}{result?.embedding_mode === 'multilingual' && <p>Multilingual demo · {result.detected_language || 'Language unspecified'} · {result.reranking_applied ? 'Reranking applied' : 'English reranker skipped'}</p>}<TextList items={warnings} empty="No additional warnings were returned." /></div></aside>
  </main></div>;
}
