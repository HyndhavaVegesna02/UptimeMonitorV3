import { Route, Routes } from 'react-router-dom'
import { Icon } from './components'
import { TABS } from './nav/tabs'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { useTheme } from './theme/useTheme'
import './AppShell.css'

/**
 * The minimal rewrite-in-progress shell (STORY-103 AC5): a top-bar stub
 * (brand + theme toggle) and a routed `<main>` rendering one placeholder
 * `Tile` per tab, all on the new Mission Teal tokens. The old sidebar +
 * top-bar + sample-mode-banner shell (and every page it wrapped) is
 * deliberately DEAD on this branch — STORY-104 builds the real top
 * command bar + horizontal tab nav; the pages return per-tab in the
 * stories that follow it (sprint-56+).
 */
export function AppShell() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

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
      <header className="app-shell__topbar">
        <span className="app-shell__brand">
          <Icon name="logo" />
          Uptime Monitor
        </span>
        <button
          type="button"
          className="app-shell__theme-toggle"
          onClick={toggleTheme}
          aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          <Icon name={isDark ? 'moon' : 'sun'} title={isDark ? 'Dark theme' : 'Light theme'} />
        </button>
      </header>
      <main id="main-content" className="app-shell__main" tabIndex={-1}>
        <Routes>
          {TABS.map((tab) => (
            <Route
              key={tab.path}
              path={tab.path}
              element={<PlaceholderPage title={tab.label} />}
            />
          ))}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  )
}
