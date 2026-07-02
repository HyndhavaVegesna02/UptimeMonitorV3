import { Route, Routes } from 'react-router-dom'
import { Nav } from './nav/Nav'
import { DashboardPage } from './pages/DashboardPage'
import { AvailabilityPage } from './pages/AvailabilityPage'
import { ApprovalsPage } from './pages/ApprovalsPage'
import { CheckHistoryPage } from './pages/CheckHistoryPage'
import { MaintenancePage } from './pages/MaintenancePage'
import { PublicationsPage } from './pages/PublicationsPage'
import './AppShell.css'

/** The routed shell: Nav + one route per tab (STORY-015a AC2). Router-agnostic
 * so tests can wrap it in a MemoryRouter without pulling in BrowserRouter. */
export function AppShell() {
  return (
    <>
      <Nav />
      <main className="app-shell__main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/availability" element={<AvailabilityPage />} />
          <Route path="/approvals" element={<ApprovalsPage />} />
          <Route path="/check-history" element={<CheckHistoryPage />} />
          <Route path="/maintenance" element={<MaintenancePage />} />
          <Route path="/publications" element={<PublicationsPage />} />
        </Routes>
      </main>
    </>
  )
}
