import { Icon } from '../components'
import { useTheme } from '../theme/useTheme'
import './TopBar.css'

/**
 * Top bar (STORY-056 AC2): right-aligned, `--header-height` tall. Hosts the
 * theme toggle carried over from the old `Nav`. Used to also host a live
 * failure-trigger ⚡ switch (STORY-049, relocated STORY-056); removed by
 * STORY-155a — see that story's file under `docs/scrum/stories/` for what
 * was here.
 */
export function TopBar() {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="top-bar">
      <button
        type="button"
        className="top-bar__button"
        onClick={toggleTheme}
        aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        title="Toggle theme"
      >
        <Icon name={theme === 'light' ? 'sun' : 'moon'} />
      </button>
    </header>
  )
}
