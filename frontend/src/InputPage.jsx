import { useRef, useState } from 'react';
import { AlertCircle, ArrowRight, FileText, Info, Search, UploadCloud } from 'lucide-react';
import AppShell from './components/AppShell';
import './dashboard.css';
import './input.css';

const examples = ['53 grade cement for concrete construction', 'PVC insulated cable rated 1100V', 'Helmets for two-wheeler riders'];

export default function InputPage({ onAnalyze, onNavigate }) {
  const [inputMode, setInputMode] = useState('upload');
  const [selectedExample, setSelectedExample] = useState('');
  const [description, setDescription] = useState('');
  const [fileName, setFileName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (file) setFileName(file.name);
  }

  async function handleAnalyze() {
    const inputText = (description || selectedExample || '').trim();
    if (!inputText) {
      setError('Please enter a product or tender requirement to analyze.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: inputText, limit: 5 }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || 'Unable to analyze the requirement right now.');
      }

      const result = await response.json();
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
  );
}
