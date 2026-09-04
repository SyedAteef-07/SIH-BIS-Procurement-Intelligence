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

const temporaryResult = {
  product: 'Industrial Safety Helmets',
  confidence: 'High Confidence',
  requirements: ['Impact resistance', 'Penetration resistance', 'For construction workers'],
  standardCode: 'IS 2925 : 1984',
  standardName: 'Specification for Industrial Safety Helmets',
  revision: 'Second Revision',
  relatedCount: 3,
  gapCount: 3,
  certification: 'ISI Marking Required',
};

const tabs = ['Recommended Standard', 'Related / Normative Standards', 'Status & Amendments', 'Gap Analysis', 'Certification'];

export default function ResultsPage() {
  return (
    <main className="page-shell results-page" id="results-top">
      <Navbar />
      <div className="results-container">
        <div className="results-toolbar">
          <a className="back-link" href="#top"><ArrowLeft size={15} /> New Search</a>
          <div className="toolbar-actions">
            <button className="outline-button" type="button"><Download size={15} /> Download Report</button>
            <button className="outline-button" type="button"><Share2 size={15} /> Share</button>
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
              <h2>{temporaryResult.product}</h2>
              <span className="confidence"><CheckCircle2 size={14} /> {temporaryResult.confidence}</span>
              <small>Based on your tender document</small>
            </div>
          </div>
          <div className="requirements-box">
            <h3><FileCheck2 size={19} /> Extracted Requirements</h3>
            <ul>{temporaryResult.requirements.map((requirement) => <li key={requirement}>{requirement}</li>)}</ul>
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
              <h2 id="standard-title">{temporaryResult.standardCode}</h2>
              <p>{temporaryResult.standardName}<br />({temporaryResult.revision})</p>
            </div>
            <div className="standard-actions"><button className="primary-small-button" type="button">View Standard</button><button className="outline-small-button" type="button">View Details</button></div>
          </div>
          <div className="standard-checks">
            <div className="why-standard"><h3>Why this standard?</h3><p><CheckCircle2 size={15} /> Product match</p><p><CheckCircle2 size={15} /> Scope match</p><p><CheckCircle2 size={15} /> Relevant to identified requirements</p></div>
            <div className="status-box"><h3>Standard Status</h3><p className="status-pill"><CheckCircle2 size={14} /> Current</p><p><CheckCircle2 size={15} /> Reaffirmed in 2019</p><a href="#evidence">View amendment history <ArrowRight size={14} /></a></div>
          </div>
        </section>

        <section className="insight-grid" aria-label="Additional analysis insights">
          <article className="insight-card"><span className="insight-icon blue"><Link2 size={21} /></span><div><h3>Related Standards</h3><strong>{temporaryResult.relatedCount}</strong><a href="#related">View all <ChevronRight size={13} /></a></div></article>
          <article className="insight-card"><span className="insight-icon amber"><CircleAlert size={21} /></span><div><h3>Potential Gaps</h3><strong>{temporaryResult.gapCount}</strong><a href="#gaps">See details <ChevronRight size={13} /></a></div></article>
          <article className="insight-card"><span className="insight-icon green"><ShieldCheck size={21} /></span><div><h3>Certification</h3><strong>{temporaryResult.certification}</strong><a href="#certification">View info <ChevronRight size={13} /></a></div></article>
        </section>

        <section className="supporting-sections">
          <article id="related"><h2><Link2 size={18} /> Related / Normative Standards</h2><p>Connected standards and references that support the recommended specification will be listed here.</p></article>
          <article id="gaps"><h2><CircleAlert size={18} /> Gap Analysis</h2><p>Review missing or unclear requirements before finalizing the tender specification.</p></article>
          <article id="certification"><h2><ShieldCheck size={18} /> Certification</h2><p>ISI marking and applicable compliance information should be verified for this product.</p></article>
        </section>

        <section className="evidence-panel" id="evidence"><h2><ExternalLink size={18} /> Evidence &amp; Sources</h2><p>Recommendation based on the available tender document and BIS standard references.</p><a href="#results-top">Open referenced BIS source <ArrowRight size={14} /></a></section>
        <aside className="disclaimer"><Info size={17} /><p><strong>Note:</strong> This is an AI-assisted analysis based on available data. Please verify the standards and requirements from official BIS sources.</p></aside>
      </div>
    </main>
  );
}
