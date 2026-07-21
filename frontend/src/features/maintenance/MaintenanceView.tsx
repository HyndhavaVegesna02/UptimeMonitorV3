import { useState, useCallback, useMemo } from 'react'
import {
  deleteMaintenance,
  getComponents,
  getMaintenance,
  postMaintenance,
  ApiError,
} from '../../api/client'
import type { MaintenanceWindowDTO } from '../../api/types'
import { Button } from '../../components/Button/Button'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { useFetch } from '../../lib/useFetch'
import { deriveMaintenanceStatus } from './deriveMaintenanceStatus'

interface MaintenanceWindowCardProps {
  windowItem: MaintenanceWindowDTO
  componentName: string
  onRefreshNeeded: () => void
}

function MaintenanceWindowCard({
  windowItem,
  componentName,
  onRefreshNeeded,
}: MaintenanceWindowCardProps) {
  const [deleteMode, setDeleteMode] = useState<'idle' | 'confirming' | 'submitting'>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const statusKind = deriveMaintenanceStatus(windowItem.starts_at, windowItem.ends_at)

  const handleDelete = async () => {
    setDeleteMode('submitting')
    setErrorMessage(null)
    try {
      await deleteMaintenance(windowItem.id)
      onRefreshNeeded()
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 404) {
          setErrorMessage('Maintenance window no longer exists.')
          onRefreshNeeded()
          return
        }
        setErrorMessage(err.detail ?? err.message)
      } else {
        setErrorMessage((err as Error).message ?? 'Failed to delete maintenance window.')
      }
      setDeleteMode('idle')
    }
  }

  return (
    <Panel title={windowItem.title || componentName}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 'var(--font-xs)',
              color: 'var(--color-text-secondary)',
              backgroundColor: 'var(--color-bg-subtle)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            Component: {componentName}
          </span>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
            {statusKind === 'active' && <StatusBadge status="maintenance" label="Active" />}
            {statusKind === 'upcoming' && (
              <span
                style={{
                  fontSize: 'var(--font-xs)',
                  fontWeight: 'var(--font-weight-medium)',
                  backgroundColor: 'var(--color-bg-subtle)',
                  color: 'var(--color-text-primary)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                }}
              >
                Upcoming
              </span>
            )}
            {statusKind === 'past' && (
              <span
                style={{
                  fontSize: 'var(--font-xs)',
                  color: 'var(--color-text-secondary)',
                  backgroundColor: 'var(--color-bg-subtle)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                Past
              </span>
            )}
          </div>
        </div>

        {windowItem.reason && (
          <p style={{ margin: 0, fontSize: 'var(--font-sm)', color: 'var(--color-text-secondary)' }}>
            {windowItem.reason}
          </p>
        )}

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 'var(--space-sm)',
            backgroundColor: 'var(--color-bg-subtle)',
            padding: 'var(--space-sm) var(--space-md)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-xs)',
          }}
        >
          <div>
            <div style={{ color: 'var(--color-text-secondary)' }}>Starts At (UTC)</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 'var(--font-weight-medium)' }}>
              {new Date(windowItem.starts_at).toUTCString()}
            </div>
          </div>
          <div>
            <div style={{ color: 'var(--color-text-secondary)' }}>Ends At (UTC)</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 'var(--font-weight-medium)' }}>
              {new Date(windowItem.ends_at).toUTCString()}
            </div>
          </div>
        </div>

        {errorMessage && (
          <div
            role="alert"
            style={{
              padding: 'var(--space-xs) var(--space-sm)',
              backgroundColor: 'var(--color-health-down-bg)',
              color: 'var(--color-health-down-text)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-xs)',
            }}
          >
            {errorMessage}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-sm)' }}>
          {deleteMode === 'idle' && (
            <Button
              variant="ghost"
              onClick={() => setDeleteMode('confirming')}
            >
              Delete Window
            </Button>
          )}

          {deleteMode === 'confirming' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
              <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
                Confirm delete?
              </span>
              <Button variant="secondary" onClick={handleDelete}>
                Confirm Delete
              </Button>
              <Button variant="ghost" onClick={() => setDeleteMode('idle')}>
                Cancel
              </Button>
            </div>
          )}

          {deleteMode === 'submitting' && (
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
              Deleting window…
            </span>
          )}
        </div>
      </div>
    </Panel>
  )
}

export function MaintenanceView() {
  const [componentId, setComponentId] = useState<string>('')
  const [title, setTitle] = useState('')
  const [reason, setReason] = useState('')
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')

  const [fieldErrors, setFieldErrors] = useState<{
    component_id?: string
    starts_at?: string
    ends_at?: string
  }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const fetcher = useCallback(async () => {
    const [windows, components] = await Promise.all([
      getMaintenance(),
      getComponents(),
    ])
    const compMap = new Map(components.map((c) => [c.id, c.name]))
    return { windows, components, compMap }
  }, [])

  const { state, retry } = useFetch(fetcher)

  const loading = state.phase === 'loading'
  const error = state.phase === 'error' ? state : null
  const windows = state.phase === 'success' ? state.data.windows : undefined
  const components = state.phase === 'success' ? state.data.components : undefined
  const compMap = state.phase === 'success' ? state.data.compMap : undefined

  // Set default component selection when components arrive
  const defaultCompId = useMemo(() => {
    if (components && components.length > 0) {
      return components[0].id
    }
    return ''
  }, [components])

  const selectedCompId = componentId || defaultCompId

  const handleSchedule = async (e: React.FormEvent) => {
    e.preventDefault()
    setFieldErrors({})
    setFormError(null)

    if (!selectedCompId) {
      setFieldErrors({ component_id: 'Component selection is required' })
      return
    }
    if (!startsAt) {
      setFieldErrors({ starts_at: 'Start time is required' })
      return
    }
    if (!endsAt) {
      setFieldErrors({ ends_at: 'End time is required' })
      return
    }

    const startDate = new Date(startsAt)
    const endDate = new Date(endsAt)

    if (endDate <= startDate) {
      setFieldErrors({ ends_at: 'End time must be strictly greater than start time' })
      return
    }

    setSubmitting(true)
    try {
      await postMaintenance({
        component_id: selectedCompId,
        starts_at: startDate.toISOString(),
        ends_at: endDate.toISOString(),
        title: title.trim() ? title.trim() : null,
        reason: reason.trim() ? reason.trim() : null,
      })
      setTitle('')
      setReason('')
      setStartsAt('')
      setEndsAt('')
      retry()
    } catch (err) {
      if (err instanceof ApiError) {
        const detailStr = (err.detail ?? err.message).toLowerCase()
        const errorsObj: typeof fieldErrors = {}

        // STORY-132 strict 422 field mapping order:
        // 1. "strictly greater than" -> ends_at (FIRST)
        // 2. "component_id" -> component_id
        // 3. "starts_at" -> starts_at
        // 4. "ends_at" -> ends_at
        if (detailStr.includes('strictly greater than')) {
          errorsObj.ends_at = err.detail ?? 'End time must be strictly greater than start time'
        } else if (detailStr.includes('component_id')) {
          errorsObj.component_id = err.detail ?? 'Invalid component'
        } else if (detailStr.includes('starts_at')) {
          errorsObj.starts_at = err.detail ?? 'Invalid start time'
        } else if (detailStr.includes('ends_at')) {
          errorsObj.ends_at = err.detail ?? 'Invalid end time'
        } else {
          setFormError(err.detail ?? err.message)
        }

        setFieldErrors(errorsObj)
      } else {
        setFormError((err as Error).message ?? 'Failed to schedule maintenance window.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      <p
        style={{
          fontSize: 'var(--font-sm)',
          color: 'var(--color-text-secondary)',
          margin: 0,
        }}
      >
        Schedule and manage planned component maintenance windows.
      </p>

      <Panel title="Schedule Maintenance Window">
        <form
          onSubmit={handleSchedule}
          style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}
        >
          {formError && (
            <div
              role="alert"
              style={{
                padding: 'var(--space-sm) var(--space-md)',
                backgroundColor: 'var(--color-health-down-bg)',
                color: 'var(--color-health-down-text)',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--font-sm)',
              }}
            >
              {formError}
            </div>
          )}

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: 'var(--space-md)',
            }}
          >
            <div>
              <label
                htmlFor="maintenance-component-select"
                style={{
                  display: 'block',
                  fontSize: 'var(--font-xs)',
                  color: 'var(--color-text-secondary)',
                  marginBottom: '4px',
                }}
              >
                Component
              </label>
              <select
                id="maintenance-component-select"
                value={selectedCompId}
                onChange={(e) => setComponentId(e.target.value)}
                style={{
                  width: '100%',
                  padding: 'var(--space-xs) var(--space-sm)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg)',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--font-sm)',
                }}
              >
                {components?.map((comp) => (
                  <option key={comp.id} value={comp.id}>
                    {comp.name} ({comp.id})
                  </option>
                ))}
              </select>
              {fieldErrors.component_id && (
                <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-health-down-text)' }}>
                  {fieldErrors.component_id}
                </span>
              )}
            </div>

            <div>
              <label
                htmlFor="maintenance-title-input"
                style={{
                  display: 'block',
                  fontSize: 'var(--font-xs)',
                  color: 'var(--color-text-secondary)',
                  marginBottom: '4px',
                }}
              >
                Title (optional)
              </label>
              <input
                id="maintenance-title-input"
                type="text"
                placeholder="e.g. Database engine upgrade"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{
                  width: '100%',
                  padding: 'var(--space-xs) var(--space-sm)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg)',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--font-sm)',
                }}
              />
            </div>

            <div>
              <label
                htmlFor="maintenance-starts-at-input"
                style={{
                  display: 'block',
                  fontSize: 'var(--font-xs)',
                  color: 'var(--color-text-secondary)',
                  marginBottom: '4px',
                }}
              >
                Starts At
              </label>
              <input
                id="maintenance-starts-at-input"
                type="datetime-local"
                value={startsAt}
                onChange={(e) => setStartsAt(e.target.value)}
                style={{
                  width: '100%',
                  padding: 'var(--space-xs) var(--space-sm)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg)',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--font-sm)',
                }}
              />
              {fieldErrors.starts_at && (
                <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-health-down-text)' }}>
                  {fieldErrors.starts_at}
                </span>
              )}
            </div>

            <div>
              <label
                htmlFor="maintenance-ends-at-input"
                style={{
                  display: 'block',
                  fontSize: 'var(--font-xs)',
                  color: 'var(--color-text-secondary)',
                  marginBottom: '4px',
                }}
              >
                Ends At
              </label>
              <input
                id="maintenance-ends-at-input"
                type="datetime-local"
                value={endsAt}
                onChange={(e) => setEndsAt(e.target.value)}
                style={{
                  width: '100%',
                  padding: 'var(--space-xs) var(--space-sm)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg)',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--font-sm)',
                }}
              />
              {fieldErrors.ends_at && (
                <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-health-down-text)' }}>
                  {fieldErrors.ends_at}
                </span>
              )}
            </div>
          </div>

          <div>
            <label
              htmlFor="maintenance-reason-input"
              style={{
                display: 'block',
                fontSize: 'var(--font-xs)',
                color: 'var(--color-text-secondary)',
                marginBottom: '4px',
              }}
            >
              Reason / Impact Notes (optional)
            </label>
            <textarea
              id="maintenance-reason-input"
              rows={2}
              placeholder="Describe planned work and expected customer impact…"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              style={{
                width: '100%',
                padding: 'var(--space-xs) var(--space-sm)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-sm)',
                resize: 'vertical',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? 'Scheduling…' : 'Schedule Window'}
            </Button>
          </div>
        </form>
      </Panel>

      {loading && <LoadingState label="Loading maintenance windows…" />}

      {error && (
        <ErrorState
          message={error.message ?? 'Failed to load maintenance windows'}
          onRetry={retry}
        />
      )}

      {!loading && !error && windows && windows.length === 0 && (
        <EmptyState message="No scheduled maintenance windows." />
      )}

      {!loading && !error && windows && windows.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          <h2
            style={{
              fontSize: 'var(--font-lg)',
              fontWeight: 'var(--font-weight-semibold)',
              margin: 0,
            }}
          >
            Scheduled Windows ({windows.length})
          </h2>
          {windows.map((win) => (
            <MaintenanceWindowCard
              key={win.id}
              windowItem={win}
              componentName={compMap?.get(win.component_id) ?? win.component_id}
              onRefreshNeeded={retry}
            />
          ))}
        </div>
      )}
    </div>
  )
}
