"""DynamoDB topology seeding logic (STORY-086)."""

from __future__ import annotations

import logging

from src.adapters.persistence.topology_keys import (
    app_item_key,
    component_item_key,
    signal_item_key,
)
from src.composition.config import Config
from src.core.domain.status import ComponentStatus

logger = logging.getLogger(__name__)


def seed_topology_dynamo(config: Config, db_resource, table_name: str) -> None:
    """Idempotently seed the topology from config into DynamoDB.

    Upserts seeded topology. Since DynamoDB has no foreign keys, order doesn't impact
    integrity, but we write apps -> components -> signals for readability.

    - Apps: Config stores the thresholds dictionary.
    - Components: Updates app_id and name, preserves existing runtime status.
    - Signals: Completely config-owned, full overwrite.
    """
    logger.info("Starting DynamoDB topology seeding from Git configuration...")
    table = db_resource.Table(table_name)

    # 1. Seed Apps
    for app in config.apps:
        app_item = {
            **app_item_key(app.id),
            "id": app.id,
            "name": app.name,
            "config": {"thresholds": app.thresholds.model_dump()},
        }
        table.put_item(Item=app_item)

    # 2. Seed Components
    for app in config.apps:
        for comp in app.components:
            # We use update_item with if_not_exists to update name and app_id,
            # but preserve status if the component already exists.
            table.update_item(
                Key=component_item_key(comp.id),
                UpdateExpression="SET #n = :name, app_id = :aid, #s = if_not_exists(#s, :default), id = :id",
                ExpressionAttributeNames={"#n": "name", "#s": "status"},
                ExpressionAttributeValues={
                    ":name": comp.name,
                    ":aid": app.id,
                    ":default": ComponentStatus.OPERATIONAL.value,
                    ":id": comp.id,
                },
            )

    # 3. Seed Signals
    for app in config.apps:
        for sig in app.signals:
            sig_item = {
                **signal_item_key(sig.signal_key),
                "signal_key": sig.signal_key,
                "app_id": app.id,
                "name": sig.name,
                "interval_seconds": sig.interval_seconds,
            }
            if sig.component_id is not None:
                sig_item["component_id"] = sig.component_id
            table.put_item(Item=sig_item)

    logger.info("DynamoDB topology seeding completed successfully.")
