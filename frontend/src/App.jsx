import { useState } from 'react';
import BISStandardsPage from './BISStandardsPage';
import DashboardPage from './DashboardPage';
import InputPage from './InputPage';
import ResultsPage from './ResultsPage';
import ReportsPage from './ReportsPage';
import AnalyticsPage from './AnalyticsPage';
import SettingsPage from './SettingsPage';

export default function App() {
  const [page, setPage] = useState('dashboard');
  const [analysis, setAnalysis] = useState(null);
  const [query, setQuery] = useState('');
  const navigate = (nextPage) => setPage(nextPage === 'analyze' ? 'input' : nextPage);

  if (analysis) {
    return <ResultsPage result={analysis} onNavigate={navigate} onNewSearch={() => { setAnalysis(null); setQuery(''); setPage('input'); }} initialQuery={query} />;
  }

  if (page === 'input') {
    return <InputPage onNavigate={navigate} onAnalyze={(description, result) => { setQuery(description); setAnalysis(result); }} />;
  }

  if (page === 'standards') {
    return <BISStandardsPage onNavigate={navigate} />;
  }

  if (page === 'reports') {
    return <ReportsPage onNavigate={navigate} />;
  }

  if (page === 'analytics') {
    return <AnalyticsPage onNavigate={navigate} />;
  }

  if (page === 'settings') {
    return <SettingsPage onNavigate={navigate} />;
  }

  return <DashboardPage onNavigate={navigate} />;
}
