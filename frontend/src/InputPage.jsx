import { useRef, useState } from 'react';
import { AlertCircle, ArrowRight, FileText, Info, Search, UploadCloud } from 'lucide-react';
import AppShell from './components/AppShell';
import { analyzePdf, analyzeRequirement } from './api';
import './dashboard.css';
import './input.css';

const examples = [
  '11 kV/433 V three phase oil immersed distribution transformer for outdoor installation',
  'PVC insulated cable rated 1100 V',
  '53 grade cement for concrete construction',
];

export default function InputPage({ onAnalyze, onNavigate }) {
  const [inputMode, setInputMode] = useState('text');
  const [description, setDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [embeddingMode, setEmbeddingMode] = useState('english');
  const fileInputRef = useRef(null);

  function chooseFile(file) {
    if (!file) return;
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setSelectedFile(null);
      setError('Please choose a PDF file.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setSelectedFile(null);
      setError('File is too large. Maximum size is 10 MB.');
      return;
    }
    setSelectedFile(file);
    setError('');
  }

  function handleDrop(event) {
    event.preventDefault();
    chooseFile(event.dataTransfer?.files?.[0]);
  }

  async function handleAnalyze() {
    setError('');
    setIsLoading(true);
    try {
      if (inputMode === 'upload') {
        if (!selectedFile) {
          setError('Please upload a tender PDF first.');
          return;
        }
        const result = await analyzePdf(selectedFile, fetch, embeddingMode);
        onAnalyze?.(selectedFile.name, result);
        return;
      }

      const text = description.trim();
      if (!text) {
        setError('Please enter a product or tender requirement to analyze.');
        return;
      }
      const result = await analyzeRequirement(text, fetch, embeddingMode);
      onAnalyze?.(text, result);
    } catch (fetchError) {
      setError(fetchError.message || 'Could not connect to the analysis service.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AppShell activePage="analyze" currentPage="Analyze Tender" onNavigate={onNavigate}>
      <main className="input-workspace" aria-labelledby="input-page-title">
        <header className="input-page-header">
          <h1 id="input-page-title">Analyze Tender</h1>
          <p>Upload a tender PDF or enter a procurement requirement to identify relevant standards.</p>
        </header>

        <section className="tender-input-card" aria-labelledby="input-card-title">
          <h2 id="input-card-title" className="sr-only">Tender requirement input</h2>

          <div className="input-method-tabs" role="tablist" aria-label="Requirement input type">
            <button
              className={inputMode === 'upload' ? 'input-method-tab is-active' : 'input-method-tab'}
              type="button"
              role="tab"
              aria-selected={inputMode === 'upload'}
              onClick={() => { setInputMode('upload'); setError(''); }}
            >
              <UploadCloud size={17} /> Upload Tender PDF
            </button>
            <button
              className={inputMode === 'text' ? 'input-method-tab is-active' : 'input-method-tab'}
              type="button"
              role="tab"
              aria-selected={inputMode === 'text'}
              onClick={() => { setInputMode('text'); setError(''); }}
            >
              <FileText size={17} /> Enter Requirement
            </button>
          </div>

          {inputMode === 'upload' ? (
            <div
              className="input-upload-zone"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(event) => event.preventDefault()}
              onDrop={handleDrop}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => event.key === 'Enter' && fileInputRef.current?.click()}
            >
              <UploadCloud className="upload-icon" size={34} />
              <strong>{selectedFile?.name || 'Drag and drop your PDF here'}</strong>
              <span>or</span>
              <button
                className="input-file-button"
                type="button"
                onClick={(event) => { event.stopPropagation(); fileInputRef.current?.click(); }}
              >
                <FileText size={16} /> Choose File
              </button>
              <small>Text-based PDF, maximum 10 MB. Scanned PDFs require OCR and are not supported yet.</small>
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf,.pdf"
                onChange={(event) => chooseFile(event.target.files?.[0])}
                hidden
              />
            </div>
          ) : (
            <div className="input-text-field">
              <label htmlFor="requirement-description">Tender requirement</label>
              <textarea
                id="requirement-description"
                value={description}
                onChange={(event) => { setDescription(event.target.value); if (error) setError(''); }}
                placeholder="Example: 11 kV/433 V three phase oil immersed distribution transformer for outdoor installation"
                rows={6}
                maxLength={2000}
              />
              <small>{description.length}/2000 characters</small>
            </div>
          )}

          <label className="input-hint">
            Language mode:{' '}
            <select
              value={embeddingMode}
              onChange={(event) => setEmbeddingMode(event.target.value)}
              disabled={isLoading}
            >
              <option value="english">English</option>
              <option value="multilingual">Multilingual demo</option>
            </select>
          </label>

          <div className="input-card-footer">
            <p className="input-hint">Specific product, rating, material, installation and safety details improve retrieval.</p>
            <button className="input-analyze-button" type="button" onClick={handleAnalyze} disabled={isLoading}>
              <Search size={17} />
              {isLoading ? 'Analyzing...' : 'Analyze Requirement'}
              {!isLoading && <ArrowRight size={16} />}
            </button>
          </div>
        </section>

        <section className="input-examples" aria-labelledby="examples-title">
          <div>
            <h2 id="examples-title">Example requirements</h2>
            <p>Select one to populate the text input.</p>
          </div>
          <div className="input-example-list">
            {examples.map((example) => (
              <button
                className="input-example-chip"
                type="button"
                key={example}
                onClick={() => { setInputMode('text'); setDescription(example); setError(''); }}
              >
                {example}
              </button>
            ))}
          </div>
        </section>

        {error ? (
          <div className="input-error" role="alert">
            <AlertCircle size={17} /><span>{error}</span>
          </div>
        ) : null}

        <p className="input-page-note">
          <Info size={16} /> Frontend calls the orchestration backend only; AI and database access remain server-side.
        </p>
      </main>
    </AppShell>
  );
}
