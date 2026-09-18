"""Add backtest models and is_backtest flag to Account.

Revision ID: 3e8a1f2b9c0d
Revises: c36620decf8c
Create Date: 2026-05-17 15:07:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3e8a1f2b9c0d"
down_revision: Union[str, Sequence[str], None] = "c36620decf8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    # Add is_backtest column to accounts table
    op.add_column("accounts", sa.Column("is_backtest", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # Create assets table
    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("symbol", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("point_value", sa.Numeric(18, 8), nullable=True, server_default=sa.text("1")),
        sa.Column("tick_size", sa.Numeric(18, 8), nullable=True),
        sa.Column("min_lot", sa.Numeric(18, 8), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create price_candles table
    op.create_table(
        "price_candles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("symbol", sa.String(50), nullable=False),
        sa.Column("timeframe", sa.String(10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(18, 8), nullable=False),
        sa.Column("high", sa.Numeric(18, 8), nullable=False),
        sa.Column("low", sa.Numeric(18, 8), nullable=False),
        sa.Column("close", sa.Numeric(18, 8), nullable=False),
        sa.Column("volume", sa.Numeric(18, 2), nullable=True),
    )
    op.create_index("ix_candles_symbol_tf_ts", "price_candles", ["symbol", "timeframe", "timestamp"])

    # Create backtest_sessions table
    op.create_table(
        "backtest_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("symbol", sa.String(50), nullable=False),
        sa.Column("timeframe", sa.String(10), nullable=False),
        sa.Column("starting_balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("current_balance", sa.Numeric(18, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create broker_connections table
    op.create_table(
        "broker_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("broker", sa.String(50), nullable=False),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("api_secret", sa.Text(), nullable=True),
        sa.Column("account_id", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_interval", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("broker_connections")
    op.drop_table("backtest_sessions")
    op.drop_index("ix_candles_symbol_tf_ts", table_name="price_candles")
    op.drop_table("price_candles")
    op.drop_table("assets")
    op.drop_column("accounts", "is_backtest")
