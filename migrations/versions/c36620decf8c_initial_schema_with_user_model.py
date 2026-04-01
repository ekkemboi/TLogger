"""initial_schema_with_user_model

Revision ID: c36620decf8c
Revises:
Create Date: 2026-04-01 20:02:59.484804

"""

from typing import Sequence, Union
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c36620decf8c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete initial schema with user authentication."""

    connection = op.get_bind()

    # Create enum types using raw SQL with IF NOT EXISTS
    connection.execute(
        sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tradedirection') THEN
                CREATE TYPE tradedirection AS ENUM ('long', 'short');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tradestatus') THEN
                CREATE TYPE tradestatus AS ENUM ('pending', 'confirmed', 'closed');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tradeoutcome') THEN
                CREATE TYPE tradeoutcome AS ENUM ('WIN', 'LOSS', 'BREAK_EVEN');
            END IF;
        END
        $$;
    """)
    )

    # ### Create users table ###
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("profile_picture", sa.String(length=500), nullable=True),
        sa.Column(
            "auth_provider",
            sa.String(length=20),
            nullable=False,
            server_default="email",
        ),
        sa.Column("google_id", sa.String(length=100), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_id"),
    )

    # ### Create accounts table ###
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "opening_balance", sa.Numeric(18, 2), nullable=True, server_default="0"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ### Create favorite_products table ###
    op.create_table(
        "favorite_products",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("point_value", sa.Numeric(18, 8), nullable=True, server_default="1"),
        sa.Column("fees", sa.Numeric(18, 8), nullable=True, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ### Create trades table using raw SQL for enum columns ###
    connection.execute(
        sa.text("""
        CREATE TABLE trades (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id),
            account_id VARCHAR(36) NOT NULL REFERENCES accounts(id),
            symbol VARCHAR(50) NOT NULL,
            direction tradedirection NOT NULL,
            entry_price NUMERIC(18, 8) NOT NULL,
            exit_price NUMERIC(18, 8),
            stop_loss NUMERIC(18, 8),
            take_profit NUMERIC(18, 8),
            position_size NUMERIC(18, 8),
            status tradestatus NOT NULL DEFAULT 'confirmed',
            outcome tradeoutcome DEFAULT 'WIN',
            pnl NUMERIC(18, 8),
            fees NUMERIC(18, 8) DEFAULT 0,
            trade_duration INTERVAL,
            notes TEXT,
            tags JSON,
            screenshot_path VARCHAR(500),
            exit_transactions JSON,
            trade_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            confirmed_at TIMESTAMP WITH TIME ZONE,
            exited_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    )

    # ### Create trade_partial_exits table ###
    op.create_table(
        "trade_partial_exits",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("trade_id", sa.String(length=36), nullable=False),
        sa.Column("qty", sa.Numeric(18, 8), nullable=False),
        sa.Column("exit_price", sa.Numeric(18, 8), nullable=False),
        sa.Column("fees", sa.Numeric(18, 8), nullable=True, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["trade_id"], ["trades.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ### Create default admin user ###
    admin_user_id = str(uuid.uuid4())
    now = datetime.utcnow()

    connection.execute(
        sa.text("""
            INSERT INTO users (id, email, name, auth_provider, is_active, created_at, updated_at)
            VALUES (:id, :email, :name, :auth_provider, :is_active, :created_at, :updated_at)
        """),
        {
            "id": admin_user_id,
            "email": "admin@tradelogger.local",
            "name": "Admin",
            "auth_provider": "email",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    )

    # ### Create default account for admin user ###
    default_account_id = str(uuid.uuid4())
    connection.execute(
        sa.text("""
            INSERT INTO accounts (id, user_id, name, is_active, created_at)
            VALUES (:id, :user_id, :name, :is_active, :created_at)
        """),
        {
            "id": default_account_id,
            "user_id": admin_user_id,
            "name": "Default",
            "is_active": True,
            "created_at": now,
        },
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("trade_partial_exits")
    op.drop_table("trades")
    op.drop_table("favorite_products")
    op.drop_table("accounts")
    op.drop_table("users")

    # Drop enum types
    connection = op.get_bind()
    connection.execute(sa.text("DROP TYPE IF EXISTS tradeoutcome"))
    connection.execute(sa.text("DROP TYPE IF EXISTS tradestatus"))
    connection.execute(sa.text("DROP TYPE IF EXISTS tradedirection"))
