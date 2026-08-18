"""Unit tests for Crossplane environment settings validation."""
from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.environments.core.crossplane_settings import (
    CROSSPLANE_AWS_REGION_KEY,
    CROSSPLANE_CLUSTER_UUID_KEY,
    CROSSPLANE_ENABLED_KEY,
    CROSSPLANE_PROVIDER_CONFIG_KEY,
    resolve_crossplane_context_for_sync,
    validate_crossplane_settings,
)
from app.environments.core.environment_settings_defaults import (
    merge_missing_default_settings,
)


def _settings(**overrides):
    base = {
        CROSSPLANE_ENABLED_KEY: False,
        CROSSPLANE_CLUSTER_UUID_KEY: "",
        CROSSPLANE_AWS_REGION_KEY: "",
        CROSSPLANE_PROVIDER_CONFIG_KEY: "",
    }
    base.update(overrides)
    return [{"key": k, "value": v} for k, v in base.items()]


def _cluster(environment_id: int, crossplane_available: bool = True):
    cluster = MagicMock()
    cluster.environment_id = environment_id
    cluster.crossplane_available = crossplane_available
    cluster.uuid = uuid4()
    return cluster


def test_validate_disabled_requires_no_fields():
    validate_crossplane_settings(_settings(), environment_id=1, get_cluster_by_uuid=lambda _: None)


def test_validate_enabled_missing_provider_config():
    cluster_uuid = uuid4()
    with pytest.raises(ValueError, match=CROSSPLANE_PROVIDER_CONFIG_KEY):
        validate_crossplane_settings(
            _settings(
                **{
                    CROSSPLANE_ENABLED_KEY: True,
                    CROSSPLANE_CLUSTER_UUID_KEY: str(cluster_uuid),
                    CROSSPLANE_AWS_REGION_KEY: "us-east-1",
                    CROSSPLANE_PROVIDER_CONFIG_KEY: "",
                }
            ),
            environment_id=1,
            get_cluster_by_uuid=lambda _: _cluster(1),
        )


def test_validate_enabled_invalid_cluster_uuid():
    with pytest.raises(ValueError, match="valid UUID"):
        validate_crossplane_settings(
            _settings(
                **{
                    CROSSPLANE_ENABLED_KEY: True,
                    CROSSPLANE_CLUSTER_UUID_KEY: "not-a-uuid",
                    CROSSPLANE_AWS_REGION_KEY: "us-east-1",
                    CROSSPLANE_PROVIDER_CONFIG_KEY: "floci",
                }
            ),
            environment_id=1,
            get_cluster_by_uuid=lambda _: None,
        )


def test_validate_enabled_missing_cluster_uuid():
    with pytest.raises(ValueError, match=CROSSPLANE_CLUSTER_UUID_KEY):
        validate_crossplane_settings(
            _settings(
                **{
                    CROSSPLANE_ENABLED_KEY: True,
                    CROSSPLANE_AWS_REGION_KEY: "us-east-1",
                    CROSSPLANE_PROVIDER_CONFIG_KEY: "floci",
                }
            ),
            environment_id=1,
            get_cluster_by_uuid=lambda _: None,
        )


def test_validate_enabled_invalid_aws_region():
    cluster_uuid = uuid4()
    with pytest.raises(ValueError, match=CROSSPLANE_AWS_REGION_KEY):
        validate_crossplane_settings(
            _settings(
                **{
                    CROSSPLANE_ENABLED_KEY: True,
                    CROSSPLANE_CLUSTER_UUID_KEY: str(cluster_uuid),
                    CROSSPLANE_AWS_REGION_KEY: "invalid",
                    CROSSPLANE_PROVIDER_CONFIG_KEY: "floci",
                }
            ),
            environment_id=1,
            get_cluster_by_uuid=lambda _: _cluster(1),
        )


def test_validate_enabled_cluster_not_found():
    cluster_uuid = uuid4()
    with pytest.raises(ValueError, match="not found"):
        validate_crossplane_settings(
            _settings(
                **{
                    CROSSPLANE_ENABLED_KEY: True,
                    CROSSPLANE_CLUSTER_UUID_KEY: str(cluster_uuid),
                    CROSSPLANE_AWS_REGION_KEY: "us-east-1",
                    CROSSPLANE_PROVIDER_CONFIG_KEY: "floci",
                }
            ),
            environment_id=1,
            get_cluster_by_uuid=lambda _: None,
        )


def test_validate_enabled_cluster_wrong_environment():
    cluster_uuid = uuid4()
    with pytest.raises(ValueError, match="same environment"):
        validate_crossplane_settings(
            _settings(
                **{
                    CROSSPLANE_ENABLED_KEY: True,
                    CROSSPLANE_CLUSTER_UUID_KEY: str(cluster_uuid),
                    CROSSPLANE_AWS_REGION_KEY: "us-east-1",
                    CROSSPLANE_PROVIDER_CONFIG_KEY: "floci",
                }
            ),
            environment_id=1,
            get_cluster_by_uuid=lambda _: _cluster(environment_id=2),
        )


def test_validate_enabled_cluster_not_available():
    cluster_uuid = uuid4()
    with pytest.raises(ValueError, match="crossplane_available"):
        validate_crossplane_settings(
            _settings(
                **{
                    CROSSPLANE_ENABLED_KEY: True,
                    CROSSPLANE_CLUSTER_UUID_KEY: str(cluster_uuid),
                    CROSSPLANE_AWS_REGION_KEY: "sa-east-1",
                    CROSSPLANE_PROVIDER_CONFIG_KEY: "default",
                }
            ),
            environment_id=1,
            get_cluster_by_uuid=lambda _: _cluster(1, crossplane_available=False),
        )


def test_resolve_disabled_context():
    ctx = resolve_crossplane_context_for_sync(
        _settings(), environment_id=1, get_cluster_by_uuid=lambda _: None
    )
    assert ctx.enabled is False
    assert ctx.cluster is None


def test_resolve_enabled_context():
    cluster_uuid = uuid4()
    cluster = _cluster(environment_id=5)
    cluster.uuid = cluster_uuid

    ctx = resolve_crossplane_context_for_sync(
        _settings(
            **{
                CROSSPLANE_ENABLED_KEY: True,
                CROSSPLANE_CLUSTER_UUID_KEY: str(cluster_uuid),
                CROSSPLANE_AWS_REGION_KEY: "us-east-1",
                CROSSPLANE_PROVIDER_CONFIG_KEY: "floci",
            }
        ),
        environment_id=5,
        get_cluster_by_uuid=lambda uid: cluster if uid == cluster_uuid else None,
    )

    assert ctx.enabled is True
    assert ctx.cluster_uuid == cluster_uuid
    assert ctx.aws_region == "us-east-1"
    assert ctx.provider_config == "floci"
    assert ctx.cluster is cluster


def test_merge_missing_default_settings_appends_crossplane_keys():
    merged = merge_missing_default_settings(
        [{"key": "max_pods", "value": 5, "description": "", "type": "number"}]
    )
    keys = {item["key"] for item in merged}
    assert "crossplane_enabled" in keys
    assert "crossplane_cluster_uuid" in keys
    assert "crossplane_aws_region" in keys
    assert "crossplane_provider_config" in keys
