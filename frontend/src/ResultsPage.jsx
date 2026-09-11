import { useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Award,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Download,
  ExternalLink,
  FileCheck2,
  HardHat,
  Info,
  Link2,
  Share2,
  ShieldCheck,
} from 'lucide-react';
import Navbar from './components/Navbar';

const tabs = ['Recommended Standard', 'Related / Normative Standards', 'Status & Amendments', 'Gap Analysis', 'Certification'];

export default function ResultsPage({ result, onNewSearch, initialQuery }) {
  const [activeTab, setActiveTab] = useState(0);

  // Adapt to the new backend schema
  const recommendedStandards = result?.recommendedStandards ?? [];
  const relatedStandards = result?.relatedStandards ?? [];
  const gapAnalysis = result?.gapAnalysis ?? [];
  const certifications = result?.certifications ?? [];
  const evidence = result?.evidence ?? [];
  const requirements = result?.requirements ?? [];
  const recommendation = result?.recommendation ?? {};
  const explanation = result?.explanation ?? '';

  const primary = recommendedStandards[0] ?? null;

  const productName = primary ? primary.title : (initialQuery || 'Requirement analysis');
  const standardCode = primary ? primary.number : 'No standard identified';
  const standardName = primary ? primary.title : 'Add more detail to improve ranking';
  const confidence = primary ? `${Math.round((primary.relevanceScore || 0) * 100)}% match` : 'Low confidence';
  const extractedRequirements = requirements.length ? requirements.map(r => r.text) : ['No explicit requirements were extracted.'];

  function handleDownloadReport() {
    const reportLines = [
      'BIS Procurement Intelligence — Analysis Report',
      '================================================',
      '',
      `Query: ${result?.query || initialQuery || 'N/A'}`,
      '',
      '--- RECOMMENDED STANDARDS ---',
      ...recommendedStandards.map((s, i) => `${i + 1}. ${s.number} — ${s.title} (Relevance: ${Math.round(s.relevanceScore * 100)}%)`),
      '',
      '--- RELATED STANDARDS ---',
      ...relatedStandards.map((s, i) => `${i + 1}. ${s.number} — ${s.title}`),
      '',
      '--- GAP ANALYSIS ---',
      ...gapAnalysis.map(g => `[${g.coverage}] ${g.requirement}${g.explanation ? ` — ${g.explanation}` : ''}`),
      '',
      '--- CERTIFICATIONS ---',
      ...certifications.map(c => `${c.name}${c.applicable ? ' (APPLICABLE)' : ''} — ${c.description || ''}`),
      '',
      '--- RECOMMENDATION ---',
      recommendation.text || 'N/A',
      '',
      '--- EXPLANATION ---',
      explanation,
      '',
      'Disclaimer: This is an AI-assisted analysis. Verify from official BIS sources.',
    ];
    const blob = new Blob([reportLines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bis-procurement-report.txt';
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleShare() {
    const shareText = `BIS Procurement Analysis: ${standardCode} — ${standardName}. Confidence: ${confidence}.`;
    if (navigator.share) {
      navigator.share({ title: 'BIS Procurement Report', text: shareText }).catch(() => {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(shareText).then(() => {
        alert('Report summary copied to clipboard!');
      });
    } else {
      alert(shareText);
    }
  }

  function getCoverageIcon(coverage) {
    switch (coverage) {
      case 'COVERED': return <CheckCircle2 size={14} style={{ color: '#0ca467' }} />;
      case 'PARTIAL': return <CircleAlert size={14} style={{ color: '#d99b37' }} />;
      case 'NOT_COVERED': return <CircleAlert size={14} style={{ color: '#e0604e' }} />;
      default: return <Info size={14} />;
    }
  }

  function getCoverageLabel(coverage) {
    switch (coverage) {
      case 'COVERED': return 'Covered';
      case 'PARTIAL': return 'Partially covered';
      case 'NOT_COVERED': return 'Not mentioned in tender';
      default: return coverage;
    }
  }

  // ----- Tab content renderers -----

  function renderRecommendedStandard() {
    return (
      <section className="standard-panel" aria-labelledby="standard-title">
        <div className="standard-header">
          <div className="standard-icon"><Award size={22} /></div>
          <div className="standard-copy">
            <span className="section-kicker">Primary Recommended Standard</span>
            <h2 id="standard-title">{standardCode}</h2>
            <p>{standardName}</p>
          </div>
          <div className="standard-actions">
            <button className="primary-small-button" type="button" onClick={() => window.open(`https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/standard_review/Standard_review/Isdetails?ID=${encodeURIComponent(standardCode)}`, '_blank')}>View Standard</button>
            <button className="outline-small-button" type="button" onClick={() => setActiveTab(2)}>View Details</button>
          </div>
        </div>
        <div className="standard-checks">
          <div className="why-standard">
            <h3>Why this standard?</h3>
            {primary?.reason ? (
              <p><CheckCircle2 size={15} /> {primary.reason}</p>
            ) : (
              <>
                <p><CheckCircle2 size={15} /> Product match</p>
                <p><CheckCircle2 size={15} /> Scope match</p>
                <p><CheckCircle2 size={15} /> Relevant to identified requirements</p>
              </>
            )}
          </div>
          <div className="status-box">
            <h3>Standard Status</h3>
            <p className="status-pill"><CheckCircle2 size={14} /> {primary?.status || 'Status unknown'}</p>
            <a href="#evidence" onClick={(e) => { e.preventDefault(); setActiveTab(2); }}>View amendment history <ArrowRight size={14} /></a>
          </div>
        </div>

        {/* Other recommended standards */}
        {recommendedStandards.length > 1 && (
          <div style={{ marginTop: '14px' }}>
            <h3 style={{ fontSize: '11px', color: '#1455ad', marginBottom: '8px' }}>Other Matching Standards</h3>
            {recommendedStandards.slice(1).map((std) => (
              <div key={std.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#f2f8fd', borderRadius: '6px', marginBottom: '6px' }}>
                <div>
                  <strong style={{ color: '#135bc4', fontSize: '13px' }}>{std.number}</strong>
                  <span style={{ marginLeft: '8px', fontSize: '12px', color: '#34496c' }}>{std.title}</span>
                </div>
                <span style={{ fontSize: '12px', color: '#2c8579', fontWeight: 700 }}>{Math.round(std.relevanceScore * 100)}%</span>
              </div>
            ))}
          </div>
        )}
      </section>
    );
  }

  function renderRelatedStandards() {
    return (
      <section className="standard-panel" style={{ padding: '16px 20px' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#173a78', fontSize: '16px', marginBottom: '14px' }}>
          <Link2 size={18} style={{ color: '#1672dc' }} /> Related / Normative Standards
        </h2>
        {relatedStandards.length ? (
          <div className="related-list" style={{ display: 'grid', gap: '12px', gridTemplateColumns: '1fr' }}>
            {relatedStandards.map((item) => (
              <div className="related-item" key={item.id} style={{ display: 'flex', gap: '12px', padding: '14px', border: '1px solid #edf1f2', borderRadius: '8px', background: '#fff' }}>
                <div className="related-icon" style={{ display: 'grid', placeItems: 'center', width: '32px', height: '32px', background: '#edf7f5', color: '#3ca38f', borderRadius: '6px' }}>
                  <Link2 size={16} />
                </div>
                <div style={{ display: 'grid', gap: '6px', flex: 1 }}>
                  <b style={{ color: '#2d8178', fontSize: '14px', margin: 0 }}>{item.number}</b>
                  <span style={{ color: '#405577', fontSize: '13px', lineHeight: 1.4 }}>{item.title}</span>
                  {item.reason && <small style={{ color: '#80959d', fontSize: '11px', marginTop: '2px' }}>{item.reason}</small>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#617493', fontSize: '14px' }}>No related or normative standards found in the knowledge base for this recommendation.</p>
        )}
      </section>
    );
  }

  function renderStatusAmendments() {
    return (
      <section className="standard-panel" style={{ padding: '16px 20px' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#173a78', fontSize: '16px', marginBottom: '14px' }}>
          <Info size={18} style={{ color: '#1672dc' }} /> Standard Status & Version Information
        </h2>
        {recommendedStandards.length ? (
          <div>
            {recommendedStandards.map((std) => (
              <div key={std.id} style={{ padding: '12px', background: '#eef8ff', borderRadius: '8px', marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong style={{ fontSize: '14px', color: '#135bc4' }}>{std.number}</strong>
                    <span style={{ marginLeft: '10px', fontSize: '13px', color: '#34496c' }}>{std.title}</span>
                  </div>
                  <span className="status-pill"><CheckCircle2 size={14} /> {std.status}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#617493', fontSize: '14px' }}>No version information available.</p>
        )}
      </section>
    );
  }

  function renderGapAnalysis() {
    return (
      <section className="standard-panel" style={{ padding: '16px 20px' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#173a78', fontSize: '16px', marginBottom: '14px' }}>
          <CircleAlert size={18} style={{ color: '#efa91e' }} /> Gap Analysis
        </h2>
        {gapAnalysis.length ? (
          <div>
            {gapAnalysis.map((gap, idx) => (
              <div key={idx} className="gap" style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '10px 0', borderTop: idx > 0 ? '1px solid #eff3f3' : 'none' }}>
                {getCoverageIcon(gap.coverage)}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', color: '#294253', fontWeight: 600 }}>{gap.requirement}</div>
                  <div style={{ fontSize: '12px', color: '#617493', marginTop: '3px' }}>
                    <strong>{getCoverageLabel(gap.coverage)}</strong>
                    {gap.explanation && ` — ${gap.explanation}`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#617493', fontSize: '14px' }}>No gaps identified. Your tender specification appears comprehensive.</p>
        )}
      </section>
    );
  }

  function renderCertification() {
    return (
      <section className="standard-panel" style={{ padding: '16px 20px' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#173a78', fontSize: '16px', marginBottom: '14px' }}>
          <ShieldCheck size={18} style={{ color: '#0aaa72' }} /> Certification & Compliance
        </h2>
        {certifications.length ? (
          <div>
            {certifications.map((cert, idx) => (
              <div key={idx} className="cert" style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '12px 0', borderTop: idx > 0 ? '1px solid #eff3f3' : 'none' }}>
                <ShieldCheck size={16} style={{ color: cert.applicable ? '#0ca467' : '#9eafb3', marginTop: '2px' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', color: '#294253', fontWeight: 600 }}>{cert.name}</div>
                  {cert.description && <div style={{ fontSize: '12px', color: '#617493', marginTop: '3px' }}>{cert.description}</div>}
                  {cert.authority && <div style={{ fontSize: '11px', color: '#80959d', marginTop: '3px' }}>Authority: {cert.authority}</div>}
                  {cert.source && <div style={{ fontSize: '11px', color: '#0768d7', marginTop: '3px' }}>Source: {cert.source}</div>}
                </div>
                <span style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '3px 8px',
                  borderRadius: '4px',
                  background: cert.applicable ? '#dff5ed' : '#f0f3f4',
                  color: cert.applicable ? '#25927e' : '#6c757d'
                }}>
                  {cert.applicable ? 'APPLICABLE' : 'NOT REQUIRED'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#617493', fontSize: '14px' }}>ISI marking and applicable compliance information should be verified for this product.</p>
        )}
      </section>
    );
  }

  const tabRenderers = [renderRecommendedStandard, renderRelatedStandards, renderStatusAmendments, renderGapAnalysis, renderCertification];

  return (
    <main className="page-shell results-page" id="results-top">
      <Navbar />
      <div className="results-container">
        <div className="results-toolbar">
          <button className="back-link" type="button" onClick={onNewSearch}><ArrowLeft size={15} /> New Search</button>
          <div className="toolbar-actions">
            <button className="outline-button" type="button" onClick={handleDownloadReport}><Download size={15} /> Download Report</button>
            <button className="outline-button" type="button" onClick={handleShare}><Share2 size={15} /> Share</button>
          </div>
        </div>

        <header className="results-heading">
          <h1>Analysis Results</h1>
          <p>Here are the relevant Indian Standards and insights based on your requirement.</p>
        </header>

        <section className="product-summary" aria-label="Identified product and extracted requirements">
          <div className="product-identity">
            <div className="product-visual"><HardHat size={65} strokeWidth={1.25} /></div>
            <div>
              <span className="section-kicker">Product Identified</span>
              <h2>{productName}</h2>
              <span className="confidence"><CheckCircle2 size={14} /> {confidence}</span>
              <small>Based on your tender document</small>
            </div>
          </div>
          <div className="requirements-box">
            <h3><FileCheck2 size={19} /> Extracted Requirements</h3>
            <ul>{extractedRequirements.map((requirement, i) => <li key={i}>{requirement}</li>)}</ul>
          </div>
        </section>

        {/* Functional tabs */}
        <nav className="results-tabs" aria-label="Analysis result sections">
          {tabs.map((tab, index) => (
            <button
              className={index === activeTab ? 'result-tab active' : 'result-tab'}
              type="button"
              key={tab}
              onClick={() => setActiveTab(index)}
            >
              {tab}
            </button>
          ))}
        </nav>

        {/* Render active tab content */}
        {tabRenderers[activeTab]()}

        {/* Summary insight cards */}
        <section className="insight-grid" aria-label="Additional analysis insights">
          <article className="insight-card" onClick={() => setActiveTab(1)} style={{ cursor: 'pointer' }}>
            <span className="insight-icon blue"><Link2 size={21} /></span>
            <div>
              <h3>Related Standards</h3>
              <strong>{relatedStandards.length}</strong>
              <a href="#related" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setActiveTab(1); }}>View all <ChevronRight size={13} /></a>
            </div>
          </article>
          <article className="insight-card" onClick={() => setActiveTab(3)} style={{ cursor: 'pointer' }}>
            <span className="insight-icon amber"><CircleAlert size={21} /></span>
            <div>
              <h3>Potential Gaps</h3>
              <strong>{gapAnalysis.filter(g => g.coverage !== 'COVERED').length}</strong>
              <a href="#gaps" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setActiveTab(3); }}>See details <ChevronRight size={13} /></a>
            </div>
          </article>
          <article className="insight-card" onClick={() => setActiveTab(4)} style={{ cursor: 'pointer' }}>
            <span className="insight-icon green"><ShieldCheck size={21} /></span>
            <div>
              <h3>Certification</h3>
              <strong>{certifications.length ? certifications.map(c => c.name).join(', ') : 'Not specified'}</strong>
              <a href="#certification" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setActiveTab(4); }}>View info <ChevronRight size={13} /></a>
            </div>
          </article>
        </section>

        {/* Evidence & Sources */}
        <section className="evidence-panel" id="evidence">
          <h2><ExternalLink size={18} /> Evidence &amp; Sources</h2>
          <p>{explanation || 'Recommendation based on the available tender document and BIS standard references.'}</p>
          {evidence.length > 0 && (
            <div style={{ marginTop: '12px' }}>
              {evidence.map((ev) => (
                <div key={ev.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderTop: '1px solid #edf1f2' }}>
                  <div>
                    <strong style={{ fontSize: '12px', color: '#135bc4' }}>{ev.id}</strong>
                    <span style={{ marginLeft: '8px', fontSize: '12px', color: '#54707a' }}>{ev.title}</span>
                    {ev.excerpt && <div style={{ fontSize: '11px', color: '#80959d', marginTop: '2px' }}>"{ev.excerpt}"</div>}
                  </div>
                  {ev.sourceUrl && (
                    <a href={ev.sourceUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: '11px', color: '#0768d7', textDecoration: 'none', fontWeight: 600 }}>
                      Open ↗
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
          {!evidence.length && (
            <a href="#results-top" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>
              Open referenced BIS source <ArrowRight size={14} />
            </a>
          )}
        </section>

        <aside className="disclaimer"><Info size={17} /><p><strong>Note:</strong> This is an AI-assisted analysis based on available data. Please verify the standards and requirements from official BIS sources.</p></aside>
      </div>
    </main>
  );
}
