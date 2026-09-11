import { useState } from 'react';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function AppShell({ activePage = 'dashboard', currentPage, onNavigate, children }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="app-shell dashboard-theme">
      <Sidebar activePage={activePage} onNavigate={onNavigate} isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      <div className="app-main">
        <Topbar currentPage={currentPage || (activePage === 'analyze' ? 'Analyze Tender' : 'Dashboard')} onMenuOpen={() => setIsSidebarOpen(true)} />
        {children}
      </div>
    </div>
  );
}
