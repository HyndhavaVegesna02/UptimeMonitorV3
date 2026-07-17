import { useEffect, useRef } from 'react'
import type { RefObject } from 'react'
import { Sidebar } from './Sidebar'
import './SidebarDrawer.css'

export interface SidebarDrawerProps {
  open: boolean
  onClose: () => void
  /** The hamburger trigger in `TopBar` — focus returns here on close
   * (STORY-096 AC2). */
  triggerRef: RefObject<HTMLButtonElement | null>
  pendingApprovals: number | undefined
}

const FOCUSABLE_SELECTOR = 'a[href], button:not([disabled])'

/**
 * Mobile (<=768px) overlay nav drawer (STORY-096 AC2, journal D2), wrapping
 * the SAME `Sidebar` used for the desktop rail in its `variant="drawer"`
 * mode (always full-labeled; its header closes the drawer instead of
 * collapsing — see `Sidebar.tsx`). Closed by default: while `open` is
 * false this renders nothing at all (not hidden via CSS), so nothing here
 * — scrim, Escape listener, focus trap — is ever live unless a dialog is
 * genuinely mounted, and the page content underneath is never narrowed by
 * it (AC2's "content >= 90% of viewport width" holds trivially since the
 * drawer is `position: fixed`, not part of flow, even while open).
 */
export function SidebarDrawer({
  open,
  onClose,
  triggerRef,
  pendingApprovals,
}: SidebarDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null)
  const wasOpen = useRef(false)

  // Focus management (AC2): move focus into the drawer's first focusable
  // element on open; return it to the trigger that opened it once `open`
  // transitions back to false (regardless of WHAT closed it — Escape,
  // scrim click, or the drawer's own header).
  useEffect(() => {
    if (open) {
      const firstFocusable = drawerRef.current?.querySelector<HTMLElement>(
        FOCUSABLE_SELECTOR,
      )
      firstFocusable?.focus()
    } else if (wasOpen.current) {
      triggerRef.current?.focus()
    }
    wasOpen.current = open
  }, [open, triggerRef])

  // Escape-close (AC2) + a same-drawer Tab focus trap so keyboard focus
  // never silently escapes into the page content behind the scrim.
  useEffect(() => {
    if (!open) {
      return undefined
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
        return
      }
      if (event.key !== 'Tab') {
        return
      }

      const focusables = drawerRef.current?.querySelectorAll<HTMLElement>(
        FOCUSABLE_SELECTOR,
      )
      if (!focusables || focusables.length === 0) {
        return
      }
      const first = focusables[0]
      const last = focusables[focusables.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  if (!open) {
    return null
  }

  return (
    <>
      <div className="sidebar-drawer__scrim" onClick={onClose} />
      <div
        className="sidebar-drawer"
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation"
      >
        <Sidebar
          variant="drawer"
          expanded
          onToggleExpanded={onClose}
          pendingApprovals={pendingApprovals}
        />
      </div>
    </>
  )
}
