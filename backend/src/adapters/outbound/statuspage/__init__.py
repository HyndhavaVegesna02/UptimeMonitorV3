"""Statuspage outbound adapter (dossier §6, §12)."""

from collections.abc import Callable
from src.core.ports import StatusPublisherPort
from src.core.domain.status import StatusChange
from src.adapters.outbound.statuspage.status_mapping import (
    map_component_status,
    UnknownComponentStatusError,
)

#: Seam type for executing HTTP requests against Statuspage API.
#: Takes (method, url, headers, json_body) and returns the parsed response dict.
Executor = Callable[[str, str, dict[str, str], dict], dict]



class UnmappedComponentIdError(ValueError):
    """Raised when a component_id has no mapped Statuspage component id."""


class StatuspagePublisher(StatusPublisherPort):
    """Outbound adapter for publishing component status changes to Statuspage SaaS."""

    def __init__(
        self,
        *,
        page_id: str,
        api_token: str,
        component_mapping: dict[str, str],
        executor: Executor,
    ) -> None:
        self._page_id = page_id
        self._api_token = api_token
        self._component_mapping = component_mapping
        self._executor = executor

    def publish(self, change: StatusChange) -> None:
        """Publish a canonical StatusChange to Statuspage."""
        component_id = change.component_id
        if component_id not in self._component_mapping:
            raise UnmappedComponentIdError(
                f"Component {component_id!r} has no mapped Statuspage component id."
            )
        vendor_comp_id = self._component_mapping[component_id]
        vendor_status = map_component_status(change.status)

        url = f"https://api.statuspage.io/v1/pages/{self._page_id}/components/{vendor_comp_id}"
        headers = {
            "Authorization": f"OAuth {self._api_token}",
            "Content-Type": "application/json",
        }
        json_body = {
            "component": {
                "status": vendor_status
            }
        }

        self._executor("PATCH", url, headers, json_body)

