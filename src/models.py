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


class User(db.Model):
    """User model for authentication."""

    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(500), nullable=True)

    # Auth fields
    auth_provider = db.Column(db.String(20), nullable=False, default="email")
    google_id = db.Column(db.String(100), nullable=True, unique=True)
    password_hash = db.Column(db.String(255), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    trades = db.relationship("Trade", backref="user", lazy=True)
    favorites = db.relationship("FavoriteProduct", backref="user", lazy=True)
    accounts = db.relationship("Account", backref="user", lazy=True)

    def to_dict(self):
        """Convert user to dictionary (no sensitive fields)."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "profile_picture": self.profile_picture,
            "auth_provider": self.auth_provider,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<User {self.email} active={self.is_active}>"


class Account(db.Model):
    """Account model for multiple trading accounts."""

    __tablename__ = "accounts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    opening_balance = db.Column(db.Numeric(18, 2), nullable=True, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_backtest = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    trades = db.relationship("Trade", backref="account", lazy=True)

    def to_dict(self):
        """Convert account to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "opening_balance": float(self.opening_balance)
            if self.opening_balance
            else 0,
            "is_active": self.is_active,
            "is_backtest": self.is_backtest,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Account {self.name} active={self.is_active}>"


class FavoriteProduct(db.Model):
    """Favorite product model for frequently traded symbols."""

    __tablename__ = "favorite_products"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    symbol = db.Column(db.String(50), nullable=False)
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
            "user_id": self.user_id,
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
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.id"), nullable=False)
    symbol = db.Column(db.String(50), nullable=False)
    direction = db.Column(
        db.Enum(
            TradeDirection,
            native_mode=False,
            values_callable=lambda x: [e.value for e in TradeDirection],
        ),
        nullable=False,
    )
    entry_price = db.Column(db.Numeric(18, 8), nullable=False)
    exit_price = db.Column(db.Numeric(18, 8), nullable=True)
    stop_loss = db.Column(db.Numeric(18, 8), nullable=True)
    take_profit = db.Column(db.Numeric(18, 8), nullable=True)
    position_size = db.Column(db.Numeric(18, 8), nullable=True)
    status = db.Column(
        db.Enum(
            TradeStatus,
            native_mode=False,
            values_callable=lambda x: [e.value for e in TradeStatus],
        ),
        nullable=False,
        default=TradeStatus.CONFIRMED,
    )
    outcome = db.Column(
        db.Enum(
            TradeOutcome,
            native_mode=False,
            values_callable=lambda x: [e.value for e in TradeOutcome],
        ),
        nullable=True,
    )
    pnl = db.Column(db.Numeric(18, 8), nullable=True)
    fees = db.Column(db.Numeric(18, 8), nullable=True, default=0)
    trade_duration = db.Column(db.Interval, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, nullable=True)
    screenshot_path = db.Column(db.String(500), nullable=True)
    exit_transactions = db.Column(db.JSON, nullable=True)
    # New: relationship to TradePartialExit table
    partial_exits = db.relationship(
        "TradePartialExit", backref="trade", lazy=True, cascade="all, delete-orphan"
    )
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
            "user_id": self.user_id,
            "account_id": self.account_id,
            "account_name": self.account.name if self.account else None,
            "symbol": self.symbol,
            "direction": self.direction.value if self.direction else None,
            "entry_price": float(self.entry_price) if self.entry_price else None,
            "exit_price": float(self.exit_price) if self.exit_price else None,
            "stop_loss": float(self.stop_loss) if self.stop_loss else None,
            "take_profit": float(self.take_profit) if self.take_profit else None,
            "position_size": float(self.position_size) if self.position_size else None,
            "status": "closed" if self.outcome else "confirmed",
            "outcome": self.outcome.value.lower() if self.outcome else "win",
            "pnl": float(self.pnl) if self.pnl else None,
            "fees": float(self.fees) if self.fees else None,
            "trade_duration": str(self.trade_duration) if self.trade_duration else None,
            "notes": self.notes,
            "tags": self.tags,
            "screenshot_path": self.screenshot_path,
            "exit_transactions": self.exit_transactions,
            "partial_exits": [pe.to_dict() for pe in self.partial_exits]
            if self.partial_exits
            else [],
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


class TradePartialExit(db.Model):
    """Model for trade partial exits - separate table for better querying."""

    __tablename__ = "trade_partial_exits"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trade_id = db.Column(db.String(36), db.ForeignKey("trades.id"), nullable=False)
    qty = db.Column(db.Numeric(18, 8), nullable=False)
    exit_price = db.Column(db.Numeric(18, 8), nullable=False)
    fees = db.Column(db.Numeric(18, 8), nullable=True, default=0)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def to_dict(self):
        """Convert partial exit to dictionary."""
        return {
            "id": self.id,
            "trade_id": self.trade_id,
            "qty": float(self.qty) if self.qty else None,
            "exit_price": float(self.exit_price) if self.exit_price else None,
            "fees": float(self.fees) if self.fees else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<TradePartialExit trade={self.trade_id} qty={self.qty}>"


class Asset(db.Model):
    """Asset/symbol with metadata for backtesting."""

    __tablename__ = "assets"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=True)
    asset_type = db.Column(db.String(50), nullable=False)
    point_value = db.Column(db.Numeric(18, 8), nullable=True, default=1)
    tick_size = db.Column(db.Numeric(18, 8), nullable=True)
    min_lot = db.Column(db.Numeric(18, 8), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "asset_type": self.asset_type,
            "point_value": float(self.point_value) if self.point_value else 1,
            "tick_size": float(self.tick_size) if self.tick_size else None,
            "min_lot": float(self.min_lot) if self.min_lot else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Asset {self.symbol} ({self.asset_type})>"


class PriceCandle(db.Model):
    """OHLCV candle data for backtesting."""

    __tablename__ = "price_candles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = db.Column(db.String(36), db.ForeignKey("assets.id"), nullable=False)
    symbol = db.Column(db.String(50), nullable=False)
    timeframe = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)
    open = db.Column(db.Numeric(18, 8), nullable=False)
    high = db.Column(db.Numeric(18, 8), nullable=False)
    low = db.Column(db.Numeric(18, 8), nullable=False)
    close = db.Column(db.Numeric(18, 8), nullable=False)
    volume = db.Column(db.Numeric(18, 2), nullable=True)

    __table_args__ = (
        db.Index("ix_candles_symbol_tf_ts", "symbol", "timeframe", "timestamp"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "open": float(self.open) if self.open else None,
            "high": float(self.high) if self.high else None,
            "low": float(self.low) if self.low else None,
            "close": float(self.close) if self.close else None,
            "volume": float(self.volume) if self.volume else None,
        }

    def __repr__(self):
        return f"<PriceCandle {self.symbol} {self.timeframe} {self.timestamp}>"


class BacktestSession(db.Model):
    """Backtesting replay session."""

    __tablename__ = "backtest_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.id"), nullable=True)
    symbol = db.Column(db.String(50), nullable=False)
    timeframe = db.Column(db.String(10), nullable=False)
    starting_balance = db.Column(db.Numeric(18, 2), nullable=False)
    current_balance = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "account_id": self.account_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "starting_balance": float(self.starting_balance) if self.starting_balance else 0,
            "current_balance": float(self.current_balance) if self.current_balance else float(self.starting_balance or 0),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f"<BacktestSession {self.symbol} {self.timeframe} [{self.status}]>"


class BrokerConnection(db.Model):
    """Broker API connection configuration for live trade sync."""

    __tablename__ = "broker_connections"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    broker = db.Column(db.String(50), nullable=False)
    label = db.Column(db.String(100), nullable=True)
    api_key = db.Column(db.Text, nullable=True)
    api_secret = db.Column(db.Text, nullable=True)
    account_id = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_sync_at = db.Column(db.DateTime(timezone=True), nullable=True)
    sync_interval = db.Column(db.Integer, nullable=False, default=60)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "broker": self.broker,
            "label": self.label,
            "account_id": self.account_id,
            "is_active": self.is_active,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "sync_interval": self.sync_interval,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<BrokerConnection {self.broker} {self.label}>"
