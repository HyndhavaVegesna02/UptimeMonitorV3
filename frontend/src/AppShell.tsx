import { useRef } from 'react'
import { Route, Routes } from 'react-router-dom'
import { deriveOverallStatus } from './features/shell/deriveOverallStatus'
import { useComponents } from './features/dashboard/useComponents'
import { useSampleMode } from './features/dashboard/useSampleMode'
import { CommandBar } from './nav/CommandBar'
import { NavSheet } from './nav/NavSheet'
import { SampleModeBanner } from './nav/SampleModeBanner'
import { TABS } from './nav/tabs'
import { useDismissibleBanner } from './nav/useDismissibleBanner'
import { useNavSheet } from './nav/useNavSheet'
import { AvailabilityPage } from './pages/AvailabilityPage'
import { DashboardPage } from './pages/DashboardPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { NotFoundPage } from './pages/NotFoundPage'
import './AppShell.css'

/**
 * The routed shell (STORY-104, design brief §IA — the real top command bar
 * replacing STORY-103's minimal top-bar-stub placeholder): a slim
 * `CommandBar` (brand + live overall-status dot + horizontal `TabNav` +
 * the mode-controls right cluster), a dismissible `SampleModeBanner`, and
 * the mobile `NavSheet` overlay, wrapping one route per tab. Router-
 * agnostic so tests can wrap it in a `MemoryRouter` without pulling in
 * `BrowserRouter` (unchanged since STORY-015a).
 *
 * `useComponents()` and `useSampleMode()` are each called ONCE here and
 * threaded down as props — never called independently by a child — so
 * every consumer of a given fetch agrees about its current state on the
 * same render (see `CommandBar.tsx`'s prop doc-comments for why two
 * independent hook instances would desync). `overallStatus` (AC2) is
 * derived from the SAME `useComponents()` call the "Updated Xs ago" text
 * uses, so the dot and the timestamp can never describe two different
 * fetches.
 *
 * `useNavSheet()` is the other single source of truth lifted here:
 * `isMobile` decides whether `CommandBar` shows its hamburger trigger AND
 * whether the desktop tab nav or the `NavSheet` overlay is the reachable
 * one, so those two can never disagree about whether a sheet exists to
 * open.
 *
 * `useDismissibleBanner(bannerVisible)` is lifted the same way: the
 * persistent "SAMPLE" chip (shown once the banner is dismissed while the
 * flag is still ON) needs to read/drive the SAME dismissed flag the banner
 * itself does.
 */
export function AppShell() {
  const components = useComponents()
  const overallStatus =
    components.state.phase === 'success'
      ? deriveOverallStatus(components.state.data)
      : undefined

  const sampleMode = useSampleMode()
  const bannerVisible = sampleMode.state.phase === 'success' && sampleMode.enabled === true
  const { dismissed, dismiss, restore } = useDismissibleBanner(bannerVisible)

  const { isMobile, open, openSheet, closeSheet } = useNavSheet()
  const menuTriggerRef = useRef<HTMLButtonElement>(null)

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
      <CommandBar
        overallStatus={overallStatus}
        fetchedAtIso={components.fetchedAtIso}
        sampleMode={sampleMode}
        showSampleChip={bannerVisible && dismissed}
        onRestoreBanner={restore}
        showMenuTrigger={isMobile}
        onOpenMenu={openSheet}
        menuTriggerRef={menuTriggerRef}
      />
      <NavSheet open={open} onClose={closeSheet} triggerRef={menuTriggerRef} />
      <SampleModeBanner visible={bannerVisible} dismissed={dismissed} onDismiss={dismiss} />
      <main id="main-content" className="app-shell__main" tabIndex={-1}>
        <Routes>
          {TABS.map((tab) => (
            <Route
              key={tab.path}
              path={tab.path}
              element={
                tab.path === '/' ? (
                  <DashboardPage />
                ) : tab.path === '/availability' ? (
                  <AvailabilityPage />
                ) : (
                  <PlaceholderPage title={tab.label} />
                )
              }
            />
          ))}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  )
}
