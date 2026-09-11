import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ArrowRight, BookOpen, ChevronLeft, ChevronRight, Database, Filter, Info, RefreshCw, Search, ShieldCheck, SlidersHorizontal } from 'lucide-react';
import AppShell from './components/AppShell';
import StatusBadge from './components/StatusBadge';
import './standards.css';

const PAGE_SIZE = 10;
const presentationStats = [
  { label: 'Total Standards', value: '24,850', icon: Database },
  { label: 'Active Standards', value: '21,420', icon: ShieldCheck },
  { label: 'With Amendments', value: '3,218', icon: RefreshCw },
  { label: 'Recently Updated', value: '126', icon: BookOpen },
];

const recentUpdates = [
  { number: 'IS 694:2010', title: 'PVC insulated cables', type: 'Amendment' },
  { number: 'IS 732:2019', title: 'Electrical wiring installations', type: 'Revision' },
  { number: 'IS 12269:2013', title: 'Ordinary Portland cement', type: 'Erratum' },
];

const statusOptions = ['All', 'Active', 'Active with amendments', 'Under revision', 'Superseded', 'Withdrawn'];
const editionOptions = ['All', '2006', '2008', '2010', '2013', '2018', '2019'];

function normalizeStatus(status) {
  return status?.toLowerCase().replace(/\s+/g, ' ').trim() || '';
}

function statusLabel(status) {
  return status || 'Status unavailable';
}

function matchesStatus(standard, selectedStatus) {
  if (selectedStatus === 'All') return true;
  return normalizeStatus(standard.status) === normalizeStatus(selectedStatus);
}

function matchesSector(standard, selectedSector) {
  if (selectedSector === 'All') return true;
  const searchable = `${standard.scope} ${standard.title}`.toLowerCase();
  const sectorTerms = {
    Electrical: ['electrical', 'cable', 'wire', 'voltage', 'wiring', 'appliance', 'lighting'],
    Construction: ['cement', 'concrete', 'construction', 'building'],
    Safety: ['safety', 'helmet', 'protective'],
  };
  return (sectorTerms[selectedSector] || [selectedSector.toLowerCase()]).some((term) => searchable.includes(term));
}

export default function BISStandardsPage({ onNavigate }) {
  const [standards, setStandards] = useState([]);
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [status, setStatus] = useState('All');
  const [edition, setEdition] = useState('All');
  const [sector, setSector] = useState('Electrical');
  const [sortBy, setSortBy] = useState('IS Number');
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryToken, setRetryToken] = useState(0);
  const [selectedStandard, setSelectedStandard] = useState(null);

  useEffect(() => {
    let isCurrent = true;
    setIsLoading(true);
    setError('');
    const search = submittedQuery.trim();
    const endpoint = search ? `http://localhost:8000/api/standards?search=${encodeURIComponent(search)}` : 'http://localhost:8000/api/standards';
    fetch(endpoint)
      .then((response) => {
        if (!response.ok) throw new Error('Unable to load BIS standards.');
        return response.json();
      })
      .then((data) => {
        if (isCurrent) setStandards(Array.isArray(data) ? data : []);
      })
      .catch((fetchError) => {
        if (isCurrent) setError(fetchError.message || 'Unable to load BIS standards.');
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false);
      });
    return () => { isCurrent = false; };
  }, [retryToken, submittedQuery]);

  const filteredStandards = useMemo(() => {
    const values = standards.filter((standard) => matchesStatus(standard, status) && (edition === 'All' || standard.edition === edition) && matchesSector(standard, sector));
    return [...values].sort((left, right) => {
      if (sortBy === 'Title') return left.title.localeCompare(right.title);
      if (sortBy === 'Relevance') return submittedQuery ? 0 : left.number.localeCompare(right.number);
      if (sortBy === 'Recently Updated') return right.edition.localeCompare(left.edition);
      return left.number.localeCompare(right.number);
    });
  }, [edition, sector, sortBy, standards, status, submittedQuery]);

  const totalPages = Math.max(1, Math.ceil(filteredStandards.length / PAGE_SIZE));
  const visibleStandards = filteredStandards.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const firstRecord = filteredStandards.length ? (page - 1) * PAGE_SIZE + 1 : 0;
  const lastRecord = Math.min(page * PAGE_SIZE, filteredStandards.length);

  function runSearch(event) {
    event.preventDefault();
    setPage(1);
    setSubmittedQuery(query);
  }

  function clearFilters() {
    setQuery('');
    setSubmittedQuery('');
    setStatus('All');
    setEdition('All');
    setSector('Electrical');
    setPage(1);
  }

  function updateFilter(setter, value) {
    setter(value);
    setPage(1);
  }

  return (
    <AppShell activePage="standards" currentPage="BIS Standards" onNavigate={onNavigate}>
      <main className="standards-workspace" aria-labelledby="standards-page-title">
        <header className="standards-page-header"><div><span className="standards-kicker">BIS KNOWLEDGE REGISTRY</span><h1 id="standards-page-title">BIS Standards</h1><p>Search and explore Indian Standards, editions, amendments, related references, and compliance information.</p></div><button className="standards-primary-button" type="button" onClick={() => document.getElementById('standards-search-input')?.focus()}><Search size={16} /> Search Standards Database</button></header>

        <section className="standards-search-card" aria-labelledby="search-standards-title"><div className="standards-card-title"><div><h2 id="search-standards-title"><Search size={18} /> Search BIS Standards</h2><p>Find a standard by number, title, product, or keyword.</p></div><span className="suggested-query">Suggested query: PVC insulated cable</span></div><form onSubmit={runSearch}><label className="standards-search-input"><Search size={17} /><input id="standards-search-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by IS number, title, product, keyword..." /></label><div className="standards-filters"><label>Category<select value="All" onChange={() => {}}><option>All</option></select></label><label>Status<select value={status} onChange={(event) => updateFilter(setStatus, event.target.value)}>{statusOptions.map((option) => <option key={option}>{option}</option>)}</select></label><label>Edition<select value={edition} onChange={(event) => updateFilter(setEdition, event.target.value)}>{editionOptions.map((option) => <option key={option}>{option}</option>)}</select></label><label>Sector<select value={sector} onChange={(event) => updateFilter(setSector, event.target.value)}><option>All</option><option>Electrical</option><option>Construction</option><option>Safety</option></select></label><button className="filter-button" type="button"><SlidersHorizontal size={15} /> More Filters</button><button className="clear-filters-button" type="button" onClick={clearFilters}>Clear Filters</button><button className="standards-search-button" type="submit"><Search size={15} /> Search</button></div></form></section>

        <section className="standards-stats-grid" aria-label="BIS standards statistics">{presentationStats.map(({ label, value, icon: Icon }) => <article className="standards-stat-card" key={label}><div><span>{label}</span><strong>{value}</strong></div><span className="standards-stat-icon"><Icon size={18} /></span></article>)}</section>

        <div className="standards-main-grid"><section className="registry-card" aria-labelledby="registry-title"><div className="registry-header"><div><span className="standards-kicker">NATIONAL REGISTRY</span><h2 id="registry-title">BIS National Registry</h2><p>Browse standards matching your search and filters.</p></div><label className="sort-control">Sort by:<select value={sortBy} onChange={(event) => setSortBy(event.target.value)}><option>IS Number</option><option>Relevance</option><option>Recently Updated</option><option>Title</option></select></label></div>{isLoading ? <div className="standards-state"><RefreshCw size={18} /> Loading BIS standards...</div> : error ? <div className="standards-state is-error"><AlertCircle size={18} /><span>{error}<small>Please try again.</small></span><button type="button" onClick={() => setRetryToken((current) => current + 1)}>Retry</button></div> : filteredStandards.length === 0 ? <div className="standards-state"><Info size={18} /> No BIS standards found. Try changing your search terms or filters.</div> : <div className="registry-table-wrap"><table className="registry-table"><thead><tr><th>IS Number</th><th>Standard Title</th><th>Category / Sector</th><th>Edition</th><th>Status</th><th>Last Updated</th><th>Action</th></tr></thead><tbody>{visibleStandards.map((standard) => <tr key={standard.number}><td className="registry-number">{standard.number}</td><td><strong>{standard.title}</strong></td><td className="registry-scope">{standard.scope}</td><td>{standard.edition}</td><td><StatusBadge status={statusLabel(standard.status)} /></td><td className="registry-muted">Not available</td><td><button className="view-standard-button" type="button" onClick={() => setSelectedStandard(standard)}>View Standard</button></td></tr>)}</tbody></table></div>}<div className="registry-footer"><span>Showing {firstRecord}–{lastRecord} of {filteredStandards.length} loaded standards</span><div className="pagination"><button type="button" aria-label="Previous page" disabled={page === 1} onClick={() => setPage((current) => Math.max(1, current - 1))}><ChevronLeft size={14} /> Previous</button>{Array.from({ length: Math.min(totalPages, 3) }, (_, index) => index + 1).map((pageNumber) => <button className={page === pageNumber ? 'is-active' : ''} type="button" key={pageNumber} onClick={() => setPage(pageNumber)}>{pageNumber}</button>)}{totalPages > 3 ? <span>...</span> : null}<button type="button" aria-label="Next page" disabled={page === totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))}>Next <ChevronRight size={14} /></button></div></div></section>

          <aside className="standards-side-rail"><section className="recently-updated-card standards-side-card" aria-labelledby="recent-title"><div className="side-card-heading"><h2 id="recent-title">Recently Updated</h2><button type="button">View All</button></div><div className="recent-update-list">{recentUpdates.map((item) => <div className="recent-update" key={item.number}><div><strong>{item.number}</strong><span>{item.title}</span></div><small>{item.type}</small></div>)}</div></section><section className="directive-card" aria-labelledby="directive-title"><ShieldCheck size={21} /><h2 id="directive-title">National Security Directive</h2><p>Standard searches and standard reference validation logs are securely archived. Ensure appropriate clearance before generating external compliance reports.</p><button type="button">Acknowledge Directive <ArrowRight size={14} /></button></section></aside></div>
        {selectedStandard ? <div className="standard-selection-note" role="status"><BookOpen size={16} /><span><strong>{selectedStandard.number}</strong> selected for future standard details.</span><button type="button" aria-label="Dismiss selected standard" onClick={() => setSelectedStandard(null)}>Dismiss</button></div> : null}
      </main>
    </AppShell>
  );
}
