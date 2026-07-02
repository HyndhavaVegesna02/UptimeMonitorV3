import { Route, Routes } from 'react-router-dom'
import { Nav } from './nav/Nav'
import { DashboardPage } from './pages/DashboardPage'
import { AvailabilityPage } from './pages/AvailabilityPage'
import { ApprovalsPage } from './pages/ApprovalsPage'
import { CheckHistoryPage } from './pages/CheckHistoryPage'
import { MaintenancePage } from './pages/MaintenancePage'
import { PublicationsPage } from './pages/PublicationsPage'
import { NotFoundPage } from './pages/NotFoundPage'
import './AppShell.css'

/** The routed shell: Nav + one route per tab (STORY-015a AC2). Router-agnostic
 * so tests can wrap it in a MemoryRouter without pulling in BrowserRouter. */
export function AppShell() {
  return (
    <>
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
      <Nav />
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
    </>
  )
}
