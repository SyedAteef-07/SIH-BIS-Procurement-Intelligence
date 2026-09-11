import { AudioLines, ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import StatusBadge from './StatusBadge';

const recentAnalyses = [
  { id: 'NIT-2026-104', requirement: 'National Highway Surveillance Integration', department: 'Ministry of Road Transport', standards: 8, status: 'Compliant', gaps: 0, date: '24 Oct 2026' },
  { id: 'SD-2026-091', requirement: 'Secure Cloud Migration Services', department: 'Federal Source of Digital Communications', standards: 5, status: 'Under Review', gaps: 2, date: '21 Oct 2026' },
  { id: 'FO-2026-218', requirement: 'Smart Energy Grid Transformer', department: 'Ministry of Power', standards: 7, status: 'Compliant', gaps: 1, date: '21 Oct 2026' },
  { id: 'TC-2026-0312', requirement: 'Tactical Radio Equipment & High-Frequency Transceivers', department: 'Department of Defense Procurement Liaison', standards: 6, status: 'Non-Compliant', gaps: 3, date: '20 Oct 2026' },
  { id: 'HD-2026-8804', requirement: 'Medical Device Sourcing & Hospital Facility Logistics', department: 'Central Healthcare Logistics & Welfare Authority', standards: 4, status: 'High Match', gaps: 0, date: '19 Oct 2026' },
  { id: 'PD-2026-0771', requirement: 'Clean Water Plant Filtration Upgrades', department: 'Dept of Sanitation & Municipal Planning', standards: 3, status: 'Compliant', gaps: 0, date: '18 Oct 2026' },
];

const columns = ['Tender ID', 'Requirement', 'Department', 'Standards Found', 'Compliance', 'Gaps', 'Date', 'Action'];

export default function RecentAnalysesTable() {
  return (
    <section className="dashboard-card recent-analyses-card" aria-labelledby="recent-analyses-title">
      <div className="card-heading-row">
        <div><h2 id="recent-analyses-title">Recent Analyses</h2><p>Latest procurement compliance evaluations and tender analysis results.</p></div>
        <button className="filter-button" type="button"><AudioLines size={14} /> Filter</button>
      </div>
      <div className="table-scroll">
        <table className="analyses-table">
          <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
          <tbody>{recentAnalyses.map((item) => <tr key={item.id}>
            <td className="tender-id">{item.id}</td><td className="requirement-cell">{item.requirement}</td><td className="department-cell">{item.department}</td><td>{item.standards}</td><td><StatusBadge status={item.status} /></td><td>{item.gaps}</td><td>{item.date}</td><td><button className="table-action" type="button">Review</button></td>
          </tr>)}</tbody>
        </table>
      </div>
      <div className="table-footer"><span>Showing 6 of 1,247 indexed tender records</span><div><button type="button" aria-label="Previous page"><ChevronLeft size={14} /> Prev</button><button type="button" aria-label="Next page">Next <ChevronRight size={14} /></button></div></div>
    </section>
  );
}
