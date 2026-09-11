import { Database, FileCheck2, FileUp, ShieldCheck } from 'lucide-react';
import AppShell from './components/AppShell';
import ActivityCard from './components/ActivityCard';
import QuickActionsCard from './components/QuickActionsCard';
import RecentAnalysesTable from './components/RecentAnalysesTable';
import StatCard from './components/StatCard';
import SystemOperationsCard from './components/SystemOperationsCard';
import UpcomingDeadlinesCard from './components/UpcomingDeadlinesCard';
import './dashboard.css';

const stats = [
  { label: 'Total Tenders', value: '1,247', trend: '+12.4% vs last month', icon: Database },
  { label: 'Active Analyses', value: '38', trend: '+3 new today', icon: Database },
  { label: 'BIS Standards Mapped', value: '156', trend: '+8.2% vs last month', icon: FileCheck2 },
  { label: 'Compliance Rate', value: '94.2%', trend: '+0.4% vs last month', icon: ShieldCheck },
];

export default function DashboardPage({ onNavigate }) {
  return (
    <AppShell activePage="dashboard" onNavigate={onNavigate}>
      <main className="dashboard-workspace">
        <section className="dashboard-header" aria-labelledby="dashboard-title">
          <div><h1 id="dashboard-title">Procurement Intelligence Dashboard</h1><p>Real-time procurement compliance, BIS standards alignment, and tender analysis insights.</p></div>
          <button className="primary-dashboard-button" type="button" onClick={() => onNavigate?.('analyze')}><FileUp size={16} /> Analyze New Tender</button>
        </section>
        <section className="stats-grid" aria-label="Procurement summary">{stats.map((stat) => <StatCard key={stat.label} {...stat} />)}</section>
        <div className="dashboard-split"><RecentAnalysesTable /><aside className="dashboard-rail"><QuickActionsCard onAnalyze={() => onNavigate?.('analyze')} /><ActivityCard /><SystemOperationsCard /><UpcomingDeadlinesCard /></aside></div>
      </main>
    </AppShell>
  );
}
