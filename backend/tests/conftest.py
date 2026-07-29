"""Test config: make the repo-root `scripts/` and `tools/` dirs importable,
and provide the shared throwaway-DB session fixture (STORY-019).

`scripts/` holds standalone CI scripts (e.g. check_fk_direction.py, dev_db.py)
that are not part of the `src` package but whose pure logic is unit-tested.
`tools/` holds `demo_engine/` (STORY-148) similarly. This repo-root is two
levels up from this file (backend/tests/conftest.py -> repo root).

Both are inserted here, in the ONE shared conftest, rather than an extra
conftest.py in a test subdirectory: pytest resolves a bare, `__init__.py`-less
conftest.py's module name from its basename alone, so two such files both
named `conftest.py` collide on the same `sys.modules['conftest']` entry
(discovered live: it broke `test_dynamo_local.py`'s
`from conftest import provide_dynamo_local`).
"""

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

_TOOLS = _REPO_ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import dynamo_local as dynamo_local_module  # noqa: E402


def provide_dynamo_local():
    """Generator implementing the `dynamo_local` fixture's lifecycle.

    Reflects DYNAMO_ENDPOINT_URL into os.environ with save/restore.
    A finalizer stops the container even on test failure.
    """
    plan = dynamo_local_module.resolve_dynamo()

    if plan.source == "skip":
        pytest.skip(
            "no DYNAMO_ENDPOINT_URL set and Docker is unavailable; "
            "skipping DynamoDB-gated tests"
        )

    prev_endpoint = os.environ.get("DYNAMO_ENDPOINT_URL")
    os.environ["DYNAMO_ENDPOINT_URL"] = plan.endpoint_url

    try:
        yield plan
    finally:
        if plan.source == "container":
            dynamo_local_module.stop_container(plan.container_name)

        if prev_endpoint is None:
            os.environ.pop("DYNAMO_ENDPOINT_URL", None)
        else:
            os.environ["DYNAMO_ENDPOINT_URL"] = prev_endpoint


@pytest.fixture(scope="session")
def dynamo_local():
    """Session-scoped throwaway-DynamoDB fixture; see provide_dynamo_local()."""
    yield from provide_dynamo_local()


@pytest.fixture
def clean_dynamo_tables(dynamo_local):
    """Function-scoped fixture: delete and re-create DynamoDB tables for isolation."""
    import boto3
    from botocore.exceptions import ClientError
    from create_tables import create_tables
    from src.composition.settings import load_settings

    settings = load_settings()
    client_kwargs = {
        "region_name": settings.aws_region,
    }
    if settings.dynamo_endpoint_url:
        client_kwargs["endpoint_url"] = settings.dynamo_endpoint_url
        client_kwargs["aws_access_key_id"] = "test"
        client_kwargs["aws_secret_access_key"] = "test"

    dynamodb = boto3.client("dynamodb", **client_kwargs)

    tables = [settings.dynamo_observations_table, settings.dynamo_control_table]
    for table in tables:
        try:
            dynamodb.delete_table(TableName=table)
            waiter = dynamodb.get_waiter("table_not_exists")
            waiter.wait(TableName=table)
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
                raise

    create_tables()
    yield


@pytest.fixture
def dynamo_resource(dynamo_local, clean_dynamo_tables):
    """Function-scoped DynamoDB resource fixture, chained on clean_dynamo_tables."""
    import boto3
    from src.composition.settings import load_settings

    settings = load_settings()
    resource_kwargs = {
        "region_name": settings.aws_region,
    }
    if settings.dynamo_endpoint_url:
        resource_kwargs["endpoint_url"] = settings.dynamo_endpoint_url
        resource_kwargs["aws_access_key_id"] = "test"
        resource_kwargs["aws_secret_access_key"] = "test"

    db_resource = boto3.resource("dynamodb", **resource_kwargs)
    yield db_resource
