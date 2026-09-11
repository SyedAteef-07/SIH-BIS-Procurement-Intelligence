import { useRef, useState } from 'react';
import { AlertCircle, ArrowRight, FileText, Info, Search, UploadCloud } from 'lucide-react';
import AppShell from './components/AppShell';
import './dashboard.css';
import './input.css';
import { ArrowUp, Check, FileText, Search, Share2, ShieldCheck, Sparkles, UploadCloud } from 'lucide-react';
import Navbar from './components/Navbar';
import { analyzeRequirement } from './api';

const examples = ['53 grade cement for concrete construction', 'PVC insulated cable rated 1100V', 'Helmets for two-wheeler riders'];

export default function InputPage({ onAnalyze, onNavigate }) {
  const [inputMode, setInputMode] = useState('upload');
export default function InputPage({ onAnalyze }) {
  const [activeTab, setActiveTab] = useState(0); // 0 = Upload, 1 = Text
  const [selectedExample, setSelectedExample] = useState('');
  const [description, setDescription] = useState('');
  const [fileName, setFileName] = useState('');
  const [fileContent, setFileContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [embeddingMode, setEmbeddingMode] = useState('english');
  const fileInputRef = useRef(null);
  const dropZoneRef = useRef(null);

  function handleTabClick(tabIndex) {
    setActiveTab(tabIndex);
    setError('');
  }

  function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      setError('File is too large. Maximum size is 10 MB.');
      return;
    }
    setFileName(file.name);
    setError('');
    // For MVP: read text from the file name as placeholder content
    // In production this would use a PDF parser
    const reader = new FileReader();
    reader.onload = () => {
      const text = reader.result;
      if (typeof text === 'string') {
        setFileContent(text.substring(0, 5000));
      }
    };
    reader.onerror = () => {
      setError('Could not read the file.');
    };
    // Try reading as text; for PDFs this won't produce useful text
    // but demonstrates the flow
    reader.readAsText(file);
  }

  function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    if (dropZoneRef.current) dropZoneRef.current.style.borderColor = '#0564d7';
  }

  function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    if (dropZoneRef.current) dropZoneRef.current.style.borderColor = '#adc8e7';
  }

  function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    if (dropZoneRef.current) dropZoneRef.current.style.borderColor = '#adc8e7';
    const file = event.dataTransfer?.files?.[0];
    if (file) {
      // Simulate a file input change
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      if (fileInputRef.current) {
        fileInputRef.current.files = dataTransfer.files;
        handleFileChange({ target: fileInputRef.current });
      }
    }
  }

  async function handleAnalyze() {
    // Determine the input text based on active tab
    let inputText = '';
    if (activeTab === 0) {
      // Upload tab — use file content or file name as fallback
      inputText = fileContent || fileName || '';
      if (!inputText.trim()) {
        setError('Please upload a tender document first.');
        return;
      }
    } else {
      // Text tab
      inputText = (description || selectedExample || '').trim();
      if (!inputText) {
        setError('Please enter a product or tender requirement to analyze.');
        return;
      }
    }

    setIsLoading(true);
    setError('');

    try {
      const result = await analyzeRequirement(inputText, fetch, embeddingMode);
      onAnalyze?.(inputText, result);
    } catch (fetchError) {
      setError(fetchError.message || 'Something went wrong while connecting to the analysis service.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AppShell activePage="analyze" currentPage="Analyze Tender" onNavigate={onNavigate}>
      <main className="input-workspace" aria-labelledby="input-page-title">
        <header className="input-page-header"><h1 id="input-page-title">Analyze Tender</h1><p>Upload a tender document or enter a procurement requirement to identify relevant BIS standards and compliance requirements.</p></header>
        <section className="tender-input-card" aria-labelledby="input-card-title">
          <h2 id="input-card-title" className="sr-only">Tender requirement input</h2>
          <div className="input-method-tabs" role="tablist" aria-label="Requirement input type">
            <button className={inputMode === 'upload' ? 'input-method-tab is-active' : 'input-method-tab'} type="button" role="tab" aria-selected={inputMode === 'upload'} onClick={() => setInputMode('upload')}><UploadCloud size={17} />Upload Tender Document</button>
            <button className={inputMode === 'text' ? 'input-method-tab is-active' : 'input-method-tab'} type="button" role="tab" aria-selected={inputMode === 'text'} onClick={() => setInputMode('text')}><FileText size={17} />Enter Requirement (Text)</button>
          </div>
          {inputMode === 'upload' ? <div className="input-upload-zone" onClick={() => fileInputRef.current?.click()} role="button" tabIndex={0} onKeyDown={(event) => event.key === 'Enter' && fileInputRef.current?.click()}>
            <UploadCloud className="upload-icon" size={34} />
            <strong>{fileName || 'Drag and drop your PDF here'}</strong><span>or</span>
            <button className="input-file-button" type="button" onClick={(event) => { event.stopPropagation(); fileInputRef.current?.click(); }}><FileText size={16} />Choose File</button>
            <small>Supports PDF files up to 10 MB</small><input ref={fileInputRef} type="file" accept="application/pdf" onChange={handleFileChange} hidden />
          </div> : null}
          <div className="input-text-field"><label htmlFor="requirement-description">{inputMode === 'upload' ? 'Requirement details' : 'Tender requirement'}</label><textarea id="requirement-description" value={description} onChange={(event) => { setDescription(event.target.value); if (error) setError(''); }} placeholder="Describe the requirement or paste tender text..." rows={6} /></div>
          <div className="input-card-footer"><p className="input-hint">Provide specific product, service, or tender details for a more relevant standards match.</p><button className="input-analyze-button" type="button" onClick={handleAnalyze} disabled={isLoading}><Search size={17} />{isLoading ? 'Analyzing...' : 'Analyze Requirement'}<ArrowRight size={16} /></button></div>
        </section>
        <section className="input-examples" aria-labelledby="examples-title"><div><h2 id="examples-title">Example requirements</h2><p>Select an example to populate the tender requirement.</p></div><div className="input-example-list">{examples.map((example) => <button className={selectedExample === example ? 'input-example-chip is-selected' : 'input-example-chip'} type="button" key={example} onClick={() => { setSelectedExample(example); setDescription(example); setError(''); setInputMode('text'); }}>{example}</button>)}</div></section>
        {error ? <div className="input-error" role="alert"><AlertCircle size={17} /><span>{error}</span></div> : null}
        <p className="input-page-note"><Info size={16} /> Analysis uses the connected BIS standards intelligence service.</p>
      </main>
    </AppShell>
          <textarea
            className="requirement-textarea"
            aria-label="Tender requirement or product description"
            value={description}
            onChange={(event) => {
              setDescription(event.target.value);
              if (error) setError('');
            }}
            placeholder="Describe the requirement or paste tender text..."
            rows={5}
            maxLength={2000}
          />
          <label style={{ display: 'block', padding: '12px' }}>
            Language mode: {' '}
            <select value={embeddingMode} onChange={(event) => setEmbeddingMode(event.target.value)} disabled={isLoading}>
              <option value="english">English</option>
              <option value="multilingual">Multilingual (English / Hindi / Kannada demo)</option>
            </select>
          </label>
    <main id="top" className="page-shell">
      <Navbar />
      <section className="hero" aria-labelledby="hero-title">
        <div className="eyebrow"><Sparkles size={14} /> PROCURE SMARTER. COMPLY EASIER.</div>
        <h1 id="hero-title">Find the Right Indian Standards<br /><span>for Your Procurement</span></h1>
        <p>Upload a tender document or describe your requirement, and get<br className="desktop-break" /> AI-powered, standards-backed recommendations.</p>

        <div className="input-panel">
          <div className="input-tabs" role="tablist" aria-label="Requirement input type">
            <button
              className={activeTab === 0 ? 'input-tab active' : 'input-tab'}
              type="button"
              role="tab"
              aria-selected={activeTab === 0}
              onClick={() => handleTabClick(0)}
            >
              <UploadCloud size={18} />Upload Tender Document
            </button>
            <button
              className={activeTab === 1 ? 'input-tab active' : 'input-tab'}
              type="button"
              role="tab"
              aria-selected={activeTab === 1}
              onClick={() => handleTabClick(1)}
            >
              <FileText size={18} />Enter Requirement (Text)
            </button>
          </div>

          {activeTab === 0 && (
            <div
              ref={dropZoneRef}
              className="drop-zone"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => event.key === 'Enter' && fileInputRef.current?.click()}
            >
              <UploadCloud className="upload-icon" size={38} strokeWidth={1.8} />
              <strong>{fileName || 'Drag and drop your PDF here'}</strong>
              <span>or</span>
              <button className="choose-file" type="button" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}>
                <FileText size={16} />Choose File
              </button>
              <small>Supports PDF (Max 10 MB)</small>
              <input ref={fileInputRef} type="file" accept="application/pdf,.txt,.doc,.docx" onChange={handleFileChange} hidden />
            </div>
          )}

          {activeTab === 1 && (
            <textarea
              className="requirement-textarea"
              aria-label="Tender requirement or product description"
              value={description}
              onChange={(event) => {
                setDescription(event.target.value);
                if (error) setError('');
              }}
              placeholder="Describe the requirement or paste tender text..."
              rows={5}
              style={{
                width: '100%',
                minHeight: '180px',
                padding: '16px',
                margin: '16px 0',
                border: '1px solid #adc8e7',
                borderRadius: '6px',
                background: 'rgba(250, 253, 255, .7)',
                color: '#182d62',
                fontSize: '15px',
                fontFamily: 'inherit',
                resize: 'vertical',
                outline: 'none',
              }}
              onFocus={(e) => { e.target.style.borderColor = '#0564d7'; e.target.style.boxShadow = '0 0 0 3px rgba(5,100,215,0.1)'; }}
              onBlur={(e) => { e.target.style.borderColor = '#adc8e7'; e.target.style.boxShadow = 'none'; }}
            />
          )}
        </div>

        <div className="examples-row">
          <strong>Try an example:</strong>
          <div className="example-buttons">
            {examples.map((example) => (
              <button
                className={selectedExample === example ? 'example-button selected' : 'example-button'}
                type="button"
                key={example}
                onClick={() => {
                  setSelectedExample(example);
                  setDescription(example);
                  setActiveTab(1); // Switch to text tab when example is clicked
                  setError('');
                }}
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        {error ? <div className="analysis-error" style={{ marginTop: '16px', padding: '12px 18px', background: '#fff0f0', border: '1px solid #f5c6cb', borderRadius: '8px', color: '#a94442', fontSize: '14px', maxWidth: '790px', margin: '16px auto 0' }}>{error}</div> : null}

        <button className="analyze-button" type="button" onClick={handleAnalyze} disabled={isLoading}>
          <Search size={18} />
          {isLoading ? 'Analyzing...' : 'Analyze Requirement'}
          {!isLoading && <ArrowUp size={16} />}
        </button>
      </section>

      <section className="feature-grid" aria-label="Product features">
        <article className="feature-card"><span className="feature-icon blue"><Search size={23} /></span><div><h2>AI-Powered Search</h2><p>Finds the most relevant<br />Indian Standards</p></div></article>
        <article className="feature-card"><span className="feature-icon sky"><Share2 size={23} /></span><div><h2>Connected Knowledge</h2><p>Discovers related and<br />normative standards</p></div></article>
        <article className="feature-card"><span className="feature-icon green"><ShieldCheck size={23} /></span><div><h2>Compliant Procurement</h2><p>Helps you create complete<br />and up-to-date specifications</p></div></article>
      </section>

      <div className="monument-illustration" aria-hidden="true">
        <svg viewBox="0 0 1200 150" preserveAspectRatio="none">
          <g fill="none" stroke="currentColor" strokeWidth="1.25" strokeLinejoin="round">
            <path d="M0 137h1200M10 137v-20h32v20m-28-20v-18h24v18m-18-18v-8h12v8m-22 46v-20m20 20v-20M70 137v-12h46v12m-40-12v-27h34v27m-27-27v-8h20v8m-14-8v-9h8v9m-27 56v-24m38 24v-24" />
            <path d="M174 137v-35h62v35m-54-35v-10h46v10m-38-10 15-18 15 18m-9-18v-16h-12v16m-5 66v-27m22 27v-27M287 137v-44h76v44m-67-44v-12h58v12m-49-12 15-22 15 22m-7-22v-18h-12v18m-2 78v-33m21 33v-33" />
            <path d="M433 137v-30h42v30m-37-30v-12h32v12m-22-12 8-17 8 17m-4-17v-11h-8v11m-5 59v-18m18 18v-18M542 137v-21h52v21m-45-21v-15h38v15m-31-15 15-19 15 19m-10-19v-14h-10v14m-4 55v-17m22 17v-17" />
            <path d="M700 137v-43h80v43m-69-43v-13h58v13m-50-13 18-24 18 24m-11-24v-18h-14v18m-3 78v-32m25 32v-32M842 137v-25h52v25m-44-25v-14h36v14m-29-14 15-18 15 18m-10-18v-14h-10v14m-4 57v-17m22 17v-17" />
            <path d="M976 137v-37h63v37m-55-37v-11h47v11m-39-11 15-21 15 21m-9-21v-16h-12v16m-3 69v-27m22 27v-27M1098 137v-17h48v17m-41-17v-14h34v14m-28-14 14-17 14 17m-9-17v-12h-10v12" />
          </g>
        </svg>
      </div>

      <footer className="footer"><span className="footer-line" /> <Check size={13} /> Building Compliant Procurement for a Safer India <span className="footer-line" /></footer>
    </main>
  );
}
