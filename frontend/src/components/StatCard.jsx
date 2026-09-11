export default function StatCard({ label, value, trend, icon: Icon }) {
  return (
    <article className="stat-card">
      <div className="stat-card-header"><span>{label}</span><span className="stat-card-icon"><Icon size={18} /></span></div>
      <div className="stat-card-body"><strong>{value}</strong><span className="trend-badge">{trend}</span></div>
    </article>
  );
}
