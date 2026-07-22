import { useCallback, useId, useRef, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { getApprovals, getComponents } from '../api/client'
import { deriveOverallStatus } from '../lib/overallStatus'
import { useFetch } from '../lib/useFetch'
import { getTabByPath } from '../nav/tabs'
import { Sidebar } from './Sidebar/Sidebar'
import { Topbar } from './Topbar/Topbar'
import './ShellLayout.css'
import { useSidebarCollapse } from './useSidebarCollapse'

/**
 * The app frame (STORY-121): grouped `Sidebar` + status-aware `Topbar`
 * around the six operator tabs, rendered as a React Router LAYOUT route
 * (`<Outlet />` renders whichever child route matched — `App.tsx` owns the
 * routing table). `/styleguide` is deliberately a SIBLING top-level route,
 * not a child of this layout — it is a standalone design-system gallery
 * with its own `<h1>Design system</h1>`, and nesting it here would double
 * up on the Topbar's own page-title `<h1>`.
 *
 * Fetches `components`/`approvals` ONCE here and passes the results down to
 * both `Sidebar` (Pinned quick-links, Approvals badge) and `Topbar`
 * (worst-of overall status) — a single network round-trip per endpoint
 * rather than each shell piece independently re-fetching the same data
 * (vercel-react-best-practices: no duplicate/waterfall fetches).
 */
export function ShellLayout() {
  const { collapsed, toggle: toggleCollapsed } = useSidebarCollapse()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const mobileToggleRef = useRef<HTMLButtonElement>(null)
  const sidebarNavId = useId()
  const location = useLocation()

  const componentsFetch = useFetch(getComponents)
  const approvalsFetch = useFetch(getApprovals)

  const components = componentsFetch.state.phase === 'success' ? componentsFetch.state.data : []
  const approvalsCount =
    approvalsFetch.state.phase === 'success' ? approvalsFetch.state.data.length : 0
  // `null` while the components fetch hasn't SUCCEEDED yet (loading OR
  // error) — the topbar renders a neutral loading treatment for that, never
  // `deriveOverallStatus([])`'s `unknown` (STORY-136 AC2: `unknown` must only
  // render for a fetch that genuinely SUCCEEDED with no components to judge).
  const overallStatus =
    componentsFetch.state.phase === 'success' ? deriveOverallStatus(componentsFetch.state.data) : null

  // Quality-review fix: `succeededAt` is captured by `useFetch` itself
  // inside the fetch promise's own `.then()` callback — not `new Date()`
  // read fresh on every ShellLayout render (which made the topbar's
  // last-updated indicator always read "just now", no matter how much real
  // time had actually passed since the last load). An unrelated re-render
  // (collapse toggle, approvals fetch settling, route change) leaves it
  // untouched.
  const lastUpdated = componentsFetch.succeededAt

  const pageTitle = getTabByPath(location.pathname)?.label ?? 'Dashboard'

  const openMobileNav = useCallback(() => setMobileNavOpen(true), [])
  const closeMobileNav = useCallback(() => {
    setMobileNavOpen(false)
    mobileToggleRef.current?.focus()
  }, [])

  return (
    <div className="shell">
      <Sidebar
        navId={sidebarNavId}
        collapsed={collapsed}
        onToggleCollapsed={toggleCollapsed}
        activePath={location.pathname}
        approvalsCount={approvalsCount}
        components={components}
        mobileOpen={mobileNavOpen}
        onCloseMobile={closeMobileNav}
      />
      <div className="shell__content">
        <Topbar
          title={pageTitle}
          overallStatus={overallStatus}
          lastUpdated={lastUpdated}
          now={new Date()}
          mobileNavOpen={mobileNavOpen}
          mobileNavId={sidebarNavId}
          onOpenMobileNav={openMobileNav}
          mobileToggleRef={mobileToggleRef}
        />
        <main id="main-content" className="shell__main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
