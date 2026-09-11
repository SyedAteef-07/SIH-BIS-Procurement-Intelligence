import {
  BarChart3,
  FileSearch,
  FileText,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldCheck,
} from 'lucide-react';

const navigation = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { key: 'analyze', label: 'Analyze Tender', icon: FileSearch },
  { key: 'standards', label: 'BIS Standards', icon: ShieldCheck },
  { key: 'reports', label: 'Analysis Reports', icon: FileText },
  { key: 'analytics', label: 'Analytics', icon: BarChart3 },
  { key: 'settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ activePage, onNavigate, isOpen, onClose }) {
  return (
    <>
      <button className={isOpen ? 'sidebar-backdrop is-visible' : 'sidebar-backdrop'} type="button" aria-label="Close navigation" onClick={onClose} />
      <aside className={isOpen ? 'app-sidebar is-open' : 'app-sidebar'} aria-label="Application navigation">
        <div className="sidebar-top">
          <div className="sidebar-brand">
            <span className="sidebar-brand-mark"><ShieldCheck size={20} /></span>
            <span><strong>BIS INTEL</strong><small>Procurement Intelligence</small></span>
          </div>

          <nav className="sidebar-nav">
            {navigation.map(({ key, label, icon: Icon }) => (
              <button
                className={activePage === key ? 'sidebar-nav-item is-active' : 'sidebar-nav-item'}
                type="button"
                key={key}
                aria-current={activePage === key ? 'page' : undefined}
                onClick={() => {
                  onNavigate?.(key);
                  onClose?.();
                }}
              >
                <Icon size={18} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="sidebar-bottom">
          <section className="support-card" aria-labelledby="support-title">
            <strong id="support-title">Government Support</strong>
            <p>Direct hotline for compliance framework queries and BIS standards verification.</p>
            <button type="button" onClick={() => onNavigate?.('support')}>Access Support Center</button>
          </section>
          <div className="sidebar-profile">
            <div className="profile-avatar">MR</div>
            <div><strong>Dir. M. Rawlings</strong><small>National Office</small></div>
            <button type="button" aria-label="Log out"><LogOut size={16} /></button>
          </div>
        </div>
      </aside>
    </>
  );
}
