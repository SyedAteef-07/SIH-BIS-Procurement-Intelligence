import { ChevronDown, CircleHelp, Home, Info, ShieldCheck, UserRound } from 'lucide-react';

export default function Navbar() {
  return (
    <header className="navbar">
      <a className="brand" href="#top" aria-label="BIS Procurement Intelligence home">
        <span className="brand-mark"><ShieldCheck size={22} strokeWidth={2.4} /></span>
        <span>BIS Procurement Intelligence</span>
      </a>
      <nav className="nav-links" aria-label="Main navigation">
        <a href="#top"><Home size={14} />Home</a>
        <a href="#about"><Info size={14} />About</a>
        <a href="#help"><CircleHelp size={14} />Help</a>
      </nav>
      <button className="profile-button" type="button">
        <span className="profile-icon"><UserRound size={16} /></span>
        <span>Government Officer</span>
        <ChevronDown size={14} />
      </button>
    </header>
  );
}
