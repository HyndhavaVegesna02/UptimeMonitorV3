import { NavLink } from 'react-router-dom'
import { useTheme } from '../theme/useTheme'
import { TABS } from './tabs'
import './Nav.css'

/**
 * Persistent top navigation (STORY-015a AC2/AC5/AC6): app title left, the
 * six-tab IA (dossier §17), theme toggle right. 56px, canvas background,
 * hairline bottom border. Tabs are real routed links (not an ARIA tablist —
 * each one navigates to its own route, which is the correct semantic for
 * URL-addressable pages), so keyboard operability and focus rings come from
 * the browser's native anchor behavior plus the shared :focus-visible rule.
 */
export function Nav() {
  const { theme, toggleTheme } = useTheme()

  return (
    <nav className="nav" aria-label="Primary">
      <span className="nav__title">Uptime Monitor</span>
      <ul className="nav__tabs">
        {TABS.map((tab) => (
          <li key={tab.path}>
            <NavLink
              to={tab.path}
              end={tab.path === '/'}
              className={({ isActive }) =>
                isActive ? 'nav__tab-link nav__tab-link--active' : 'nav__tab-link'
              }
            >
              {tab.label}
            </NavLink>
          </li>
        ))}
      </ul>
      <button
        type="button"
        className="nav__toggle"
        onClick={toggleTheme}
        aria-label={
          theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'
        }
      >
        {theme === 'dark' ? '☀' : '☾'}
      </button>
    </nav>
  )
}
