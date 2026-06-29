import { useState, useEffect } from 'react';
import { fetchComponents, type ComponentDTO } from './apiClient';

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
  const [components, setComponents] = useState<ComponentDTO[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Sync hash routing
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      const matchingTab = TABS.find(t => t.id === hash);
      if (matchingTab) {
        setActiveTab(matchingTab.id);
      } else {
        setActiveTab('dashboard');
      }
    };

    // Initial load
    handleHashChange();

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Fetch components when Dashboard becomes active
  const loadComponents = async () => {
    try {
      const data = await fetchComponents();
      setComponents(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'dashboard') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadComponents();
    }
  }, [activeTab]);

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadComponents();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'up':
        return (
          <span className="health-badge health-badge--up" data-testid="status-badge-up">
            <svg className="health-badge-icon" viewBox="0 0 12 12" width="12" height="12" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <circle cx="6" cy="6" r="4" />
            </svg>
            <span>Operational</span>
          </span>
        );
      case 'down':
        return (
          <span className="health-badge health-badge--down" data-testid="status-badge-down">
            <svg className="health-badge-icon" viewBox="0 0 12 12" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <line x1="2" y1="6" x2="10" y2="6" />
            </svg>
            <span>Outage</span>
          </span>
        );
      case 'degraded':
        return (
          <span className="health-badge health-badge--degraded" data-testid="status-badge-degraded">
            <svg className="health-badge-icon" viewBox="0 0 12 12" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <polygon points="6,2 10,10 2,10" />
            </svg>
            <span>Degraded</span>
          </span>
        );
      case 'maintenance':
        return (
          <span className="health-badge health-badge--maintenance" data-testid="status-badge-maintenance">
            <svg className="health-badge-icon" viewBox="0 0 12 12" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="2 2" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <circle cx="6" cy="6" r="4" />
            </svg>
            <span>Maintenance</span>
          </span>
        );
      default:
        return (
          <span className="health-badge" data-testid="status-badge-unknown">
            <span>{status}</span>
          </span>
        );
    }
  };

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
              onClick={() => {
                if (tab.id === 'dashboard') {
                  setLoading(true);
                  setError(null);
                }
                setActiveTab(tab.id);
              }}
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
          <div className="tab-panel" data-testid="dashboard-panel">
            <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
              <div>
                <h1 className="display-md">Dashboard</h1>
                <p className="caption" style={{ marginTop: '4px' }}>Real-time operator view of component health and status.</p>
              </div>
              <button onClick={handleRefresh} className="btn-secondary" style={{ padding: '10px 16px', fontSize: '14px' }}>
                Refresh
              </button>
            </div>

            {loading ? (
              <div className="panel" style={{ display: 'flex', justifyContent: 'center', padding: 'var(--spacing-xxl)' }} data-testid="loading-indicator">
                <span className="body-md" style={{ color: 'var(--colors-muted)' }}>Loading components...</span>
              </div>
            ) : error ? (
              <div className="panel" style={{ borderColor: 'var(--colors-signature-coral)', backgroundColor: 'var(--colors-health-down-surface)' }} data-testid="error-message">
                <h2 className="title-sm" style={{ color: 'var(--colors-signature-coral)' }}>Failed to Load Components</h2>
                <p className="body-md" style={{ marginTop: 'var(--spacing-xs)', color: 'var(--colors-body)' }}>{error}</p>
                <button onClick={handleRefresh} className="btn-primary" style={{ marginTop: 'var(--spacing-md)', padding: '10px 16px', fontSize: '14px' }}>
                  Try Again
                </button>
              </div>
            ) : (
              <div className="panel" data-testid="components-list" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '500px' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--colors-hairline)', backgroundColor: 'var(--colors-surface-soft)' }}>
                        <th className="label-md" style={{ padding: 'var(--spacing-md)', color: 'var(--colors-muted)', fontWeight: 500 }}>Component Name</th>
                        <th className="label-md" style={{ padding: 'var(--spacing-md)', color: 'var(--colors-muted)', fontWeight: 500 }}>Identifier</th>
                        <th className="label-md" style={{ padding: 'var(--spacing-md)', color: 'var(--colors-muted)', fontWeight: 500 }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {components.map(comp => (
                        <tr key={comp.id} style={{ borderBottom: '1px solid var(--colors-hairline)' }}>
                          <td className="body-md" style={{ padding: 'var(--spacing-md)', color: 'var(--colors-ink)', fontWeight: 500 }}>{comp.name}</td>
                          <td className="body-md" style={{ padding: 'var(--spacing-md)', color: 'var(--colors-muted)', fontFamily: 'monospace' }}>{comp.id}</td>
                          <td className="body-md" style={{ padding: 'var(--spacing-md)' }}>
                            {getStatusBadge(comp.status)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
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
