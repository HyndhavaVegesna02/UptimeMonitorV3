import { Navigate, Route, Routes } from 'react-router-dom'
import { StyleguidePage } from './pages/StyleguidePage/StyleguidePage'
import './AppShell.css'

/**
 * Minimal application frame (STORY-120). The full grouped sidebar + topbar
 * shell (collapsible rail, routing to the six tabs) is built in STORY-121;
 * this is just enough of a mount point to make the design-system gallery
 * (`/styleguide`) reachable in the running app.
 */
export function AppShell() {
  return (
    <div className="app-shell">
      <main id="main-content" className="app-shell__main">
        <Routes>
          <Route path="/" element={<Navigate to="/styleguide" replace />} />
          <Route path="/styleguide" element={<StyleguidePage />} />
          <Route path="*" element={<Navigate to="/styleguide" replace />} />
        </Routes>
      </main>
    </div>
  )
}
