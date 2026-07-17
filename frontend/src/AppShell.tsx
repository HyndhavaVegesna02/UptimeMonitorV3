import { useRef } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Sidebar } from './nav/Sidebar'
import { SidebarDrawer } from './nav/SidebarDrawer'
import { TopBar } from './nav/TopBar'
import { SampleModeBanner } from './nav/SampleModeBanner'
import { useResponsiveSidebar } from './nav/useResponsiveSidebar'
import { useApprovalsBadge } from './features/shell/useApprovalsBadge'
import { useSampleMode } from './features/dashboard/useSampleMode'
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
 * `TopBar` (theme toggle + the relocated sample-mode trigger) + a
 * dismissible `SampleModeBanner`, wrapping one route per tab. Router-
 * agnostic so tests can wrap it in a `MemoryRouter` without pulling in
 * `BrowserRouter` (unchanged from STORY-015a).
 *
 * `useSampleMode()` is called ONCE here and its result is passed down to
 * both `TopBar` (the trigger) and `SampleModeBanner` (via the derived
 * `visible` boolean) — a single source of truth, so a toggle in the top
 * bar is guaranteed to be reflected in the banner on the very same render
 * (two independent hook instances would each run their own GET/override
 * cycle and could disagree — see `TopBar.tsx`'s header comment).
 *
 * `useResponsiveSidebar()` (STORY-096) is the other single source of truth
 * this shell lifts once: `isMobile` decides whether the persistent
 * `Sidebar` or the overlay `SidebarDrawer` renders AND whether `TopBar`
 * shows its hamburger trigger, so those three can never disagree about
 * whether a drawer exists to open.
 */
export function AppShell() {
  const pendingApprovals = useApprovalsBadge()
  const sampleMode = useSampleMode()
  const { isMobile, expanded, toggleExpanded, drawerOpen, openDrawer, closeDrawer } =
    useResponsiveSidebar()
  const menuTriggerRef = useRef<HTMLButtonElement>(null)

  const bannerVisible = sampleMode.state.phase === 'success' && sampleMode.enabled === true

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
      {isMobile ? (
        <SidebarDrawer
          open={drawerOpen}
          onClose={closeDrawer}
          triggerRef={menuTriggerRef}
          pendingApprovals={pendingApprovals}
        />
      ) : (
        <Sidebar
          expanded={expanded}
          onToggleExpanded={toggleExpanded}
          pendingApprovals={pendingApprovals}
        />
      )}
      <div className="app-shell__content">
        <TopBar
          sampleMode={sampleMode}
          showMenuTrigger={isMobile}
          onOpenMenu={openDrawer}
          menuTriggerRef={menuTriggerRef}
        />
        <SampleModeBanner visible={bannerVisible} />
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
