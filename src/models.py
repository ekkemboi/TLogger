"""SQLAlchemy models for TradeLogger."""

import uuid
from datetime import date, datetime
from enum import Enum

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class TradeDirection(str, Enum):
    """Trade direction enum."""

    LONG = "long"
    SHORT = "short"


class TradeStatus(str, Enum):
    """Trade status enum."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CLOSED = "closed"


class TradeOutcome(str, Enum):
    """Trade outcome enum."""

    WIN = "WIN"
    LOSS = "LOSS"
    BREAK_EVEN = "BREAK_EVEN"


class Account(db.Model):
    """Account model for multiple trading accounts."""

    __tablename__ = "accounts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    trades = db.relationship("Trade", backref="account", lazy=True)

    def to_dict(self):
        """Convert account to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Account {self.name} active={self.is_active}>"


class FavoriteProduct(db.Model):
    """Favorite product model for frequently traded symbols."""

    __tablename__ = "favorite_products"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = db.Column(db.String(50), nullable=False, unique=True)
    point_value = db.Column(db.Numeric(18, 8), nullable=True, default=1)
    fees = db.Column(db.Numeric(18, 8), nullable=True, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def to_dict(self):
        """Convert favorite product to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "point_value": float(self.point_value) if self.point_value else 1,
            "fees": float(self.fees) if self.fees else 0,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<FavoriteProduct {self.symbol} active={self.is_active}>"


class Trade(db.Model):
    """Trade model."""

    __tablename__ = "trades"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.id"), nullable=True)
    symbol = db.Column(db.String(50), nullable=False)
    direction = db.Column(db.Enum(TradeDirection), nullable=False)
    entry_price = db.Column(db.Numeric(18, 8), nullable=False)
    exit_price = db.Column(db.Numeric(18, 8), nullable=True)
    stop_loss = db.Column(db.Numeric(18, 8), nullable=True)
    take_profit = db.Column(db.Numeric(18, 8), nullable=True)
    position_size = db.Column(db.Numeric(18, 8), nullable=True)
    status = db.Column(
        db.Enum(TradeStatus), nullable=False, default=TradeStatus.CONFIRMED
    )
    outcome = db.Column(db.Enum(TradeOutcome), nullable=True, default=TradeOutcome.WIN)
    pnl = db.Column(db.Numeric(18, 8), nullable=True)
    fees = db.Column(db.Numeric(18, 8), nullable=True, default=0)
    trade_duration = db.Column(db.Interval, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, nullable=True)
    screenshot_path = db.Column(db.String(500), nullable=True)
    exit_transactions = db.Column(db.JSON, nullable=True)
    trade_date = db.Column(db.Date, nullable=True, default=date.today)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    confirmed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    exited_at = db.Column(db.DateTime(timezone=True), nullable=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        """Convert trade to dictionary."""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "symbol": self.symbol,
            "direction": self.direction.value if self.direction else None,
            "entry_price": float(self.entry_price) if self.entry_price else None,
            "exit_price": float(self.exit_price) if self.exit_price else None,
            "stop_loss": float(self.stop_loss) if self.stop_loss else None,
            "take_profit": float(self.take_profit) if self.take_profit else None,
            "position_size": float(self.position_size) if self.position_size else None,
            "status": self.status.value if self.status else None,
            "outcome": self.outcome.value.lower() if self.outcome else "win",
            "pnl": float(self.pnl) if self.pnl else None,
            "fees": float(self.fees) if self.fees else None,
            "trade_duration": str(self.trade_duration) if self.trade_duration else None,
            "notes": self.notes,
            "tags": self.tags,
            "screenshot_path": self.screenshot_path,
            "exit_transactions": self.exit_transactions,
            "trade_date": self.trade_date.isoformat() if self.trade_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at.isoformat()
            if self.confirmed_at
            else None,
            "exited_at": self.exited_at.isoformat() if self.exited_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Trade {self.symbol} {self.direction} {self.status}>"
