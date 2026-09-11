const statusClasses = {
  Compliant: 'status-success',
  'Under Review': 'status-warning',
  'Non-Compliant': 'status-error',
  'High Match': 'status-info',
  Active: 'status-success',
  'Active with amendments': 'status-warning',
  'Under revision': 'status-warning',
  Superseded: 'status-error',
  Withdrawn: 'status-error',
  Completed: 'status-success',
  Draft: 'status-info',
  Archived: 'status-info',
};

export default function StatusBadge({ status }) {
  return <span className={`status-badge ${statusClasses[status] || 'status-info'}`}>{status}</span>;
}
