import React from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight, Bell, BookOpen, CheckCircle2, ChevronDown, FileText,
  Globe2, LayoutDashboard, Lightbulb, Search, ShieldCheck, Sparkles,
  UploadCloud, X, AlertTriangle,
} from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const demoResult = {
  recommendations: [
    {
      number: "IS 694:2010",
      title: "PVC insulated cables for working voltages up to and including 1100 V",
      edition: "2010",
      status: "Active with amendments",
      score: 0.93,
      matched_terms: ["cable", "pvc", "1100v"],
      certification: "BIS Product Certification (Scheme-I)",
      requirements: ["conductor resistance", "insulation resistance", "voltage test"],
    },
    {
      number: "IS 732:2019",
      title: "Electrical wiring installations - Code of practice",
      edition: "2019",
      status: "Active",
      score: 0.61,
      matched_terms: ["electrical", "installation"],
      requirements: ["earthing", "circuit protection", "inspection and testing"],
    },
  ],
  related_standards: [
    { number: "IS 3043:2018", title: "Code of practice for earthing", edition: "2018", status: "Active" },
    { number: "IS 302 (Part 1):2008", title: "Safety of household and similar electrical appliances", edition: "2008", status: "Active" },
  ],
  certifications: ["BIS Product Certification (Scheme-I)"],
  gaps: ["insulation resistance", "voltage test"],
};

function App() {
  const [description, setDescription] = React.useState("");
  const [result, setResult] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [language, setLanguage] = React.useState("English");

  async function analyze() {
    if (!description.trim()) return;
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });
      if (!response.ok) throw new Error("The analysis service returned an error.");
      setResult(await response.json());
    } catch {
      setResult(demoResult);
      setError("Demo results shown. Start the FastAPI service to receive live recommendations.");
    } finally {
      setLoading(false);
    }
  }

  function loadExample() {
    setDescription("PVC insulated electrical cable for 1100V power and lighting installation");
    setResult(null);
    setError("");
  }

  const shownResult = result || (description ? null : demoResult);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">B</div><div><strong>BIS<span>Intel</span></strong><small>PROCUREMENT INTELLIGENCE</small></div></div>
        <nav>
          <a className="active"><LayoutDashboard size={17} /> Dashboard</a>
          <a><Search size={17} /> Standards Explorer</a>
          <a><FileText size={17} /> Saved Analyses <em>4</em></a>
          <a><BookOpen size={17} /> Knowledge Base</a>
        </nav>
        <div className="sidebar-bottom">
          <div className="help-card"><Sparkles size={18} /><div><b>AI-assisted search</b><span>Recommendations are explainable and traceable to the standards catalog.</span></div></div>
          <div className="profile"><div className="avatar">PS</div><div><b>Priya Sharma</b><span>Procurement Officer</span></div><ChevronDown size={15} /></div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar"><div><div className="eyebrow">MINISTRY OF CONSUMER AFFAIRS</div><h1>Standards Intelligence</h1></div><div className="top-actions"><button className="icon-btn"><Bell size={18} /><i /></button><button className="lang"><Globe2 size={16} /> {language}<ChevronDown size={14} /></button></div></header>
        <section className="hero">
          <div><p className="eyebrow teal">AI-POWERED RECOMMENDATION ENGINE</p><h2>Find the right Indian Standards<br /><span>for every specification.</span></h2><p className="hero-copy">Describe a product, paste technical requirements, or upload a tender document. Get relevant standards, allied references, and certification guidance in seconds.</p></div>
          <div className="hero-art"><div className="orb orb-one" /><div className="orb orb-two" /><div className="art-card"><Sparkles size={18} /><span>Semantic analysis</span><strong>Standards matched</strong><b>98.4%</b></div></div>
        </section>
        <section className="workspace">
          <div className="input-panel panel">
            <div className="panel-heading"><div><span className="step">01</span><div><h3>Describe your requirement</h3><p>Use natural language in English or Hindi</p></div></div><button className="text-button" onClick={loadExample}>Try an example <ArrowRight size={14} /></button></div>
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="e.g. PVC insulated electrical cable suitable for 1100V power distribution..." />
            <div className="input-footer"><button className="upload"><UploadCloud size={17} /> Upload tender document</button><span>{description.length}/5000</span><button className="analyze-btn" onClick={analyze} disabled={!description.trim() || loading}>{loading ? "Analyzing..." : "Analyze requirement"} <ArrowRight size={17} /></button></div>
          </div>
          {error && <div className="notice"><AlertTriangle size={16} /> {error}<button onClick={() => setError("")}><X size={15} /></button></div>}
          {shownResult && <Results result={shownResult} />}
        </section>
      </main>
    </div>
  );
}

function Results({ result }) {
  return <section className="results">
    <div className="results-heading"><div><p className="eyebrow teal">ANALYSIS RESULTS</p><h2>Recommended standards</h2></div><div className="confidence"><CheckCircle2 size={17} /> High confidence <b>{Math.round((result.recommendations?.[0]?.score || 0.93) * 100)}%</b></div></div>
    <div className="result-grid">
      <div className="primary-column">{(result.recommendations || []).map((item, index) => <StandardCard key={item.number} item={item} primary={index === 0} />)}</div>
      <div className="side-column">
        <div className="panel compact"><div className="card-title"><div className="icon-box green"><ShieldCheck size={18} /></div><div><h3>Certification guidance</h3><p>Applicable requirements</p></div></div>{(result.certifications || []).map((cert) => <div className="cert" key={cert}><CheckCircle2 size={15} />{cert}</div>)}<a>View certification details <ArrowRight size={14} /></a></div>
        <div className="panel compact"><div className="card-title"><div className="icon-box amber"><Lightbulb size={18} /></div><div><h3>Specification gaps</h3><p>Consider adding to your tender</p></div></div>{(result.gaps || []).map((gap) => <div className="gap" key={gap}><span />{gap}</div>)}{!result.gaps?.length && <p className="muted">No obvious gaps detected.</p>}</div>
      </div>
    </div>
    <div className="panel related"><div className="related-head"><div><h3>Allied &amp; normative standards</h3><p>References connected to your primary recommendation</p></div><button className="text-button">View all <ArrowRight size={14} /></button></div><div className="related-list">{(result.related_standards || []).map((item) => <div className="related-item" key={item.number}><div className="related-icon"><BookOpen size={16} /></div><div><b>{item.number}</b><span>{item.title}</span></div><small>{item.edition}</small><ArrowRight size={16} /></div>)}</div></div>
  </section>;
}

function StandardCard({ item, primary }) {
  return <article className={`standard-card ${primary ? "primary" : ""}`}><div className="standard-top"><div className="standard-number">{item.number}{primary && <span>BEST MATCH</span>}</div><div className="score"><div className="score-ring" style={{ "--score": `${Math.round(item.score * 100)}%` }}><b>{Math.round(item.score * 100)}</b></div><small>match</small></div></div><h3>{item.title}</h3><div className="meta"><span className="status-dot" /> {item.status} <span className="divider" /> Edition: {item.edition}</div><div className="matched">{(item.matched_terms || []).map((term) => <span key={term}>{term}</span>)}</div><button className="details">Explore standard <ArrowRight size={15} /></button></article>;
}

createRoot(document.getElementById("root")).render(<App />);
