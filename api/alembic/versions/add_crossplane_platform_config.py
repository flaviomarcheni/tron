"""add_crossplane_platform_config

Revision ID: add_crossplane_platform
Revises: env_settings_single_json
Create Date: 2026-08-18

Add crossplane_available flag to clusters for messaging Crossplane sync.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "add_crossplane_platform"
down_revision: Union[str, None] = "env_settings_single_json"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clusters",
        sa.Column(
            "crossplane_available",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("clusters", "crossplane_available")
