import { useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Sidebar } from './nav/Sidebar'
import { TopBar } from './nav/TopBar'
import { persistExpanded, resolveInitialExpanded } from './nav/sidebarState'
import { useApprovalsBadge } from './features/shell/useApprovalsBadge'
import { DashboardPage } from './pages/DashboardPage'
import { AvailabilityPage } from './pages/AvailabilityPage'
import { ApprovalsPage } from './pages/ApprovalsPage'
import { CheckHistoryPage } from './pages/CheckHistoryPage'
import { MaintenancePage } from './pages/MaintenancePage'
import { PublicationsPage } from './pages/PublicationsPage'
import { NotFoundPage } from './pages/NotFoundPage'
import './AppShell.css'

/**
 * The routed shell (STORY-056): a collapsible left icon `Sidebar` + a
 * `TopBar` (theme toggle), wrapping one route per tab. Router-agnostic so
 * tests can wrap it in a `MemoryRouter` without pulling in `BrowserRouter`
 * (unchanged from STORY-015a). Used to also lift a load+mutate hook result
 * down to `TopBar`'s trigger and a dismissible warning banner (STORY-049,
 * relocated STORY-056); both were removed by STORY-155a — see that story's
 * History for what was here.
 */
export function AppShell() {
  const [expanded, setExpanded] = useState(() => resolveInitialExpanded())
  const pendingApprovals = useApprovalsBadge()

  const toggleExpanded = () => {
    setExpanded((current) => {
      const next = !current
      persistExpanded(next)
      return next
    })
  }

  return (
    <div className="app-shell">
      <a
        href="#main-content"
        className="skip-link"
        onClick={(event) => {
          const target = document.getElementById('main-content')
          if (target) {
            event.preventDefault()
            target.focus()
          }
        }}
      >
        Skip to main content
      </a>
      <Sidebar
        expanded={expanded}
        onToggleExpanded={toggleExpanded}
        pendingApprovals={pendingApprovals}
      />
      <div className="app-shell__content">
        <TopBar />
        <main id="main-content" className="app-shell__main" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/availability" element={<AvailabilityPage />} />
            <Route path="/approvals" element={<ApprovalsPage />} />
            <Route path="/check-history" element={<CheckHistoryPage />} />
            <Route path="/maintenance" element={<MaintenancePage />} />
            <Route path="/publications" element={<PublicationsPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
