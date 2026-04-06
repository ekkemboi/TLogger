"""Trade service for business logic."""

from datetime import date, datetime
from decimal import Decimal

from src.models import (
    FavoriteProduct,
    Trade,
    TradeDirection,
    TradeOutcome,
    TradePartialExit,
    db,
)


class TradeService:
    """Service for trade operations."""

    @staticmethod
    def get_point_value(symbol):
        """Get point value from favorite product."""
        favorite = FavoriteProduct.query.filter_by(
            symbol=symbol.upper(), is_active=True
        ).first()
        if favorite and favorite.point_value:
            return Decimal(str(favorite.point_value))
        return Decimal("1")

    @staticmethod
    def get_default_fees(symbol):
        """Get default fees from favorite product."""
        favorite = FavoriteProduct.query.filter_by(
            symbol=symbol.upper(), is_active=True
        ).first()
        if favorite and favorite.fees:
            return Decimal(str(favorite.fees))
        return Decimal("0")

    @staticmethod
    def calculate_pnl(trade):
        """Calculate P&L for a trade with partial exits support."""
        entry = Decimal(str(trade.entry_price))
        size = Decimal(str(trade.position_size or 1))
        fees = Decimal(str(trade.fees or 0))
        point_value = TradeService.get_point_value(trade.symbol)

        is_long = trade.direction == TradeDirection.LONG

        # Check for partial exits from new table first
        if trade.partial_exits:
            total_pnl = Decimal("0")
            exited_qty = Decimal("0")

            # Calculate P&L from partial exits
            for pe in trade.partial_exits:
                qty = Decimal(str(pe.qty))
                exit_price = Decimal(str(pe.exit_price))
                exit_fees = Decimal(str(pe.fees or 0))
                if is_long:
                    total_pnl += (exit_price - entry) * qty * point_value - exit_fees
                else:
                    total_pnl += (entry - exit_price) * qty * point_value - exit_fees
                exited_qty += qty

            # Calculate remaining position using take_profit
            remaining_qty = size - exited_qty
            if remaining_qty > 0 and trade.take_profit:
                tp = Decimal(str(trade.take_profit))
                if is_long:
                    total_pnl += (tp - entry) * remaining_qty * point_value
                else:
                    total_pnl += (entry - tp) * remaining_qty * point_value

            return total_pnl

        # Fallback to JSON (for backward compatibility)
        if trade.exit_transactions:
            total_pnl = Decimal("0")
            exited_qty = Decimal("0")

            for exit_tx in trade.exit_transactions:
                qty = Decimal(str(exit_tx["qty"]))
                exit_price = Decimal(str(exit_tx["exit_price"]))
                exit_fees = Decimal(str(exit_tx.get("fees", 0)))
                if is_long:
                    total_pnl += (exit_price - entry) * qty * point_value - exit_fees
                else:
                    total_pnl += (entry - exit_price) * qty * point_value - exit_fees
                exited_qty += qty

            # Calculate remaining position using take_profit
            remaining_qty = size - exited_qty
            if remaining_qty > 0 and trade.take_profit:
                tp = Decimal(str(trade.take_profit))
                if is_long:
                    total_pnl += (tp - entry) * remaining_qty * point_value
                else:
                    total_pnl += (entry - tp) * remaining_qty * point_value

            return total_pnl

        outcome = trade.outcome

        if outcome == TradeOutcome.BREAK_EVEN:
            return -fees

        if outcome == TradeOutcome.LOSS:
            if trade.stop_loss:
                sl = Decimal(str(trade.stop_loss))
                if is_long:
                    return -abs((sl - entry) * size * point_value) - fees
                else:
                    return -abs((entry - sl) * size * point_value) - fees
            return -fees

        # Default: WIN - use take_profit
        if trade.take_profit:
            tp = Decimal(str(trade.take_profit))
            if is_long:
                return (tp - entry) * size * point_value - fees
            else:
                return (entry - tp) * size * point_value - fees
        return None

    @staticmethod
    def create_trade(data, screenshot_file=None):
        """Create a new trade journal entry."""
        exit_transactions = data.get("exit_transactions", [])
        take_profit = data.get("take_profit")
        exit_price = data.get("exit_price")
        symbol = data.get("symbol").upper()
        outcome = data.get("outcome")

        # Only uppercase if outcome was provided (not None)
        if outcome:
            outcome = outcome.upper()

        # Trade is closed if it has exit_price, take_profit, or exit_transactions
        is_closed = exit_price or take_profit or exit_transactions

        trade_date = None
        if data.get("trade_date"):
            trade_date = date.fromisoformat(data["trade_date"])

        # Get fees from favorite if not provided
        fees = data.get("fees")
        if fees is None:
            fees = TradeService.get_default_fees(symbol)
        else:
            fees = Decimal(str(fees))

        trade = Trade(
            user_id=data.get("user_id"),
            account_id=data.get("account_id"),
            symbol=symbol,
            direction=TradeDirection(data.get("direction")),
            entry_price=Decimal(str(data.get("entry_price"))),
            exit_price=(
                Decimal(str(data.get("exit_price"))) if data.get("exit_price") else None
            ),
            take_profit=(
                Decimal(str(data.get("take_profit")))
                if data.get("take_profit")
                else None
            ),
            stop_loss=(
                Decimal(str(data.get("stop_loss"))) if data.get("stop_loss") else None
            ),
            position_size=(
                Decimal(str(data.get("position_size")))
                if data.get("position_size")
                else None
            ),
            outcome=TradeOutcome(outcome)
            if outcome
            else (TradeOutcome.WIN if is_closed else None),
            fees=fees,
            notes=data.get("notes"),
            tags=data.get("tags"),
            exit_transactions=exit_transactions if exit_transactions else None,
            trade_date=trade_date,
            confirmed_at=datetime.utcnow(),
            exited_at=datetime.utcnow() if is_closed else None,
        )

        trade.pnl = TradeService.calculate_pnl(trade)

        db.session.add(trade)
        db.session.flush()  # Get trade.id before committing

        # Save partial exits to new table
        if exit_transactions:
            for tx in exit_transactions:
                partial_exit = TradePartialExit(
                    trade_id=trade.id,
                    qty=Decimal(str(tx.get("qty", 0))),
                    exit_price=Decimal(str(tx.get("exit_price", 0))),
                    fees=Decimal(str(tx.get("fees", 0)))
                    if tx.get("fees")
                    else Decimal("0"),
                )
                db.session.add(partial_exit)

        db.session.commit()

        if screenshot_file:
            from flask import current_app

            filename = f"{trade.id}.png"
            filepath = current_app.config["SCREENSHOT_DIR"] / filename
            screenshot_file.save(str(filepath))
            trade.screenshot_path = f"/api/screenshots/{filename}"
            db.session.commit()

        return trade

    @staticmethod
    def get_trades(filters=None, page=1, per_page=50):
        """Get trades with optional filters."""
        query = Trade.query

        if filters:
            # Always filter by user_id for security (user isolation)
            if filters.get("user_id"):
                query = query.filter(Trade.user_id == filters["user_id"])
            if filters.get("symbol"):
                query = query.filter(Trade.symbol == filters["symbol"].upper())
            if filters.get("direction"):
                query = query.filter(
                    Trade.direction == TradeDirection(filters["direction"].lower())
                )
            if filters.get("status"):
                # Check if outcome is not null to determine if trade is closed
                if filters["status"].lower() == "closed":
                    query = query.filter(Trade.outcome.isnot(None))
                elif filters["status"].lower() == "confirmed":
                    query = query.filter(Trade.outcome.is_(None))
            if filters.get("account_id"):
                query = query.filter(Trade.account_id == filters["account_id"])
            if filters.get("start_date"):
                query = query.filter(Trade.trade_date >= filters["start_date"])
            if filters.get("end_date"):
                query = query.filter(Trade.trade_date <= filters["end_date"])

        query = query.order_by(
            Trade.trade_date.desc().nullslast(), Trade.created_at.desc()
        )
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_trade(trade_id):
        """Get a single trade by ID."""
        return Trade.query.get(trade_id)

    @staticmethod
    def update_trade(trade_id, data):
        """Update a trade."""
        trade = Trade.query.get(trade_id)
        if not trade:
            return None

        if "take_profit" in data:
            trade.take_profit = (
                Decimal(str(data["take_profit"])) if data["take_profit"] else None
            )
            if data["take_profit"]:
                trade.exited_at = datetime.utcnow()
                # Set outcome to WIN when closing with take_profit
                trade.outcome = TradeOutcome.WIN

        if "exit_transactions" in data:
            trade.exit_transactions = data["exit_transactions"]
            if data["exit_transactions"]:
                trade.exited_at = datetime.utcnow()
                trade.outcome = TradeOutcome.WIN

        if "symbol" in data:
            trade.symbol = data["symbol"].upper()

        if "direction" in data:
            trade.direction = TradeDirection(data["direction"])

        if "entry_price" in data:
            trade.entry_price = Decimal(str(data["entry_price"]))

        if "stop_loss" in data:
            trade.stop_loss = (
                Decimal(str(data["stop_loss"])) if data["stop_loss"] else None
            )

        if "position_size" in data:
            trade.position_size = (
                Decimal(str(data["position_size"])) if data["position_size"] else None
            )

        if "notes" in data:
            trade.notes = data["notes"]
        if "tags" in data:
            trade.tags = data["tags"]
        if "fees" in data:
            trade.fees = Decimal(str(data["fees"]))
        if "trade_date" in data:
            trade.trade_date = date.fromisoformat(data["trade_date"])

        trade.pnl = TradeService.calculate_pnl(trade)
        trade.updated_at = datetime.utcnow()
        db.session.commit()
        return trade

    @staticmethod
    def delete_trade(trade_id):
        """Delete a trade."""
        trade = Trade.query.get(trade_id)
        if not trade:
            return False

        if trade.screenshot_path:
            from pathlib import Path

            from flask import current_app

            # screenshot_path is like /api/screenshots/{id}.png
            filename = trade.screenshot_path.split("/")[-1]
            filepath = current_app.config["SCREENSHOT_DIR"] / filename
            Path(filepath).unlink(missing_ok=True)

        db.session.delete(trade)
        db.session.commit()
        return True

    @staticmethod
    def get_pending_trades(user_id=None):
        """Get trades without exit price (open positions)."""
        query = Trade.query.filter(Trade.outcome.is_(None), Trade.take_profit.is_(None))
        if user_id:
            query = query.filter(Trade.user_id == user_id)
        return query.all()
