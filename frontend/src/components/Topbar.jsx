import { Bell, ChevronRight, Menu, Search } from 'lucide-react';

export default function Topbar({ onMenuOpen, currentPage = 'Dashboard' }) {
  return (
    <header className="app-topbar">
      <button className="mobile-menu-button" type="button" aria-label="Open navigation" onClick={onMenuOpen}><Menu size={20} /></button>
      <div className="breadcrumb" aria-label="Breadcrumb"><span>Home</span><ChevronRight size={14} /><strong>{currentPage}</strong></div>
      <div className="topbar-controls">
        <label className="dashboard-search">
          <Search size={16} />
          <input type="search" placeholder="Search tender ID, title, or agency..." aria-label="Search tenders" />
        </label>
        <button className="notification-button" type="button" aria-label="View notifications"><Bell size={21} /><span aria-hidden="true" /></button>
        <span className="system-status"><i /> System Secure</span>
      </div>
    </header>
  );
}
