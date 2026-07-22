import type { KeyboardEvent } from 'react'
import { useEffect, useRef } from 'react'
import type { MaintenanceWindowDTO } from '../../api/types'
import { Button } from '../../components/Button/Button'
import { Panel } from '../../components/Panel/Panel'
import { deriveMaintenanceWindowState } from './deriveWindowState'
import { formatWindowRange } from './formatWindowRange'
import type { DeletionNotice } from './useMaintenanceDeletion'
import { WindowStateBadge } from './WindowStateBadge'
import './MaintenanceWindowCard.css'

export interface MaintenanceWindowCardProps {
  window: MaintenanceWindowDTO
  /** "What time is it right now", read once at the page level (same
   * discipline as `DashboardPage`/`ApprovalsPage`'s `now={new Date()}`) —
   * never `new Date()` read inside a presentational component. */
  now: Date
  isConfirming: boolean
  isSubmitting: boolean
  /** True while a DIFFERENT window is mid-deletion. */
  isBlocked: boolean
  notice?: DeletionNotice
  onRequestConfirm: () => void
  onCancelConfirm: () => void
  onConfirmDelete: () => void
}

/**
 * One scheduled maintenance window (STORY-132 AC1/AC4) — title (tidy
 * fallback when null), the client-derived upcoming/active/past badge,
 * component, UTC range, and reason (an em dash when null, never a blank
 * line) — plus the delete action's inline two-step confirm. The delete
 * trigger stays mounted (only disabled) while confirming/submitting rather
 * than being replaced, so a single stable ref is enough to restore focus
 * after Cancel — unlike Approvals' two-trigger (Approve/Reject) card, there
 * is no ambiguity about which button to refocus.
 */
export function MaintenanceWindowCard({
  window,
  now,
  isConfirming,
  isSubmitting,
  isBlocked,
  notice,
  onRequestConfirm,
  onCancelConfirm,
  onConfirmDelete,
}: MaintenanceWindowCardProps) {
  const deleteButtonRef = useRef<HTMLButtonElement>(null)
  const confirmButtonRef = useRef<HTMLButtonElement>(null)
  const pendingRefocus = useRef(false)

  const state = deriveMaintenanceWindowState(window, now)
  const title = window.title ?? 'Maintenance window'

  // Focus moves TO the Confirm button the instant the two-step prompt opens
  // (mirrors ApprovalsPage's AC7 focus discipline).
  useEffect(() => {
    if (isConfirming) {
      confirmButtonRef.current?.focus()
    }
  }, [isConfirming])

  // Focus returns to the (still-mounted) Delete trigger, but ONLY after an
  // explicit cancel — a resolved deletion removes the window from the list
  // on refresh, so there is nothing left to refocus.
  useEffect(() => {
    if (!isConfirming && !isSubmitting && pendingRefocus.current) {
      pendingRefocus.current = false
      deleteButtonRef.current?.focus()
    }
  }, [isConfirming, isSubmitting])

  function handleCancel() {
    pendingRefocus.current = true
    onCancelConfirm()
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      handleCancel()
    }
  }

  const showGoneNotice = notice && notice.kind === 'gone' ? notice : undefined
  const showErrorNotice = notice && notice.kind === 'error' ? notice : undefined
  const showConfirmBlock = isConfirming || isSubmitting

  return (
    <Panel headingLevel="h3" title={title} className="maintenance-window-card">
      <div className="maintenance-window-card__meta">
        <WindowStateBadge state={state} />
        <span className="maintenance-window-card__component">{window.component_id}</span>
      </div>

      <time className="maintenance-window-card__range" dateTime={window.starts_at}>
        {formatWindowRange(window.starts_at, window.ends_at)}
      </time>

      <p className="maintenance-window-card__reason">{window.reason ?? '—'}</p>

      {showGoneNotice ? (
        <p className="maintenance-window-card__notice maintenance-window-card__notice--info" role="status">
          {showGoneNotice.message}
        </p>
      ) : null}

      {showConfirmBlock ? (
        <div className="maintenance-window-card__confirm" onKeyDown={handleKeyDown}>
          {showErrorNotice ? (
            <p className="maintenance-window-card__notice maintenance-window-card__notice--error" role="alert">
              {showErrorNotice.message}
            </p>
          ) : (
            <p className="maintenance-window-card__confirm-prompt">Delete this maintenance window?</p>
          )}
          <div className="maintenance-window-card__actions">
            <button
              ref={confirmButtonRef}
              type="button"
              className="button button--primary"
              disabled={isSubmitting}
              onClick={onConfirmDelete}
            >
              {isSubmitting ? 'Deleting…' : showErrorNotice ? 'Retry' : 'Confirm delete'}
            </button>
            <Button variant="ghost" disabled={isSubmitting} onClick={handleCancel}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="maintenance-window-card__actions">
          {/* A plain native button (not the shared `Button` primitive, which
             doesn't forward refs — same reasoning as ProposalCard's confirm
             button) so this is a stable imperative refocus target. Same
             visual classes `Button` itself applies. */}
          <button
            ref={deleteButtonRef}
            type="button"
            className="button button--secondary maintenance-window-card__delete-button"
            disabled={isBlocked}
            aria-label={`Delete ${title}`}
            onClick={onRequestConfirm}
          >
            Delete
          </button>
        </div>
      )}
    </Panel>
  )
}
