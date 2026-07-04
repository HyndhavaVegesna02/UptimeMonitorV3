import type { ComponentTopologyDTO, TopologySignalDTO } from '../../api/types'

/** A selectable signal option (STORY-015e AC1) — a `TopologySignalDTO` plus
 * the name of the component it belongs to, for a labeled selector entry. */
export interface SignalOption extends TopologySignalDTO {
  componentName: string
}

/**
 * Flattens the topology's nested components -> signals structure into a
 * flat, selectable list (STORY-015e AC1) — reuses the EXISTING
 * `GET /api/v1/topology` shape (STORY-044/015d) rather than adding a new
 * signal-enumeration endpoint. Order is preserved: components in the
 * topology response's own order, each component's own `signals` in their
 * (server-sorted) order — the first entry is the tab's default selection.
 */
export function flattenSignals(topology: ComponentTopologyDTO[]): SignalOption[] {
  return topology.flatMap((component) =>
    component.signals.map((signal) => ({ ...signal, componentName: component.name })),
  )
}
