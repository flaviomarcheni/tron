"""Crossplane platform settings validation and sync context resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional
from uuid import UUID

CROSSPLANE_ENABLED_KEY = "crossplane_enabled"
CROSSPLANE_CLUSTER_UUID_KEY = "crossplane_cluster_uuid"
CROSSPLANE_AWS_REGION_KEY = "crossplane_aws_region"
CROSSPLANE_PROVIDER_CONFIG_KEY = "crossplane_provider_config"

AWS_REGION_PATTERN = re.compile(r"^[a-z]{2}-[a-z]+-\d+$")


@dataclass
class CrossplaneContext:
    """Resolved Crossplane configuration for messaging sync."""

    enabled: bool
    cluster_uuid: Optional[UUID] = None
    aws_region: Optional[str] = None
    provider_config: Optional[str] = None
    cluster: Any = None


def get_setting_value(settings_list: list | None, key: str) -> Any:
    """Return the value for a setting key, or None if missing."""
    if not settings_list:
        return None
    for item in settings_list:
        if isinstance(item, dict) and item.get("key") == key:
            return item.get("value")
    return None


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


def _parse_cluster_uuid(value: Any) -> UUID:
    if value is None or value == "":
        raise ValueError(
            f"{CROSSPLANE_CLUSTER_UUID_KEY} is required when crossplane_enabled is true"
        )
    try:
        return UUID(str(value))
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"{CROSSPLANE_CLUSTER_UUID_KEY} must be a valid UUID"
        ) from exc


def validate_crossplane_settings(
    settings_list: list,
    environment_id: int,
    get_cluster_by_uuid: Callable[[UUID], Any],
) -> None:
    """
    Validate Crossplane environment settings.
    Raises ValueError when crossplane_enabled is true and config is invalid.
    """
    enabled = _is_truthy(get_setting_value(settings_list, CROSSPLANE_ENABLED_KEY))
    if not enabled:
        return

    cluster_uuid = _parse_cluster_uuid(
        get_setting_value(settings_list, CROSSPLANE_CLUSTER_UUID_KEY)
    )

    aws_region = get_setting_value(settings_list, CROSSPLANE_AWS_REGION_KEY)
    if not aws_region or not isinstance(aws_region, str) or not aws_region.strip():
        raise ValueError(
            f"{CROSSPLANE_AWS_REGION_KEY} is required when crossplane_enabled is true"
        )
    aws_region = aws_region.strip()
    if not AWS_REGION_PATTERN.match(aws_region):
        raise ValueError(
            f"{CROSSPLANE_AWS_REGION_KEY} must be a valid AWS region (e.g. us-east-1, sa-east-1)"
        )

    provider_config = get_setting_value(settings_list, CROSSPLANE_PROVIDER_CONFIG_KEY)
    if (
        not provider_config
        or not isinstance(provider_config, str)
        or not provider_config.strip()
    ):
        raise ValueError(
            f"{CROSSPLANE_PROVIDER_CONFIG_KEY} is required when crossplane_enabled is true"
        )

    cluster = get_cluster_by_uuid(cluster_uuid)
    if not cluster:
        raise ValueError(f"Cluster with UUID {cluster_uuid} not found")
    if cluster.environment_id != environment_id:
        raise ValueError("Crossplane cluster must belong to the same environment")
    if not getattr(cluster, "crossplane_available", False):
        raise ValueError(
            "Crossplane cluster must have crossplane_available enabled"
        )


def resolve_crossplane_context_for_sync(
    settings_list: list,
    environment_id: int,
    get_cluster_by_uuid: Callable[[UUID], Any],
) -> CrossplaneContext:
    """
    Resolve Crossplane context for messaging sync.
    Validates settings when enabled; returns disabled context otherwise.
    """
    enabled = _is_truthy(get_setting_value(settings_list, CROSSPLANE_ENABLED_KEY))
    if not enabled:
        return CrossplaneContext(enabled=False)

    validate_crossplane_settings(settings_list, environment_id, get_cluster_by_uuid)

    cluster_uuid = _parse_cluster_uuid(
        get_setting_value(settings_list, CROSSPLANE_CLUSTER_UUID_KEY)
    )
    cluster = get_cluster_by_uuid(cluster_uuid)
    aws_region = str(get_setting_value(settings_list, CROSSPLANE_AWS_REGION_KEY)).strip()
    provider_config = str(
        get_setting_value(settings_list, CROSSPLANE_PROVIDER_CONFIG_KEY)
    ).strip()

    return CrossplaneContext(
        enabled=True,
        cluster_uuid=cluster_uuid,
        aws_region=aws_region,
        provider_config=provider_config,
        cluster=cluster,
    )
