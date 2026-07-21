import {
  CheckCircle,
  Question,
  Warning,
  WarningCircle,
  WarningOctagon,
  Wrench,
  XCircle,
} from '@phosphor-icons/react'
import type { Icon as PhosphorIcon } from '@phosphor-icons/react'
import type { HealthStatus } from '../components/StatusBadge/StatusBadge'

/**
 * One Phosphor icon per health status (STORY-121 AC3 — the topbar's
 * worst-of overall status pill is "dot + icon + text label", never colour
 * alone). Shared so any future health-status pill (STORY-122) uses the same
 * icon per status rather than re-choosing one per call site.
 */
export const HEALTH_ICONS: Record<HealthStatus, PhosphorIcon> = {
  up: CheckCircle,
  degraded: Warning,
  partial: WarningCircle,
  down: XCircle,
  maintenance: Wrench,
  unknown: Question,
  missing: WarningOctagon,
}
