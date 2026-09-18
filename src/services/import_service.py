"""CSV import service for trade journal — parses broker exports and creates trades."""

import csv
import io
import json
from datetime import date, datetime
from decimal import Decimal

from src.models import Trade, TradeDirection, TradeOutcome, db


class ImportService:
    """Service for importing trades from CSV files."""

    BROKER_FORMATS = {
        "mt4": {
            "name": "MetaTrader 4/5",
            "columns": ["Ticket", "Open Time", "Type", "Size", "Symbol", "Open Price", "SL", "TP", "Close Price", "Commission", "Taxes", "Swap", "Profit"],
            "required": ["Symbol", "Open Price", "Type"],
        },
        "tradovate": {
            "name": "Tradovate",
            "columns": ["Fill Id", "Order Id", "Account Id", "Instrument", "Trade Date", "Trade Time", "Order Type", "Trade Action", "Quantity", "Price", "Commission", "P&L"],
            "required": ["Instrument", "Price", "Trade Action"],
        },
        "ctrader": {
            "name": "cTrader",
            "columns": ["Trade ID", "Open Time", "Symbol", "Direction", "Volume", "Open Price", "Close Price", "SL", "TP", "Commission", "Net Profit"],
            "required": ["Symbol", "Open Price", "Direction"],
        },
        "ninjatrader": {
            "name": "NinjaTrader",
            "columns": ["Instrument", "Action", "Quantity", "Entry Price", "Exit Price", "Entry Time", "Exit Time", "Commission", "Profit/Loss"],
            "required": ["Instrument", "Entry Price", "Action"],
        },
    }

    FORMAT_MAP = {
        # Map broker-specific names to our field names
        "symbol": ["symbol", "instrument", "pair"],
        "direction": ["direction", "type", "action", "trade action"],
        "entry_price": ["open price", "entry price", "price"],
        "exit_price": ["close price", "exit price"],
        "stop_loss": ["sl", "stop loss"],
        "take_profit": ["tp", "take profit"],
        "position_size": ["size", "volume", "quantity", "lots"],
        "fees": ["commission", "fees"],
        "pnl": ["profit", "pnl", "net profit", "profit/loss", "p&l"],
        "trade_date": ["open time", "trade date", "entry time"],
    }

    @staticmethod
    def detect_format(headers):
        """Detect broker format from CSV headers."""
        header_lower = [h.strip().lower() for h in headers]
        for fmt, config in ImportService.BROKER_FORMATS.items():
            expected = [c.lower() for c in config["columns"]]
            matches = sum(1 for h in header_lower if h in expected or any(h.startswith(e.split()[0].lower()) for e in expected))
            if matches >= len(config["required"]):
                return fmt
        return "generic"

    @staticmethod
    def map_columns(headers):
        """Map CSV column headers to our field names."""
        header_lower = [h.strip().lower() for h in headers]
        mapping = {}
        for field, alternatives in ImportService.FORMAT_MAP.items():
            for alt in alternatives:
                for i, h in enumerate(header_lower):
                    if alt == h or h.startswith(alt):
                        mapping[field] = i
                        break
                if field in mapping:
                    break
        return mapping

    @staticmethod
    def parse_direction(value):
        """Parse trade direction from various formats."""
        v = value.strip().lower()
        if v in ("buy", "long", "b"):
            return TradeDirection.LONG
        if v in ("sell", "short", "s"):
            return TradeDirection.SHORT
        return None

    @staticmethod
    def parse_decimal(value):
        """Parse decimal value, returning None if invalid."""
        if not value or not value.strip():
            return None
        try:
            return Decimal(str(value).replace(",", ""))
        except (ValueError, ArithmeticError):
            return None

    @staticmethod
    def parse_datetime(value):
        """Parse datetime from various formats."""
        if not value or not value.strip():
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y.%m.%d %H:%M", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def parse_csv(file_content, filename=None):
        """Parse CSV content and return rows with auto-detected format."""
        content = file_content.read() if hasattr(file_content, "read") else file_content
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return {"format": None, "headers": [], "rows": [], "mapping": {}}

        headers = rows[0]
        fmt = ImportService.detect_format(headers)
        mapping = ImportService.map_columns(headers)

        parsed = []
        for row in rows[1:]:
            if not row or all(cell.strip() == "" for cell in row):
                continue
            parsed.append(row)

        return {
            "format": fmt,
            "headers": headers,
            "rows": parsed,
            "mapping": mapping,
        }

    @staticmethod
    def import_trades(csv_data, user_id, account_id):
        """Parse CSV and create Trade objects. Returns import stats."""
        result = ImportService.parse_csv(csv_data)
        if not result["mapping"] or not result["rows"]:
            return {"imported": 0, "skipped": 0, "errors": 0, "error": "No data to import"}

        mapping = result["mapping"]
        imported = 0
        skipped = 0
        errors = 0

        for row in result["rows"]:
            try:
                symbol_idx = mapping.get("symbol")
                direction_idx = mapping.get("direction")
                entry_idx = mapping.get("entry_price")
                exit_idx = mapping.get("exit_price")
                sl_idx = mapping.get("stop_loss")
                tp_idx = mapping.get("take_profit")
                size_idx = mapping.get("position_size")
                fees_idx = mapping.get("fees")
                pnl_idx = mapping.get("pnl")
                date_idx = mapping.get("trade_date")

                if symbol_idx is None or entry_idx is None:
                    errors += 1
                    continue

                symbol = row[symbol_idx].strip().upper() if symbol_idx < len(row) else None
                entry_price = ImportService.parse_decimal(row[entry_idx]) if entry_idx < len(row) else None

                if not symbol or not entry_price:
                    errors += 1
                    continue

                direction = TradeDirection.LONG
                if direction_idx is not None and direction_idx < len(row):
                    parsed_dir = ImportService.parse_direction(row[direction_idx])
                    if parsed_dir:
                        direction = parsed_dir

                exit_price = ImportService.parse_decimal(row[exit_idx]) if exit_idx is not None and exit_idx < len(row) else None
                stop_loss = ImportService.parse_decimal(row[sl_idx]) if sl_idx is not None and sl_idx < len(row) else None
                take_profit = ImportService.parse_decimal(row[tp_idx]) if tp_idx is not None and tp_idx < len(row) else None
                position_size = ImportService.parse_decimal(row[size_idx]) if size_idx is not None and size_idx < len(row) else None
                fees = ImportService.parse_decimal(row[fees_idx]) if fees_idx is not None and fees_idx < len(row) else Decimal("0")
                pnl_value = ImportService.parse_decimal(row[pnl_idx]) if pnl_idx is not None and pnl_idx < len(row) else None

                trade_date = None
                if date_idx is not None and date_idx < len(row):
                    dt = ImportService.parse_datetime(row[date_idx])
                    if dt:
                        trade_date = dt.date()

                # Determine outcome and status
                is_closed = exit_price is not None or take_profit is not None
                outcome = None
                if is_closed and pnl_value is not None:
                    if pnl_value > 0:
                        outcome = TradeOutcome.WIN
                    elif pnl_value < 0:
                        outcome = TradeOutcome.LOSS
                    else:
                        outcome = TradeOutcome.BREAK_EVEN
                elif is_closed:
                    outcome = TradeOutcome.WIN

                # Check for duplicate
                existing = Trade.query.filter_by(
                    user_id=user_id,
                    symbol=symbol,
                    entry_price=entry_price,
                    trade_date=trade_date or date.today(),
                ).first()
                if existing:
                    skipped += 1
                    continue

                trade = Trade(
                    user_id=user_id,
                    account_id=account_id,
                    symbol=symbol,
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    fees=fees,
                    pnl=pnl_value,
                    outcome=outcome,
                    trade_date=trade_date or date.today(),
                    status="closed" if is_closed else "confirmed",
                )
                db.session.add(trade)
                imported += 1

            except Exception:
                errors += 1
                continue

        db.session.commit()
        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "format": result["format"],
        }

    @staticmethod
    def get_templates():
        """Return available CSV template formats."""
        return [
            {"id": "mt4", "name": "MetaTrader 4/5"},
            {"id": "tradovate", "name": "Tradovate"},
            {"id": "ctrader", "name": "cTrader"},
            {"id": "ninjatrader", "name": "NinjaTrader"},
        ]

    @staticmethod
    def generate_template(broker):
        """Generate a sample CSV template for a given broker."""
        config = ImportService.BROKER_FORMATS.get(broker)
        if not config:
            return None

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(config["columns"])
        output.seek(0)
        return output.getvalue()
