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
import { relevanceLabel } from './relevance';

const tabs = ['Recommended Standard', 'Related / Normative Standards', 'Status & Amendments', 'Gap Analysis', 'Certification'];

export default function ResultsPage({ result, onNewSearch, initialQuery }) {
  const primary = result?.recommendations?.[0] ?? null;
  const relatedStandards = result?.related_standards ?? [];
  const gaps = result?.gaps ?? [];
  const certifications = result?.certifications ?? [];

  const productName = primary ? `${primary.title}` : (initialQuery || 'Requirement analysis');
  const standardCode = primary ? primary.number : 'No standard identified';
  const standardName = primary ? primary.title : 'Add more detail to improve ranking';
  const standardRevision = primary?.edition ? `Edition ${primary.edition}` : 'Edition unverified';
  const relevance = relevanceLabel(primary);
  const requirements = primary?.requirements?.length ? primary.requirements : ['No explicit requirements were returned for this item.'];

  return (
    <main className="page-shell results-page" id="results-top">
      <Navbar />
      <div className="results-container">
        <div className="results-toolbar">
          <button className="back-link" type="button" onClick={onNewSearch}><ArrowLeft size={15} /> New Search</button>
          <div className="toolbar-actions">
            <button className="outline-button" type="button"><Download size={15} /> Download Report</button>
            <button className="outline-button" type="button"><Share2 size={15} /> Share</button>
          </div>
        </div>

        <header className="results-heading">
          <h1>Analysis Results</h1>
          <p>Here are the relevant Indian Standards and insights based on your requirement.</p>
        </header>

        <section aria-label="Analysis status" role="status">
          {result?.embedding_mode === 'multilingual' ? <p>Multilingual demo · {result.detected_language} · {result.reranking_applied ? 'Reranked' : 'Semantic retrieval; English reranker skipped'}</p> : null}
          <p>{result?.degraded ? 'Incomplete results — some metadata is unavailable.'
            : result?.match_status === 'NO_RELIABLE_MATCH' ? 'No sufficiently reliable match was identified.'
            : result?.match_status === 'MATCH' ? 'Candidates pass the configured relevance cutoff; validity is unverified.'
            : 'Candidate relevance has not been assessed against a reliability threshold.'}</p>
          {result?.warnings?.length ? <ul>{result.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul> : null}
        </section>

        <section className="product-summary" aria-label="Identified product and extracted requirements">
          <div className="product-identity">
            <div className="product-visual"><HardHat size={65} strokeWidth={1.25} /></div>
            <div>
              <span className="section-kicker">Product Identified</span>
              <h2>{productName}</h2>
              <span className="confidence"><Info size={14} /> {relevance}</span>
              <small>Based on your requirement text</small>
            </div>
          </div>
          <div className="requirements-box">
            <h3><FileCheck2 size={19} /> Extracted Requirements</h3>
            <ul>{requirements.map((requirement) => <li key={requirement}>{requirement}</li>)}</ul>
          </div>
        </section>

        <nav className="results-tabs" aria-label="Analysis result sections">
          {tabs.map((tab, index) => <button className={index === 0 ? 'result-tab active' : 'result-tab'} type="button" key={tab}>{tab}</button>)}
        </nav>

        <section className="standard-panel" aria-labelledby="standard-title">
          <div className="standard-header">
            <div className="standard-icon"><Award size={22} /></div>
            <div className="standard-copy">
              <span className="section-kicker">Primary Recommended Standard</span>
              <h2 id="standard-title">{standardCode}</h2>
              <p>{standardName}<br />({standardRevision})</p>
            </div>
            <div className="standard-actions"><button className="primary-small-button" type="button">View Standard</button><button className="outline-small-button" type="button">View Details</button></div>
          </div>
          <div className="standard-checks">
            <div className="why-standard">
              <h3>Why this standard?</h3>
              {primary?.supporting_evidence?.map((evidence, index) => <p key={index}><Info size={15} /> {evidence}</p>)}
            </div>
            <div className="status-box">
              <h3>Standard Status</h3>
              <p className="status-pill"><CheckCircle2 size={14} /> {primary?.status || 'Status unknown'}</p>
              <p><CheckCircle2 size={15} /> {primary?.edition ? `Edition ${primary.edition}` : 'Edition not available'}</p>
              <a href="#evidence">View amendment history <ArrowRight size={14} /></a>
            </div>
          </div>
        </section>

        <section className="insight-grid" aria-label="Additional analysis insights">
          <article className="insight-card"><span className="insight-icon blue"><Link2 size={21} /></span><div><h3>Related Standards</h3><strong>{relatedStandards.length}</strong><a href="#related">View all <ChevronRight size={13} /></a></div></article>
          <article className="insight-card"><span className="insight-icon amber"><CircleAlert size={21} /></span><div><h3>Potential Gaps</h3><strong>{gaps.length}</strong><a href="#gaps">See details <ChevronRight size={13} /></a></div></article>
          <article className="insight-card"><span className="insight-icon green"><ShieldCheck size={21} /></span><div><h3>Certification</h3><strong>{certifications.length ? certifications.join(', ') : 'Not specified'}</strong><a href="#certification">View info <ChevronRight size={13} /></a></div></article>
        </section>

        <section className="supporting-sections">
          <article id="related"><h2><Link2 size={18} /> Related / Normative Standards</h2>
            {relatedStandards.length ? (
              <ul>{relatedStandards.map((item) => <li key={item.number}>{item.number} — {item.title}</li>)}</ul>
            ) : (
              <p>Connected standards and references that support the recommended specification will be listed here.</p>
            )}
          </article>
          <article id="gaps"><h2><CircleAlert size={18} /> Gap Analysis</h2>
            {gaps.length ? (
              <ul>{gaps.map((item) => <li key={item}>{item}</li>)}</ul>
            ) : (
              <p>Review missing or unclear requirements before finalizing the tender specification.</p>
            )}
          </article>
          <article id="certification"><h2><ShieldCheck size={18} /> Certification</h2>
            {certifications.length ? (
              <ul>{certifications.map((item) => <li key={item}>{item}</li>)}</ul>
            ) : (
              <p>ISI marking and applicable compliance information should be verified for this product.</p>
            )}
          </article>
        </section>

        <section className="evidence-panel" id="evidence"><h2><ExternalLink size={18} /> Evidence &amp; Sources</h2><p>{result?.explanation || 'Recommendation based on the available tender document and BIS standard references.'}</p><a href="#results-top">Open referenced BIS source <ArrowRight size={14} /></a></section>
        <aside className="disclaimer"><Info size={17} /><p><strong>Note:</strong> This is an AI-assisted analysis based on available data. Please verify the standards and requirements from official BIS sources.</p></aside>
      </div>
    </main>
  );
}
