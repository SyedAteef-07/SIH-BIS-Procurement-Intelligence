import { useState } from 'react';
import InputPage from './InputPage';
import ResultsPage from './ResultsPage';

export default function App() {
  const [analysis, setAnalysis] = useState(null);
  const [query, setQuery] = useState('');

  if (analysis) {
    return <ResultsPage result={analysis} onNewSearch={() => { setAnalysis(null); setQuery(''); }} initialQuery={query} />;
  }

  return <InputPage onAnalyze={(description, result) => { setQuery(description); setAnalysis(result); }} />;
}
