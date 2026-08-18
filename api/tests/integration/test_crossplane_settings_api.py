"""Integration tests for Crossplane environment settings."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from uuid import uuid4

from app.environments.infra.environment_model import Environment
from app.environments.infra.environment_repository import EnvironmentRepository
from app.environments.infra.environment_settings_model import EnvironmentSettings
from app.environments.infra.environment_settings_repository import (
    EnvironmentSettingsRepository,
)
from app.environments.core.environment_settings_defaults import (
    DEFAULT_ENVIRONMENT_SETTINGS,
)
from app.clusters.infra.cluster_model import Cluster
from app.clusters.infra.cluster_repository import ClusterRepository


@pytest.fixture
def test_environment_with_settings(test_db, admin_user, test_organization):
    """Environment with default settings row."""
    env_repo = EnvironmentRepository(test_db)
    environment = env_repo.create(
        Environment(name="crossplane-env", organization_id=test_organization.id)
    )
    settings_repo = EnvironmentSettingsRepository(test_db)
    settings_repo.create(
        EnvironmentSettings(
            uuid=uuid4(),
            environment_id=environment.id,
            organization_id=test_organization.id,
            settings=[dict(item) for item in DEFAULT_ENVIRONMENT_SETTINGS],
        )
    )
    test_db.commit()
    test_db.refresh(environment)
    environment.organization = test_organization
    return environment


@pytest.fixture
def crossplane_cluster(test_db, test_environment_with_settings):
    """Cluster marked available for Crossplane."""
    cluster_repo = ClusterRepository(test_db)
    cluster = cluster_repo.create(
        Cluster(
            uuid=uuid4(),
            name="crossplane-cluster",
            api_address="https://k8s-crossplane.example.com",
            token="token",
            environment_id=test_environment_with_settings.id,
            crossplane_available=True,
        )
    )
    test_db.commit()
    test_db.refresh(cluster)
    return cluster


def test_update_crossplane_settings_success(
    client,
    admin_token,
    test_organization,
    test_environment_with_settings,
    crossplane_cluster,
):
    org_uuid = str(test_organization.uuid)
    env_uuid = str(test_environment_with_settings.uuid)

    response = client.put(
        f"/organizations/{org_uuid}/environments/{env_uuid}/settings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "crossplane_enabled": True,
            "crossplane_cluster_uuid": str(crossplane_cluster.uuid),
            "crossplane_aws_region": "us-east-1",
            "crossplane_provider_config": "floci",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    settings = {item["key"]: item["value"] for item in response.json()}
    assert settings["crossplane_enabled"] is True
    assert settings["crossplane_aws_region"] == "us-east-1"


def test_update_crossplane_settings_invalid_region(
    client,
    admin_token,
    test_organization,
    test_environment_with_settings,
    crossplane_cluster,
):
    org_uuid = str(test_organization.uuid)
    env_uuid = str(test_environment_with_settings.uuid)

    response = client.put(
        f"/organizations/{org_uuid}/environments/{env_uuid}/settings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "crossplane_enabled": True,
            "crossplane_cluster_uuid": str(crossplane_cluster.uuid),
            "crossplane_aws_region": "not-a-region",
            "crossplane_provider_config": "floci",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "crossplane_aws_region" in response.json()["detail"]


def test_update_crossplane_settings_cluster_not_available(
    client,
    admin_token,
    test_organization,
    test_environment_with_settings,
    test_db,
):
    cluster_repo = ClusterRepository(test_db)
    cluster = cluster_repo.create(
        Cluster(
            uuid=uuid4(),
            name="unavailable-cluster",
            api_address="https://k8s-unavailable.example.com",
            token="token",
            environment_id=test_environment_with_settings.id,
            crossplane_available=False,
        )
    )
    test_db.commit()

    org_uuid = str(test_organization.uuid)
    env_uuid = str(test_environment_with_settings.uuid)

    response = client.put(
        f"/organizations/{org_uuid}/environments/{env_uuid}/settings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "crossplane_enabled": True,
            "crossplane_cluster_uuid": str(cluster.uuid),
            "crossplane_aws_region": "us-east-1",
            "crossplane_provider_config": "floci",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "crossplane_available" in response.json()["detail"]


def test_environment_get_returns_cluster_objects(
    client,
    admin_token,
    test_organization,
    test_environment_with_settings,
    crossplane_cluster,
):
    org_uuid = str(test_organization.uuid)
    env_uuid = str(test_environment_with_settings.uuid)

    response = client.get(
        f"/organizations/{org_uuid}/environments/{env_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["clusters"]) == 1
    cluster = data["clusters"][0]
    assert cluster["uuid"] == str(crossplane_cluster.uuid)
    assert cluster["name"] == crossplane_cluster.name
    assert cluster["crossplane_available"] is True
    setting_keys = {item["key"] for item in data["settings"]}
    assert "crossplane_enabled" in setting_keys
    assert "crossplane_cluster_uuid" in setting_keys
    assert "crossplane_aws_region" in setting_keys
    assert "crossplane_provider_config" in setting_keys


@patch("app.clusters.core.cluster_service.K8sClient")
def test_create_cluster_with_crossplane_available(
    mock_k8s_client,
    client,
    admin_token,
    test_environment_with_settings,
):
    mock_client_instance = MagicMock()
    mock_client_instance.validate_connection.return_value = (
        True,
        {"message": "Connection successful"},
    )
    mock_k8s_client.return_value = mock_client_instance

    org_uuid = str(test_environment_with_settings.organization.uuid)
    response = client.post(
        f"/organizations/{org_uuid}/clusters/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "cp-cluster",
            "api_address": "https://k8s.example.com",
            "token": "test-token",
            "environment_uuid": str(test_environment_with_settings.uuid),
            "crossplane_available": True,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["crossplane_available"] is True
