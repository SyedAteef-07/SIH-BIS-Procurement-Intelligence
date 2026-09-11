const activity = [
  { day: 'Mon', height: 18 }, { day: 'Tue', height: 24 }, { day: 'Wed', height: 30 }, { day: 'Thu', height: 36 }, { day: 'Fri', height: 42 }, { day: 'Sat', height: 48 }, { day: 'Sun', height: 54 },
];

export default function ActivityCard() {
  return <section className="dashboard-card rail-card activity-card" aria-labelledby="activity-title"><div><h2 id="activity-title">Activity</h2><p>Analysis volume over the last 7 days.</p></div><div className="activity-chart" aria-label="Analysis volume increases from Monday through Sunday">{activity.map(({ day, height }, index) => <div className="activity-column" key={day}><span className={index === activity.length - 1 ? 'is-current' : ''} style={{ height }} /><small>{day}</small></div>)}</div></section>;
}
