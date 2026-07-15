"""DynamoDB implementation of RejectedObservationRepository."""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from src.adapters.persistence.dynamo_serde import to_canonical_iso
from src.core.ports.rejected_observation_repository import RejectedObservationRepository


class DynamoRejectedObservationRepository(RejectedObservationRepository):
    """DynamoDB repository for quarantining invalid observations (STORY-086)."""

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table_name = table_name
        self._table = self._db.Table(table_name)

    def save(
        self,
        *,
        signal_key: str | None,
        reason: str,
        payload: dict,
        rejected_at: datetime,
    ) -> None:
        """Persist one rejected observation for audit.

        Converts floats in the payload to Decimal to satisfy boto3 serialization requirements.
        """
        rejected_at_str = to_canonical_iso(rejected_at)
        pk_key = f"REJECTED#{signal_key if signal_key is not None else 'UNKNOWN'}"
        sk_key = f"{rejected_at_str}#{uuid4()}"

        # Convert floats to Decimal in payload
        serialized_payload = json.loads(json.dumps(payload), parse_float=Decimal)

        item = {
            "pk": pk_key,
            "sk": sk_key,
            "reason": reason,
            "payload": serialized_payload,
            "rejected_at": rejected_at_str,
        }
        if signal_key is not None:
            item["signal_key"] = signal_key

        self._table.put_item(Item=item)
