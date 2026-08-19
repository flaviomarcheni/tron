from collections.abc import Callable
from typing import Any
from uuid import UUID, uuid4

from app.crossplane.api.crossplane_dto import (
    CrossplaneConfigResponse,
    CrossplaneConfigUpdate,
)
from app.crossplane.core.crossplane_validators import (
    CrossplaneContext,
    resolve_crossplane_context_for_sync,
    validate_crossplane_config,
)
from app.crossplane.infra.crossplane_config_model import EnvironmentCrossplaneConfig
from app.crossplane.infra.crossplane_config_repository import CrossplaneConfigRepository
from app.environments.infra.environment_repository import EnvironmentRepository


class CrossplaneService:
    """Business logic for environment-scoped Crossplane config."""

    def __init__(
        self,
        repository: CrossplaneConfigRepository,
        environment_repository: EnvironmentRepository,
        get_cluster_by_uuid: Callable[[UUID], Any],
    ):
        self.repository = repository
        self.environment_repository = environment_repository
        self.get_cluster_by_uuid = get_cluster_by_uuid

    def get_config(
        self, environment_uuid: UUID, organization_id: int
    ) -> CrossplaneConfigResponse:
        environment = self._require_environment(environment_uuid, organization_id)
        row = self.repository.find_by_environment_id(environment.id)
        return self._to_response(row)

    def update_config(
        self,
        environment_uuid: UUID,
        dto: CrossplaneConfigUpdate,
        organization_id: int,
    ) -> CrossplaneConfigResponse:
        environment = self._require_environment(environment_uuid, organization_id)
        validate_crossplane_config(
            dto.enabled,
            dto.cluster_uuid,
            dto.aws_region,
            dto.provider_config,
            environment.id,
            self.get_cluster_by_uuid,
        )

        row = self.repository.find_by_environment_id(environment.id)
        aws_region = dto.aws_region.strip()
        provider_config = dto.provider_config.strip()
        if row:
            row.enabled = dto.enabled
            row.cluster_uuid = dto.cluster_uuid
            row.aws_region = aws_region
            row.provider_config = provider_config
            saved = self.repository.update(row)
        else:
            saved = self.repository.create(
                EnvironmentCrossplaneConfig(
                    uuid=uuid4(),
                    environment_id=environment.id,
                    organization_id=organization_id,
                    enabled=dto.enabled,
                    cluster_uuid=dto.cluster_uuid,
                    aws_region=aws_region,
                    provider_config=provider_config,
                )
            )
        return self._to_response(saved)

    def resolve_context_for_sync(
        self, environment_uuid: UUID, organization_id: int
    ) -> CrossplaneContext:
        environment = self._require_environment(environment_uuid, organization_id)
        row = self.repository.find_by_environment_id(environment.id)
        if not row:
            return CrossplaneContext(enabled=False)
        return resolve_crossplane_context_for_sync(
            row.enabled,
            row.cluster_uuid,
            row.aws_region or "",
            row.provider_config or "",
            environment.id,
            self.get_cluster_by_uuid,
        )

    def _require_environment(self, environment_uuid: UUID, organization_id: int):
        environment = self.environment_repository.find_by_uuid_and_organization(
            environment_uuid, organization_id
        )
        if not environment:
            raise ValueError(
                f"Environment with UUID {environment_uuid} not found in organization"
            )
        return environment

    def _to_response(
        self, row: EnvironmentCrossplaneConfig | None
    ) -> CrossplaneConfigResponse:
        if not row:
            return CrossplaneConfigResponse()
        return CrossplaneConfigResponse(
            enabled=bool(row.enabled),
            cluster_uuid=row.cluster_uuid,
            aws_region=row.aws_region or "",
            provider_config=row.provider_config or "",
        )
