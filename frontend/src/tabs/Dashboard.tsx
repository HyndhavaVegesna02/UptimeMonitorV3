import { useComponents } from '../hooks/useComponents';
import type { ComponentDTO } from '../apiClient';

/* ─────────────────────────────────────────────────────────────────────────────
   getStatusBadge — SVG icon + text label.
   Status is NEVER conveyed by color alone (AC3).
   Unknown statuses display the raw string neutrally rather than crashing.
   ───────────────────────────────────────────────────────────────────────────── */
function getStatusBadge(status: string) {
  switch (status) {
    case 'up':
      return (
        <span
          className="health-badge health-badge--up"
          data-testid="status-badge-up"
          role="img"
          aria-label="Operational"
        >
          <svg
            className="health-badge-icon"
            viewBox="0 0 12 12"
            width="12"
            height="12"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
          >
            <circle cx="6" cy="6" r="4" />
          </svg>
          <span>Operational</span>
        </span>
      );
    case 'down':
      return (
        <span
          className="health-badge health-badge--down"
          data-testid="status-badge-down"
          role="img"
          aria-label="Outage"
        >
          <svg
            className="health-badge-icon"
            viewBox="0 0 12 12"
            width="12"
            height="12"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
          >
            <line x1="2" y1="6" x2="10" y2="6" />
          </svg>
          <span>Outage</span>
        </span>
      );
    case 'degraded':
      return (
        <span
          className="health-badge health-badge--degraded"
          data-testid="status-badge-degraded"
          role="img"
          aria-label="Degraded"
        >
          <svg
            className="health-badge-icon"
            viewBox="0 0 12 12"
            width="12"
            height="12"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
          >
            <polygon points="6,2 10,10 2,10" />
          </svg>
          <span>Degraded</span>
        </span>
      );
    case 'maintenance':
      return (
        <span
          className="health-badge health-badge--maintenance"
          data-testid="status-badge-maintenance"
          role="img"
          aria-label="Maintenance"
        >
          <svg
            className="health-badge-icon"
            viewBox="0 0 12 12"
            width="12"
            height="12"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray="2 2"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
            focusable="false"
          >
            <circle cx="6" cy="6" r="4" />
          </svg>
          <span>Maintenance</span>
        </span>
      );
    default:
      return (
        <span
          className="health-badge"
          data-testid="status-badge-unknown"
          role="img"
          aria-label={status}
        >
          <span>{status}</span>
        </span>
      );
  }
}

/* ─────────────────────────────────────────────────────────────────────────────
   ComponentRow — a single <tr> in the status table.
   Declared outside Dashboard so it is not recreated on every render.
   ───────────────────────────────────────────────────────────────────────────── */
function ComponentRow({ component }: { component: ComponentDTO }) {
  return (
    <tr className="dashboard-table-row">
      <td className="dashboard-table-cell dashboard-table-cell--name">
        <span className="label-md" style={{ color: 'var(--colors-ink)' }}>
          {component.name}
        </span>
      </td>
      <td className="dashboard-table-cell dashboard-table-cell--id">
        <span
          className="body-md"
          style={{ color: 'var(--colors-muted)', fontFamily: 'monospace' }}
        >
          {component.id}
        </span>
      </td>
      <td className="dashboard-table-cell dashboard-table-cell--status">
        {getStatusBadge(component.status)}
      </td>
    </tr>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Loading skeleton — a calm, quiet state consistent with the white-canvas aesthetic.
   ───────────────────────────────────────────────────────────────────────────── */
function LoadingSkeleton() {
  return (
    <div
      className="panel dashboard-loading"
      data-testid="loading-indicator"
      aria-label="Loading components"
      aria-busy="true"
    >
      <div className="dashboard-skeleton-rows" aria-hidden="true">
        {[1, 2, 3].map((n) => (
          <div key={n} className="dashboard-skeleton-row">
            <div className="dashboard-skeleton-cell dashboard-skeleton-cell--name" />
            <div className="dashboard-skeleton-cell dashboard-skeleton-cell--id" />
            <div className="dashboard-skeleton-cell dashboard-skeleton-cell--status" />
          </div>
        ))}
      </div>
      <p className="body-md" style={{ color: 'var(--colors-muted)', marginTop: 'var(--spacing-sm)' }}>
        Loading components…
      </p>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   EmptyState — shown when the API returns an empty array.
   ───────────────────────────────────────────────────────────────────────────── */
function EmptyState() {
  return (
    <div
      className="panel dashboard-empty"
      data-testid="empty-state"
    >
      <p className="body-md" style={{ color: 'var(--colors-muted)' }}>
        No components configured yet.
      </p>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   ErrorPanel — shown on fetch failure. "Try Again" calls refetch.
   Uses the tokenized --colors-health-down-surface tint (no raw literals).
   ───────────────────────────────────────────────────────────────────────────── */
function ErrorPanel({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="panel dashboard-error" data-testid="error-message">
      <h2
        className="title-sm"
        style={{ color: 'var(--colors-signature-coral)' }}
      >
        Failed to Load Components
      </h2>
      <p
        className="body-md"
        style={{ marginTop: 'var(--spacing-xs)', color: 'var(--colors-body)' }}
      >
        {message}
      </p>
      <button
        onClick={onRetry}
        className="btn-primary"
        style={{ marginTop: 'var(--spacing-md)', padding: '10px 16px', fontSize: '14px' }}
      >
        Try Again
      </button>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   ComponentTable — real <table> with <th scope> for a11y.
   No horizontal scroll at 375px: the outer wrapper enables overflow-x: auto
   so the table scrolls inside the panel rather than the viewport.
   ───────────────────────────────────────────────────────────────────────────── */
function ComponentTable({ components }: { components: ComponentDTO[] }) {
  return (
    <div
      className="panel"
      data-testid="components-list"
      style={{ padding: 0, overflow: 'hidden' }}
    >
      <div style={{ overflowX: 'auto' }}>
        <table className="dashboard-table" aria-label="Component status">
          <thead>
            <tr className="dashboard-table-header-row">
              <th
                scope="col"
                className="dashboard-table-header dashboard-table-header--name label-md"
              >
                Component Name
              </th>
              <th
                scope="col"
                className="dashboard-table-header dashboard-table-header--id label-md"
              >
                Identifier
              </th>
              <th
                scope="col"
                className="dashboard-table-header dashboard-table-header--status label-md"
              >
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {components.map((comp) => (
              <ComponentRow key={comp.id} component={comp} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Dashboard — the tab page component.
   Renders: header + refresh button, then one of four explicit branches:
   loading | error | empty | success. No components-inside-components pattern.
   ───────────────────────────────────────────────────────────────────────────── */
export function Dashboard() {
  const { data, loading, error, refetch } = useComponents();

  const handleRefresh = () => {
    refetch();
  };

  return (
    <div className="tab-panel" data-testid="dashboard-panel">
      {/* ── Header row ─────────────────────────────────────────────────────── */}
      <div className="dashboard-header">
        <div>
          <h1 className="display-md">Dashboard</h1>
          <p className="caption" style={{ marginTop: 'var(--spacing-xxs)' }}>
            Real-time operator view of component health and status.
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="btn-secondary"
          style={{ padding: '10px 16px', fontSize: '14px' }}
          aria-label="Refresh component statuses"
        >
          Refresh
        </button>
      </div>

      {/* ── Content branch ─────────────────────────────────────────────────── */}
      {loading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorPanel message={error} onRetry={handleRefresh} />
      ) : data.length === 0 ? (
        <EmptyState />
      ) : (
        <ComponentTable components={data} />
      )}
    </div>
  );
}

export default Dashboard;
