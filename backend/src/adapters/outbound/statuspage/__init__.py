"""Statuspage outbound adapter (dossier §6, §12)."""

from collections.abc import Callable
from src.core.ports import StatusPublisherPort
from src.core.domain.status import StatusChange

#: Seam type for executing HTTP requests against Statuspage API.
#: Takes (method, url, headers, json_body) and returns the parsed response dict.
Executor = Callable[[str, str, dict[str, str], dict], dict]


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
        raise NotImplementedError
