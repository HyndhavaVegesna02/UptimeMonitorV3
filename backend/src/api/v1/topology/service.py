"""Thin edge service for the topology feature (dossier §7, §9, §13, STORY-044 AC1).

Resolves `ComponentRepository`/`SignalRepository` via the container, groups
signals under their component, and shapes the DTO response — no business
logic here, the grouping is a pure read-shaping concern.
"""

from collections import defaultdict

from fastapi import Depends

from src.api.dependencies import get_component_repo, get_signal_repo
from src.api.v1.topology.models import ComponentTopologyDTO, TopologySignalDTO
from src.core.ports import ComponentRepository, SignalRepository


class TopologyService:
    """Thin edge service: list components + signals, nest, shape DTOs (dossier §13)."""

    def __init__(
        self,
        component_repo: ComponentRepository,
        signal_repo: SignalRepository,
    ) -> None:
        self._component_repo = component_repo
        self._signal_repo = signal_repo

    def get_topology(self) -> list[ComponentTopologyDTO]:
        """Return every component with its signals, sourced from the seeded topology.

        Component order follows `ComponentRepository.list_components()`.
        Signals are grouped by `component_id` and sorted by `signal_key`
        within each group. An orphan signal (`component_id is None`, or one
        referencing a component absent from `list_components()`) is
        component-centric AC1's deliberate exclusion — it appears nowhere in
        the nesting (config validation already rejects dangling
        `component_id`s at load time, so only `None` is reachable in
        practice).
        """
        components = self._component_repo.list_components()
        signals = self._signal_repo.list_signals()

        signals_by_component: dict[str, list] = defaultdict(list)
        for signal in signals:
            if signal.component_id is not None:
                signals_by_component[signal.component_id].append(signal)

        return [
            ComponentTopologyDTO(
                id=component.id,
                name=component.name,
                signals=[
                    TopologySignalDTO(
                        signal_key=signal.signal_key,
                        name=signal.name,
                        interval_seconds=signal.interval_seconds,
                        component_id=component.id,
                    )
                    for signal in sorted(
                        signals_by_component.get(component.id, []),
                        key=lambda s: s.signal_key,
                    )
                ],
            )
            for component in components
        ]


def get_topology_service(
    component_repo: ComponentRepository = Depends(get_component_repo),
    signal_repo: SignalRepository = Depends(get_signal_repo),
) -> TopologyService:
    """Dependency provider for TopologyService (dossier §13)."""
    return TopologyService(component_repo=component_repo, signal_repo=signal_repo)
