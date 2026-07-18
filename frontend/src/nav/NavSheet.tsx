import { useEffect, useRef } from 'react'
import type { RefObject } from 'react'
import { Icon } from '../components'
import { TabNav } from './TabNav'
import './NavSheet.css'

export interface NavSheetProps {
  open: boolean
  onClose: () => void
  /** The hamburger trigger in `CommandBar` — focus returns here on close. */
  triggerRef: RefObject<HTMLButtonElement | null>
}

const FOCUSABLE_SELECTOR = 'a[href], button:not([disabled])'

/**
 * Mobile (<=768px) overlay nav sheet (STORY-104 AC4, ported from
 * `ui-redesign`'s `SidebarDrawer` focus-trap contract — salvage list),
 * dropping down from under the command bar and wrapping the SAME `TabNav`
 * the desktop bar uses (vertical layout via `tab-nav--sheet`) rather than
 * a left rail — this IA has no sidebar at all (design brief §IA). Closed
 * by default: while `open` is false this renders nothing at all (not
 * hidden via CSS), so nothing here — scrim, Escape listener, focus trap —
 * is ever live unless a dialog is genuinely mounted.
 *
 * `TabNav`'s `onNavigate` prop is wired to `onClose`: without it,
 * activating a nav link would navigate correctly but leave the sheet open
 * over the destination page (the same 2026-07-17 reality-gate finding the
 * ported `SidebarDrawer` fixed). Focus management mirrors the ported
 * contract: move focus into the sheet's first focusable element on open
 * (the header's close button); return it to the trigger once `open`
 * transitions back to false, regardless of what closed it (Escape, scrim
 * click, the close button, or a nav-link activation).
 */
export function NavSheet({ open, onClose, triggerRef }: NavSheetProps) {
  const sheetRef = useRef<HTMLDivElement>(null)
  const wasOpen = useRef(false)

  useEffect(() => {
    if (open) {
      const firstFocusable = sheetRef.current?.querySelector<HTMLElement>(
        FOCUSABLE_SELECTOR,
      )
      firstFocusable?.focus()
    } else if (wasOpen.current) {
      triggerRef.current?.focus()
    }
    wasOpen.current = open
  }, [open, triggerRef])

  // Escape-close + a same-sheet Tab focus trap so keyboard focus never
  // silently escapes into the page content behind the scrim.
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

      const focusables = sheetRef.current?.querySelectorAll<HTMLElement>(
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
      <div className="nav-sheet__scrim" onClick={onClose} />
      <div
        className="nav-sheet"
        ref={sheetRef}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation"
      >
        <div className="nav-sheet__header">
          <span className="nav-sheet__brand">
            <Icon name="logo" />
            Uptime Monitor
          </span>
          <button
            type="button"
            className="nav-sheet__close"
            onClick={onClose}
            aria-label="Close navigation"
          >
            <Icon name="x" />
          </button>
        </div>
        <TabNav className="tab-nav--sheet" onNavigate={onClose} />
      </div>
    </>
  )
}
