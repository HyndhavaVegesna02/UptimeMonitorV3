"""DynamoDB resource factory (composition zone, dossier §3, §17)."""

from __future__ import annotations

import boto3
from src.composition.settings import Settings


def make_dynamo_resource(settings: Settings):
    """Create a boto3 DynamoDB resource targeting the configured environment (dossier §17, STORY-082 AC4).

    When settings.dynamo_endpoint_url is set, dummy static credentials ('test'/'test')
    are used to target a local/throwaway DynamoDB Local instance, avoiding
    reading real AWS credentials.
    """
    resource_kwargs: dict = {
        "region_name": settings.aws_region,
    }
    
    if settings.dynamo_endpoint_url:
        resource_kwargs["endpoint_url"] = settings.dynamo_endpoint_url
        resource_kwargs["aws_access_key_id"] = "test"
        resource_kwargs["aws_secret_access_key"] = "test"

    return boto3.resource("dynamodb", **resource_kwargs)
