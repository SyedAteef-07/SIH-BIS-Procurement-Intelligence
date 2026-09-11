import { useRef, useState } from 'react';
import { AlertCircle, ArrowRight, FileText, Search, Share2, ShieldCheck, Sparkles, UploadCloud, LoaderCircle, X } from 'lucide-react';
import BrandHeader from './components/BrandHeader';
import { analyzePdf, analyzeRequirement } from './api';
import './input.css';

const examples = ['53 grade cement for concrete construction', '33 kV XLPE power cable', '11 kV three phase distribution transformer'];
export default function InputPage({ onAnalyze }) {
  const [inputMode, setInputMode] = useState('upload');
  const [description, setDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [embeddingMode, setEmbeddingMode] = useState('english');
  const [isLoading, setIsLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  function chooseFile(file) {
    if (!file || isLoading) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) { setSelectedFile(null); setError('Please choose a PDF file.'); return; }
    if (file.size > 10 * 1024 * 1024) { setSelectedFile(null); setError('File is too large. Maximum size is 10 MB.'); return; }
    if (!file.size) { setSelectedFile(null); setError('This file is empty. Please choose a readable PDF.'); return; }
    setSelectedFile(file); setError('');
  }
  async function handleAnalyze(event) {
    event.preventDefault();
    if (isLoading) return;
    if (inputMode === 'upload' && !selectedFile) { setError('Please upload a tender PDF first.'); return; }
    if (inputMode === 'text' && !description.trim()) { setError('Please enter a product or tender requirement to analyze.'); return; }
    setIsLoading(true); setError('');
    try {
      const result = inputMode === 'upload' ? await analyzePdf(selectedFile, fetch, embeddingMode) : await analyzeRequirement(description.trim(), fetch, embeddingMode);
      onAnalyze(inputMode === 'upload' ? selectedFile.name : description.trim(), result);
    } catch (err) { setError(err.message || 'Could not connect to the analysis service.'); }
    finally { setIsLoading(false); }
  }
  return <div className="page-shell"><BrandHeader /><main className="input-main">
    <header className="hero"><div className="eyebrow"><Sparkles size={15} /> PROCUREMENT, WITH CLARITY</div>
      <h1>Find the Right Indian Standards<br /><span>for Your Procurement</span></h1>
      <p>Upload a tender document or describe your requirement, and get<br className="desktop-break" /> AI-powered, standards-backed recommendations.</p>
    </header>
    <form onSubmit={handleAnalyze} aria-busy={isLoading}>
      <section className="input-card">
        <div className="input-tabs" role="tablist" aria-label="Requirement input type">
          {[['upload', 'Upload Tender Document', UploadCloud], ['text', 'Enter Requirement (Text)', FileText]].map(([id, label, Icon]) =>
            <button key={id} id={'input-tab-' + id} type="button" role="tab" aria-selected={inputMode === id} aria-controls="input-panel" disabled={isLoading} className={inputMode === id ? 'active' : ''} onClick={() => { setInputMode(id); setError(''); }}><Icon size={18} />{label}</button>)}
        </div>
        <div id="input-panel" role="tabpanel" aria-labelledby={'input-tab-' + inputMode}>
          {inputMode === 'upload' ? <div className={'drop-zone' + (dragging ? ' dragging' : '')}
            onDragOver={e => { e.preventDefault(); if (!isLoading) setDragging(true); }} onDragLeave={() => setDragging(false)}
            onDrop={e => { e.preventDefault(); setDragging(false); chooseFile(e.dataTransfer.files[0]); }}>
            <div className="upload-emblem"><UploadCloud size={39} strokeWidth={1.5} /></div>
            <strong>{selectedFile?.name || 'Drag and drop your PDF here'}</strong><span>or</span>
            <button type="button" className="choose-file" disabled={isLoading} onClick={() => fileInputRef.current?.click()}><FileText size={16} /> Choose File</button>
            <small>Supports PDF · Max 10 MB</small>
            <input aria-label="Choose tender PDF" ref={fileInputRef} type="file" accept=".pdf,application/pdf" hidden disabled={isLoading} onChange={e => { chooseFile(e.target.files[0]); e.target.value = ''; }} />
            {selectedFile && <button className="text-button" type="button" disabled={isLoading} onClick={() => setSelectedFile(null)}><X size={14} /> Remove file</button>}
          </div> : <div className="text-input"><label htmlFor="description">Your procurement requirement</label><textarea id="description" value={description} disabled={isLoading} onChange={e => { setDescription(e.target.value); setError(''); }} rows={7} maxLength={2000} placeholder="Describe the product, material, rating and intended use…" /><small>{description.length} / 2,000 characters</small></div>}
        </div>
        <div className="input-options"><label>Language mode <select value={embeddingMode} disabled={isLoading} onChange={e => setEmbeddingMode(e.target.value)}><option value="english">English</option><option value="multilingual">Multilingual demo</option></select></label><small>Text-based PDFs only. Scanned documents require OCR.</small></div>
      </section>
      <div className="examples"><strong>Try an example:</strong><div>{examples.map(example => <button key={example} type="button" disabled={isLoading} onClick={() => { setInputMode('text'); setDescription(example); setError(''); }}>{example}</button>)}</div></div>
      {error && <p className="error-notice" role="alert"><AlertCircle size={18} />{error}</p>}
      <button className="analyze-button" disabled={isLoading} type="submit">{isLoading ? <LoaderCircle className="spin" size={19} /> : <Search size={19} />}{isLoading ? 'Analyzing…' : 'Analyze Requirement'}{!isLoading && <ArrowRight size={17} />}</button>
    </form>
    <section className="feature-grid" aria-label="Product features">
      {[[Search, 'AI-Powered Search', 'Find relevant standards for your requirements.'], [Share2, 'Connected Knowledge', 'Explore supporting references when available.'], [ShieldCheck, 'Compliant Procurement', 'Support informed decisions with evidence.']].map(([Icon, title, description]) => <article key={title}><div className="feature-icon"><Icon size={24} /></div><div><h2>{title}</h2><p>{description}</p></div></article>)}
    </section>
    <footer>Supporting informed procurement. All demo standards require verification.</footer>
  </main></div>;
}
