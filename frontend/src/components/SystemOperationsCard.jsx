import { DatabaseSearch, DownloadCloud, UploadCloud } from 'lucide-react';

const operations = [
  ['Upload Compliance Brief', UploadCloud],
  ['Scan Standards Database', DatabaseSearch],
  ['Export Regulatory Archive', DownloadCloud],
];

export default function SystemOperationsCard() {
  return <section className="dashboard-card rail-card" aria-labelledby="operations-title"><h2 id="operations-title">System Operations</h2><div className="action-stack">{operations.map(([label, Icon]) => <button className="rail-action" type="button" key={label}><Icon size={16} />{label}</button>)}</div></section>;
}
