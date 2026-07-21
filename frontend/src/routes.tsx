import { Navigate, Route, Routes } from 'react-router-dom'
import { ApprovalsPage } from './pages/ApprovalsPage/ApprovalsPage'
import { AvailabilityPage } from './pages/AvailabilityPage/AvailabilityPage'
import { DashboardPage } from './pages/DashboardPage/DashboardPage'
import { HistoryPage } from './pages/HistoryPage/HistoryPage'
import { MaintenancePage } from './pages/MaintenancePage/MaintenancePage'
import { PublicationsPage } from './pages/PublicationsPage/PublicationsPage'
import { StyleguidePage } from './pages/StyleguidePage/StyleguidePage'
import { ShellLayout } from './shell/ShellLayout'

/**
 * The app's routing table (STORY-121) — a `BrowserRouter` (`App.tsx`, prod)
 * or `MemoryRouter` (`ShellLayout.test.tsx`) supplies the Router; this
 * defines what renders at each path, so both share the exact same wiring
 * (checklist: composition/assembly tests construct the real wired objects).
 *
 * `/styleguide` is a standalone SIBLING route — it has its own
 * `<h1>Design system</h1>` and no shell chrome, deliberately not a child of
 * `ShellLayout` (nesting it would double up on the Topbar's page-title
 * `<h1>`). Every operator tab is a child of the `ShellLayout` LAYOUT route
 * (`<Outlet />`), so a page component never needs to know about the
 * sidebar/topbar rendered around it.
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/styleguide" element={<StyleguidePage />} />
      <Route element={<ShellLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="availability" element={<AvailabilityPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="approvals" element={<ApprovalsPage />} />
        <Route path="maintenance" element={<MaintenancePage />} />
        <Route path="publications" element={<PublicationsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}
