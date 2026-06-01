"""niche thumbnail_provider column

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-01 00:00:00.000000

Adds an optional dedicated thumbnail image provider per niche (e.g. nano_banana)
so the thumbnail can use a paid AI image generator while the video scenes stay
on a free provider (Pexels/Unsplash).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("niches", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("thumbnail_provider", sa.String(length=32), nullable=False, server_default="")
        )


def downgrade() -> None:
    with op.batch_alter_table("niches", schema=None) as batch_op:
        batch_op.drop_column("thumbnail_provider")
