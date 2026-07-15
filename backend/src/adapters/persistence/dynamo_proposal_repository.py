"""DynamoDB implementation of ProposalRepository."""

from __future__ import annotations

from datetime import datetime

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.adapters.persistence.dynamo_serde import from_canonical_iso, to_canonical_iso
from src.core.domain.proposal import (
    ProposalNotOpenError,
    ProposalState,
    StatusProposal,
)
from src.core.domain.status import ComponentStatus
from src.core.ports.proposal_repository import ProposalRepository


class DynamoProposalRepository(ProposalRepository):
    """DynamoDB repository for managing status proposals and approval events."""

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table_name = table_name
        self._table = self._db.Table(table_name)

    def _map_item(self, item: dict) -> StatusProposal:
        from_status = None
        if item.get("from_status") is not None:
            from_status = ComponentStatus(item["from_status"])

        resolved_at = None
        if item.get("resolved_at") is not None:
            resolved_at = from_canonical_iso(item["resolved_at"])

        return StatusProposal(
            id=int(item["id"]) if item.get("id") is not None else None,
            component_id=item["component_id"],
            from_status=from_status,
            to_status=ComponentStatus(item["to_status"]),
            state=ProposalState(item["state"]),
            reason=item.get("reason"),
            proposed_at=from_canonical_iso(item["proposed_at"]),
            resolved_at=resolved_at,
        )

    def _base_proposal_attrs(
        self,
        proposal: StatusProposal,
        assigned_id: int,
        proposed_at_str: str,
        resolved_at_str: str | None,
    ) -> dict:
        """Helper to extract shared proposal attributes for DB writes."""
        attrs = {
            "id": assigned_id,
            "component_id": proposal.component_id,
            "to_status": proposal.to_status.value,
            "state": proposal.state.value,
            "proposed_at": proposed_at_str,
        }
        if proposal.from_status is not None:
            attrs["from_status"] = proposal.from_status.value
        if proposal.reason is not None:
            attrs["reason"] = proposal.reason
        if resolved_at_str is not None:
            attrs["resolved_at"] = resolved_at_str
        return attrs

    def _next_id(self) -> int:
        """Increment sequence counter and return the next Proposal ID."""
        response = self._table.update_item(
            Key={"pk": "COUNTER", "sk": "proposal"},
            UpdateExpression="ADD seq :inc",
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="UPDATED_NEW",
        )
        return int(response["Attributes"]["seq"])

    def create_open(self, proposal: StatusProposal) -> StatusProposal | None:
        """Persist a new open status proposal.

        Enforces that only one open proposal exists per component_id.
        If an open proposal already exists, returns None.
        """
        assigned_id = self._next_id()
        proposed_at_str = to_canonical_iso(proposal.proposed_at)
        resolved_at_str = (
            to_canonical_iso(proposal.resolved_at) if proposal.resolved_at else None
        )

        base_attrs = self._base_proposal_attrs(
            proposal, assigned_id, proposed_at_str, resolved_at_str
        )

        # Proposal META item
        meta_item = {
            "pk": f"PROPOSAL#{assigned_id}",
            "sk": "META",
            **base_attrs,
        }

        # If proposal is open, index via sparse GSI
        if proposal.state == ProposalState.OPEN:
            meta_item["gsi1pk"] = "PROPOSAL_OPEN"
            meta_item["gsi1sk"] = f"PROPOSAL#{assigned_id}"

        # Slot item: COMPONENT#<cid> / OPEN_PROPOSAL
        slot_item = {
            "pk": f"COMPONENT#{proposal.component_id}",
            "sk": "OPEN_PROPOSAL",
            **base_attrs,
        }

        client = self._db.meta.client

        try:
            client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self._table_name,
                            "Item": meta_item,
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                    {
                        "Put": {
                            "TableName": self._table_name,
                            "Item": slot_item,
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                ]
            )
            return proposal.model_copy(update={"id": assigned_id})
        except ClientError as e:
            if e.response["Error"]["Code"] == "TransactionCanceledException":
                # Condition check failed (slot already exists or META already exists)
                return None
            raise

    def get_open(self, component_id: str) -> StatusProposal | None:
        """Retrieve the open status proposal for a component, if any."""
        response = self._table.get_item(
            Key={
                "pk": f"COMPONENT#{component_id}",
                "sk": "OPEN_PROPOSAL",
            },
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            return None
        return self._map_item(item)

    def get(self, proposal_id: int) -> StatusProposal | None:
        """Return the proposal with this id, or None if none exists."""
        response = self._table.get_item(
            Key={
                "pk": f"PROPOSAL#{proposal_id}",
                "sk": "META",
            },
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            return None
        return self._map_item(item)

    def list_open(self) -> list[StatusProposal]:
        """Retrieve all OPEN status proposals from the repository."""
        response = self._table.query(
            IndexName="gsi1",
            KeyConditionExpression=Key("gsi1pk").eq("PROPOSAL_OPEN"),
        )
        items = response.get("Items", [])
        return [self._map_item(item) for item in items]

    def resolve(
        self,
        proposal_id: int,
        *,
        to_state: ProposalState,
        reason: str | None,
        resolved_at: datetime,
    ) -> None:
        """Move an open status proposal to a terminal state."""
        # 1. Consistent read of the META item to get component_id
        proposal = self.get(proposal_id)
        if not proposal or proposal.state != ProposalState.OPEN:
            raise ProposalNotOpenError(
                f"Proposal {proposal_id} not found or not in open state."
            )

        resolved_at_str = to_canonical_iso(resolved_at)

        # 2. Transaction to update META and delete Slot
        client = self._db.meta.client

        # Expression to update META (sets state/resolved_at/reason, removes sparse GSI fields)
        update_expr = "SET #state = :state, resolved_at = :resolved_at"
        expr_attr_names = {"#state": "state"}
        expr_attr_values = {
            ":state": to_state.value,
            ":resolved_at": resolved_at_str,
            ":open_state": ProposalState.OPEN.value,
        }
        if reason is not None:
            update_expr += ", reason = :reason"
            expr_attr_values[":reason"] = reason

        update_expr += " REMOVE gsi1pk, gsi1sk"

        try:
            client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": self._table_name,
                            "Key": {"pk": f"PROPOSAL#{proposal_id}", "sk": "META"},
                            "UpdateExpression": update_expr,
                            "ExpressionAttributeNames": expr_attr_names,
                            "ExpressionAttributeValues": expr_attr_values,
                            "ConditionExpression": "attribute_exists(pk) AND #state = :open_state",
                        }
                    },
                    {
                        "Delete": {
                            "TableName": self._table_name,
                            "Key": {
                                "pk": f"COMPONENT#{proposal.component_id}",
                                "sk": "OPEN_PROPOSAL",
                            },
                            # Open proposal component_id slot is unique, but check ID for absolute safety
                            "ConditionExpression": "id = :proposal_id",
                            "ExpressionAttributeValues": {":proposal_id": proposal_id},
                        }
                    },
                ]
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "TransactionCanceledException":
                raise ProposalNotOpenError(
                    f"Proposal {proposal_id} not found or not in open state."
                )
            raise

    def record_approval_event(
        self,
        proposal_id: int,
        *,
        actor: str,
        action: str,
        notes: str | None,
        occurred_at: datetime,
    ) -> None:
        """Record an approval or rejection event for a proposal."""
        occurred_at_str = to_canonical_iso(occurred_at)

        # Event item: PROPOSAL#<id> / EVENT#<occurred_at>#<action>
        event_item = {
            "pk": f"PROPOSAL#{proposal_id}",
            "sk": f"EVENT#{occurred_at_str}#{action}",
            "proposal_id": proposal_id,
            "actor": actor,
            "action": action,
            "occurred_at": occurred_at_str,
        }
        if notes is not None:
            event_item["notes"] = notes

        client = self._db.meta.client

        # Build transaction to write event and denormalize approved_actor if approved
        transact_items = [
            {
                "Put": {
                    "TableName": self._table_name,
                    "Item": event_item,
                }
            }
        ]

        if action == "approved":
            transact_items.append(
                {
                    "Update": {
                        "TableName": self._table_name,
                        "Key": {"pk": f"PROPOSAL#{proposal_id}", "sk": "META"},
                        "UpdateExpression": "SET approved_actor = :actor",
                        "ExpressionAttributeValues": {":actor": actor},
                        "ConditionExpression": "attribute_exists(pk)",
                    }
                }
            )
        else:
            # STORY-091: Add a condition check on the proposal META item to prevent orphan events.
            # Currently unreachable via ApprovalService._decide, which loads + resolves first,
            # so this is latent-divergence hygiene, not a live bug.
            transact_items.append(
                {
                    "ConditionCheck": {
                        "TableName": self._table_name,
                        "Key": {"pk": f"PROPOSAL#{proposal_id}", "sk": "META"},
                        "ConditionExpression": "attribute_exists(pk)",
                    }
                }
            )

        # Any ClientError (incl. a TransactionCanceledException when the approved-actor
        # Update's attribute_exists(pk) condition fails on a missing proposal) propagates
        # — recording an event against a missing proposal is not permitted. (STORY-085
        # quality review: removed a dead try/except that re-raised unconditionally.)
        client.transact_write_items(TransactItems=transact_items)
