import { FileText, Search, UploadCloud } from 'lucide-react';

export default function QuickActionsCard({ onAnalyze }) {
  const actions = [
    { label: 'Analyze New Tender', icon: FileText, primary: true, onClick: onAnalyze },
    { label: 'Import Bulk Tenders', icon: UploadCloud },
    { label: 'Generate Analysis Report', icon: FileText },
    { label: 'Search BIS Standards', icon: Search },
  ];

  return <section className="dashboard-card rail-card" aria-labelledby="quick-actions-title"><h2 id="quick-actions-title">Quick Actions</h2><div className="action-stack">{actions.map(({ label, icon: Icon, primary, onClick }) => <button className={primary ? 'rail-action primary' : 'rail-action'} type="button" key={label} onClick={onClick}><Icon size={16} />{label}</button>)}</div></section>;
}
