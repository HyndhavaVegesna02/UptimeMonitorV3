import { useState, useEffect } from 'react';
import { Dashboard } from './tabs/Dashboard';

const TABS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'availability', label: 'Availability' },
  { id: 'approvals', label: 'Approvals' },
  { id: 'check-history', label: 'Check History' },
  { id: 'maintenance', label: 'Maintenance' },
  { id: 'publications', label: 'Publications' }
] as const;

type TabId = typeof TABS[number]['id'];

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');

  // Sync hash routing — derives state from the URL, never from a prop change.
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      const matchingTab = TABS.find(t => t.id === hash);
      setActiveTab(matchingTab ? matchingTab.id : 'dashboard');
    };

    // Initial load
    handleHashChange();

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return (
    <div className="app-shell">
      <header className="top-nav">
        <div className="nav-brand">
          <span className="title-sm" style={{ fontWeight: 600, color: 'var(--colors-primary)' }}>Uptime Monitor V3</span>
        </div>
        <nav className="nav-links" aria-label="Main Navigation">
          {TABS.map(tab => (
            <a
              key={tab.id}
              href={`#${tab.id}`}
              className={`nav-link ${activeTab === tab.id ? 'nav-state-active' : ''}`}
              aria-current={activeTab === tab.id ? 'page' : undefined}
            >
              {tab.label}
            </a>
          ))}
        </nav>
        <div className="nav-actions">
          <button className="btn-secondary" style={{ padding: '8px 16px', fontSize: '14px', height: '36px' }}>
            Sign Out
          </button>
        </div>
      </header>

      <main className="main-content" id="main-content">
        {activeTab === 'dashboard' ? (
          <Dashboard />
        ) : (
          <div className="panel" data-testid="placeholder-panel">
            <h1 className="display-md">{TABS.find(t => t.id === activeTab)?.label}</h1>
            <p className="body-md" style={{ marginTop: 'var(--spacing-md)', color: 'var(--colors-muted)' }}>
              The {TABS.find(t => t.id === activeTab)?.label} panel is coming soon in a future sprint.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
