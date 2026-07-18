import { Icon } from '../components'
import { TabNav } from './TabNav'
import './CommandBar.css'

/**
 * Slim top command bar (STORY-104 AC1, design brief §IA — replaces the
 * pre-rewrite left sidebar entirely): brand block on the left, the
 * horizontal `TabNav` in the middle (CSS-hidden at <=768px, replaced by a
 * hamburger sheet trigger — STORY-104 Step 4), and a right cluster of mode
 * controls (sample-mode switch/chip, theme toggle, last-updated — Step 3).
 * This is the Step-1 scaffold: brand + tab nav + an empty cluster region.
 */
export function CommandBar() {
  return (
    <header className="command-bar">
      <div className="command-bar__brand">
        <Icon name="logo" />
        <span className="command-bar__brand-text">Uptime Monitor</span>
      </div>
      <TabNav className="command-bar__nav" />
      <div className="command-bar__cluster" />
    </header>
  )
}
