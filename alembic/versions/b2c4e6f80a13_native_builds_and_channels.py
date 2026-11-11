"""native builds for versions, install channels for devices

Revision ID: b2c4e6f80a13
Revises: fa8fc66b8da6
Create Date: 2026-11-11 16:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b2c4e6f80a13"
down_revision: Union[str, Sequence[str], None] = "fa8fc66b8da6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("versions", sa.Column("native", sa.String(), nullable=True))
    op.add_column("devices", sa.Column("is_prod", sa.Integer(), nullable=True))
    op.add_column("devices", sa.Column("version_build", sa.String(), nullable=True))
    op.add_column("devices", sa.Column("version_name", sa.String(), nullable=True))
    # "production" was only the old default, and beta/staging came from a debug menu that is gone: the install
    # decides the channel now, and only test stays as a choice made on the device.
    op.execute("UPDATE devices SET channel = NULL WHERE channel IS DISTINCT FROM 'test'")


def downgrade() -> None:
    op.execute("UPDATE devices SET channel = 'production' WHERE channel IS NULL")
    op.drop_column("devices", "version_name")
    op.drop_column("devices", "version_build")
    op.drop_column("devices", "is_prod")
    op.drop_column("versions", "native")
