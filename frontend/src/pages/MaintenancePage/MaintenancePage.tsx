import { getMaintenance } from '../../api/client'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { MaintenanceWindowCard } from '../../features/maintenance/MaintenanceWindowCard'
import { ScheduleMaintenanceForm } from '../../features/maintenance/ScheduleMaintenanceForm'
import { useMaintenanceDeletion } from '../../features/maintenance/useMaintenanceDeletion'
import { useFetch } from '../../lib/useFetch'
import './MaintenancePage.css'

/**
 * The Maintenance page (STORY-132) — schedule + delete maintenance windows,
 * the sprint's most complex mutation. Two independent regions per AC5: the
 * schedule form (its own `getComponents` fetch + submit state, entirely
 * inside `ScheduleMaintenanceForm`) and the windows list (`getMaintenance`,
 * fetched here). Both mutations reconcile the list from the server on a
 * genuinely settled outcome — `windowsFetch.retry` is passed to the form's
 * `onScheduled` and to `useMaintenanceDeletion`'s `onResolved` — never an
 * optimistic local edit. No `<h1>` here — `ShellLayout`'s `Topbar` already
 * owns the page's one top-level heading (same convention as
 * `ApprovalsPage`).
 */
export function MaintenancePage() {
  const windowsFetch = useFetch(getMaintenance)
  const deletion = useMaintenanceDeletion(windowsFetch.retry)

  // Fresh each render, like `ApprovalsPage`'s `now={new Date()}` — a "what
  // time is it right now" reference for deriving each window's state badge,
  // never a captured success timestamp.
  const now = new Date()

  return (
    <div className="maintenance-page">
      <p className="maintenance-page__description">
        Scheduled maintenance windows — upcoming, active, and past — suppress a component's status
        changes from availability and Statuspage while they run.
      </p>

      <Panel title="Schedule maintenance" headingLevel="h2" className="maintenance-page__form-panel">
        <ScheduleMaintenanceForm onScheduled={windowsFetch.retry} />
      </Panel>

      <section aria-labelledby="maintenance-page-list-heading" className="maintenance-page__list-section">
        <h2 id="maintenance-page-list-heading" className="maintenance-page__list-heading">
          Scheduled windows
        </h2>

        {windowsFetch.state.phase === 'loading' ? <LoadingState label="Loading maintenance windows…" /> : null}
        {windowsFetch.state.phase === 'error' ? (
          <ErrorState message={windowsFetch.state.message} onRetry={windowsFetch.retry} />
        ) : null}
        {windowsFetch.state.phase === 'success' ? (
          windowsFetch.state.data.length === 0 ? (
            <EmptyState
              message="No maintenance scheduled"
              detail="Windows you schedule above will show up here."
            />
          ) : (
            <div className="maintenance-page__list">
              {windowsFetch.state.data.map((window) => (
                <MaintenanceWindowCard
                  key={window.id}
                  window={window}
                  now={now}
                  isConfirming={deletion.isConfirming(window.id)}
                  isSubmitting={deletion.isSubmitting(window.id)}
                  isBlocked={deletion.isBlocked(window.id)}
                  notice={deletion.noticeFor(window.id)}
                  onRequestConfirm={() => deletion.requestConfirm(window.id)}
                  onCancelConfirm={deletion.cancelConfirm}
                  onConfirmDelete={() => {
                    void deletion.confirmDelete(window.id)
                  }}
                />
              ))}
            </div>
          )
        ) : null}
      </section>
    </div>
  )
}
