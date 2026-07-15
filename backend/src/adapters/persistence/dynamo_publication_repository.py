"""DynamoDB implementation of PublicationRepository."""

from __future__ import annotations

from boto3.dynamodb.conditions import Key

from src.adapters.persistence.dynamo_serde import from_canonical_iso, to_canonical_iso
from src.core.domain.publication import Publication, PublicationOutcome
from src.core.domain.status import ComponentStatus
from src.core.ports.publication_repository import PublicationRepository


class DynamoPublicationRepository(PublicationRepository):
    """DynamoDB repository for recording and listing publications (STORY-086)."""

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table_name = table_name
        self._table = self._db.Table(table_name)

    def _next_id(self) -> int:
        """Increment sequence counter and return the next Publication ID."""
        response = self._table.update_item(
            Key={"pk": "COUNTER", "sk": "publication"},
            UpdateExpression="ADD seq :inc",
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="UPDATED_NEW",
        )
        return int(response["Attributes"]["seq"])

    def record(self, publication: Publication) -> Publication:
        """INSERT a new publication item and return it with the assigned id."""
        assigned_id = self._next_id()
        published_at_str = to_canonical_iso(publication.published_at)

        item = {
            "pk": "PUBLICATION",
            "sk": f"{published_at_str}#{assigned_id}",
            "id": assigned_id,
            "component_id": publication.component_id,
            "status": publication.status.value,
            "published_at": published_at_str,
            "outcome": publication.outcome.value,
        }
        if publication.proposal_id is not None:
            item["proposal_id"] = publication.proposal_id

        self._table.put_item(Item=item)
        return publication.model_copy(update={"id": assigned_id})

    def list_recent(self, limit: int = 50) -> list[Publication]:
        """Query the PUBLICATION partition descending, capped at limit."""
        response = self._table.query(
            KeyConditionExpression=Key("pk").eq("PUBLICATION"),
            ScanIndexForward=False,
            Limit=limit,
        )
        items = response.get("Items", [])
        if not items:
            return []

        # Collect distinct proposal IDs (ignoring None)
        proposal_ids = sorted(
            list(
                {
                    int(item["proposal_id"])
                    for item in items
                    if item.get("proposal_id") is not None
                }
            )
        )

        # Retrieve proposal METAs using BatchGetItem
        author_map = {}
        if proposal_ids:
            # Chunk keys in batches of 100 as per batch_get_item limit
            chunk_size = 100
            for i in range(0, len(proposal_ids), chunk_size):
                chunk = proposal_ids[i : i + chunk_size]
                keys = [{"pk": f"PROPOSAL#{pid}", "sk": "META"} for pid in chunk]

                unprocessed_keys = {self._table_name: {"Keys": keys}}
                while unprocessed_keys and self._table_name in unprocessed_keys:
                    batch_response = self._db.meta.client.batch_get_item(
                        RequestItems=unprocessed_keys
                    )

                    # Process retrieved items
                    retrieved_items = batch_response.get("Responses", {}).get(
                        self._table_name, []
                    )
                    for item in retrieved_items:
                        pid = int(item["id"])
                        approved_actor = item.get("approved_actor")
                        if approved_actor:
                            author_map[pid] = approved_actor

                    # Get unprocessed keys if any
                    unprocessed_keys = batch_response.get("UnprocessedKeys", {})

        publications = []
        for item in items:
            prop_id = (
                int(item["proposal_id"])
                if item.get("proposal_id") is not None
                else None
            )
            author = author_map.get(prop_id) if prop_id is not None else None

            publications.append(
                Publication(
                    id=int(item["id"]),
                    component_id=item["component_id"],
                    status=ComponentStatus(item["status"]),
                    published_at=from_canonical_iso(item["published_at"]),
                    outcome=PublicationOutcome(item["outcome"]),
                    proposal_id=prop_id,
                    author=author,
                )
            )
        return publications
