import { useMemo, useState } from 'react';
import { Download, FileText, Search, Share2, SlidersHorizontal } from 'lucide-react';
import AppShell from './components/AppShell';
import StatCard from './components/StatCard';
import StatusBadge from './components/StatusBadge';
import './operations.css';

const reportStats = [
  { label: 'Total Reports', value: '186', trend: 'All generated reports', icon: FileText },
  { label: 'Generated This Month', value: '24', trend: '+6 vs last month', icon: FileText },
  { label: 'Pending Review', value: '8', trend: 'Requires attention', icon: FileText },
  { label: 'Shared Reports', value: '42', trend: 'Across departments', icon: Share2 },
];

const reportRecords = [
  { id: 'RPT-2026-1042', requirement: 'National Highway Surveillance Integration', department: 'Ministry of Road Transport', status: 'Completed', date: '24 Oct 2026', score: '92%' },
  { id: 'RPT-2026-1038', requirement: 'Secure Cloud Migration Services', department: 'Federal Source of Digital Communications', status: 'Under Review', date: '21 Oct 2026', score: '87%' },
  { id: 'RPT-2026-1031', requirement: 'Smart Energy Grid Transformer', department: 'Ministry of Power', status: 'Completed', date: '21 Oct 2026', score: '91%' },
  { id: 'RPT-2026-1024', requirement: 'Tactical Radio Equipment', department: 'Department of Defense Procurement Liaison', status: 'Draft', date: '20 Oct 2026', score: '78%' },
];

export default function ReportsPage({ onNavigate }) {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('All');
  const [notice, setNotice] = useState('');
  const filteredReports = useMemo(() => reportRecords.filter((report) => (!query || `${report.id} ${report.requirement} ${report.department}`.toLowerCase().includes(query.toLowerCase())) && (status === 'All' || report.status === status)), [query, status]);

  function showUnavailable(action, reportId) {
    setNotice(`${action} is not connected to a backend operation yet (${reportId}).`);
  }

  return <AppShell activePage="reports" currentPage="Analysis Reports" onNavigate={onNavigate}>
    <main className="operations-workspace" aria-labelledby="reports-title">
      <header className="operations-header"><div><span className="operations-kicker">REPORT MANAGEMENT</span><h1 id="reports-title">Analysis Reports</h1><p>Review, manage, download, and share procurement intelligence reports generated from tender analysis.</p></div><button className="operations-primary-button" type="button" onClick={() => setNotice('Report generation is available from an analyzed tender result.') }><FileText size={16} /> Generate Analysis Report</button></header>
      <section className="operations-stats">{reportStats.map((stat) => <StatCard key={stat.label} {...stat} />)}</section>
      <section className="operations-filter-card" aria-label="Report filters"><div className="operations-filter-heading"><div><h2>Find a report</h2><p>Search generated procurement intelligence reports.</p></div><SlidersHorizontal size={18} /></div><div className="operations-filter-row"><label className="operations-search"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by report ID, tender ID, requirement, department" aria-label="Search reports" /></label><label>Status<select value={status} onChange={(event) => setStatus(event.target.value)}><option>All</option><option>Completed</option><option>Under Review</option><option>Draft</option><option>Archived</option></select></label><label>Department<select><option>All departments</option><option>Ministry of Power</option><option>Ministry of Road Transport</option></select></label><label>Date Range<select><option>All dates</option><option>Last 30 days</option><option>Last 90 days</option></select></label><label>Report Type<select><option>All types</option><option>Compliance report</option><option>Standards report</option></select></label><button className="operations-clear-button" type="button" onClick={() => { setQuery(''); setStatus('All'); }}>Clear Filters</button><button className="operations-search-button" type="button">Search</button></div></section>
      <section className="operations-table-card" aria-labelledby="report-table-title"><div className="operations-table-heading"><div><span className="operations-kicker">REPORT LIBRARY</span><h2 id="report-table-title">Generated Reports</h2><p>{filteredReports.length} presentation records available for review.</p></div></div><div className="operations-table-scroll"><table className="operations-table"><thead><tr><th>Report ID</th><th>Tender / Requirement</th><th>Department</th><th>Status</th><th>Generated Date</th><th>Match Score</th><th>Action</th></tr></thead><tbody>{filteredReports.map((report) => <tr key={report.id}><td className="operations-id">{report.id}</td><td><strong>{report.requirement}</strong></td><td className="operations-muted">{report.department}</td><td><StatusBadge status={report.status} /></td><td className="operations-muted">{report.date}</td><td className="operations-score">{report.score}</td><td><div className="operations-row-actions"><button type="button" onClick={() => showUnavailable('View', report.id)}>View</button><button type="button" aria-label={`Download ${report.id}`} onClick={() => showUnavailable('Download', report.id)}><Download size={14} /></button><button type="button" aria-label={`Share ${report.id}`} onClick={() => showUnavailable('Share', report.id)}><Share2 size={14} /></button></div></td></tr>)}</tbody></table></div><div className="operations-table-footer"><span>Showing {filteredReports.length} of 186 reports</span><div><button type="button" disabled>Previous</button><button className="is-active" type="button">1</button><button type="button">2</button><button type="button">Next</button></div></div></section>
      {notice ? <div className="operations-notice" role="status"><span>{notice}</span><button type="button" onClick={() => setNotice('')}>Dismiss</button></div> : null}
    </main>
  </AppShell>;
}
