"""Controller for the topology feature (dossier §7, §9, §13, STORY-044 AC1).

GET /topology
Returns every component with its signals — sourced from the seeded topology,
never re-read from config files at request time.
"""

from fastapi import APIRouter, Depends

from src.api.v1.topology.models import ComponentTopologyDTO
from src.api.v1.topology.service import TopologyService, get_topology_service

router = APIRouter()


@router.get("/topology", response_model=list[ComponentTopologyDTO])
def get_topology(
    service: TopologyService = Depends(get_topology_service),
) -> list[ComponentTopologyDTO]:
    """Return every component with its signals (dossier §7, §9, §13).

    Empty topology -> 200 + []. A component with no mapped signals gets
    signals: []. An orphan signal (no component_id) appears nowhere.
    """
    return service.get_topology()
