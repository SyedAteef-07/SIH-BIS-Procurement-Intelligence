import { ChevronDown, CircleHelp, Home, Info, ShieldCheck, UserRound } from 'lucide-react';

export default function Navbar() {
  function handleHome(e) {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function handleAbout(e) {
    e.preventDefault();
    alert('BIS Procurement Intelligence v0.1.0\n\nAn AI-powered tool to help government procurement officers identify relevant Indian Standards for their tenders.\n\nBuilt for Smart India Hackathon.');
  }

  function handleHelp(e) {
    e.preventDefault();
    alert('How to use:\n\n1. Enter a product requirement or upload a tender document\n2. Click "Analyze Requirement"\n3. Review recommended standards, gap analysis, and certifications\n4. Download the report for your records\n\nTip: Try the example queries to see the system in action!');
  }

  return (
    <header className="navbar">
      <a className="brand" href="#top" aria-label="BIS Procurement Intelligence home" onClick={handleHome}>
        <span className="brand-mark"><ShieldCheck size={22} strokeWidth={2.4} /></span>
        <span>BIS Procurement Intelligence</span>
      </a>
      <nav className="nav-links" aria-label="Main navigation">
        <a href="#top" onClick={handleHome}><Home size={14} />Home</a>
        <a href="#about" onClick={handleAbout}><Info size={14} />About</a>
        <a href="#help" onClick={handleHelp}><CircleHelp size={14} />Help</a>
      </nav>
      <button className="profile-button" type="button" onClick={() => alert('Profile settings coming soon.')}>
        <span className="profile-icon"><UserRound size={16} /></span>
        <span>Government Officer</span>
        <ChevronDown size={14} />
      </button>
    </header>
  );
}
