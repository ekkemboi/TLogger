"""Add account_id to backtest_sessions for resume capability.

Revision ID: 4d0b2a3c5e6f
Revises: 3e8a1f2b9c0d
Create Date: 2026-05-17 19:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4d0b2a3c5e6f"
down_revision: Union[str, Sequence[str], None] = "3e8a1f2b9c0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "backtest_sessions",
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("backtest_sessions", "account_id")
