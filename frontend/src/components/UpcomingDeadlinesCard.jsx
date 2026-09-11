const deadlines = [
  { day: '28', month: 'Oct', title: 'Filing: Secure Smart Tenders...', detail: 'Must file in 4 days', urgent: true },
  { day: '02', month: 'Nov', title: 'Defense Comm. Technical...', detail: 'Scheduled evaluation' },
  { day: '15', month: 'Nov', title: 'National Grid Phase 3...', detail: 'Standards certificate check' },
];

export default function UpcomingDeadlinesCard() {
  return <section className="dashboard-card rail-card deadlines-card" aria-labelledby="deadlines-title"><div className="card-heading-row"><h2 id="deadlines-title">Upcoming Deadlines</h2><button className="all-link" type="button">All</button></div><div className="deadlines-list">{deadlines.map((item) => <div className="deadline-item" key={`${item.day}-${item.month}`}><div className={item.urgent ? 'deadline-date urgent' : 'deadline-date'}><strong>{item.day}</strong><span>{item.month}</span></div><div><strong>{item.title}</strong><p className={item.urgent ? 'urgent-text' : ''}>{item.detail}</p></div></div>)}</div></section>;
}
