import { Bell } from '@phosphor-icons/react'
import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { Button } from '../../components/Button/Button'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { Icon } from '../../components/Icon/Icon'
import { Panel } from '../../components/Panel/Panel'
import './NotificationsButton.css'

/**
 * The topbar's notifications control (STORY-141 AC1) — previously a dead
 * icon-only button with no `onClick`/panel (`Topbar.tsx:71`, confirmed live
 * at the 2026-07-22 design-QA review). A fresh, minimal, extensible
 * disclosure popover, not a stub: the trigger wires `aria-haspopup` +
 * `aria-expanded` + `aria-controls` to the panel; opening moves focus INTO
 * the panel, Escape (or an outside click) closes it and returns focus to
 * the trigger — mirroring the mobile sheet's own close-and-refocus
 * convention (`ShellLayout.tsx::closeMobileNav`). There is no notifications
 * data source in scope yet, so the panel's only content is an explicit "No
 * notifications" empty state — deliberately not fabricated data.
 */
export function NotificationsButton() {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const panelId = useId()

  const close = useCallback(() => {
    setOpen(false)
    containerRef.current
      ?.querySelector<HTMLButtonElement>('.notifications-button__trigger')
      ?.focus()
  }, [])

  useEffect(() => {
    if (!open) {
      return
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        close()
      }
    }

    function onPointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        close()
      }
    }

    document.addEventListener('keydown', onKeyDown)
    document.addEventListener('mousedown', onPointerDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.removeEventListener('mousedown', onPointerDown)
    }
  }, [open, close])

  useEffect(() => {
    if (open) {
      containerRef.current?.querySelector<HTMLElement>('[role="dialog"]')?.focus()
    }
  }, [open])

  return (
    <div className="notifications-button" ref={containerRef}>
      <Button
        variant="ghost"
        iconOnly
        aria-label="Notifications"
        className="notifications-button__trigger"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
      >
        <Icon icon={Bell} aria-hidden />
      </Button>
      {open ? (
        <Panel
          id={panelId}
          role="dialog"
          aria-label="Notifications"
          tabIndex={-1}
          className="notifications-button__panel"
        >
          <EmptyState message="No notifications" />
        </Panel>
      ) : null}
    </div>
  )
}
