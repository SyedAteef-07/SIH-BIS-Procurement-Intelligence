import { useState } from 'react';
import InputPage from './InputPage';
import ResultsPage from './ResultsPage';

export default function App() {
  const [analysis, setAnalysis] = useState(null);
  const [query, setQuery] = useState('');
  function reset() { setAnalysis(null); setQuery(''); window.scrollTo(0, 0); }
  return analysis
    ? <ResultsPage result={analysis} initialQuery={query} onNewSearch={reset} />
    : <InputPage onAnalyze={(text, result) => { setQuery(text); setAnalysis(result); window.scrollTo(0, 0); }} />;
}
