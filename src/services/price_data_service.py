"""Historical price data import service — parses OHLCV CSV files and creates candles."""

import csv
import io
from datetime import datetime
from decimal import Decimal

from src.models import Asset, PriceCandle, db


class PriceDataImportService:
    """Service for importing historical price data from CSV files."""

    PRICE_COLUMNS = {
        "timestamp": ["timestamp", "date", "time", "datetime", "date/time", "date_time"],
        "open": ["open", "opening price", "opening"],
        "high": ["high", "high price", "high of day"],
        "low": ["low", "low price", "low of day"],
        "close": ["close", "closing price", "closing"],
        "volume": ["volume", "vol", "tick volume", "tickvol"],
    }

    @staticmethod
    def detect_price_format(headers):
        """Detect if headers look like OHLCV price data."""
        header_lower = [h.strip().lower() for h in headers]
        score = 0
        for field, alternatives in PriceDataImportService.PRICE_COLUMNS.items():
            for alt in alternatives:
                if alt in header_lower:
                    score += 1
                    break
        return score >= 4  # At least timestamp, open, high, close

    @staticmethod
    def map_price_columns(headers):
        """Map CSV headers to OHLCV fields."""
        header_lower = [h.strip().lower() for h in headers]
        mapping = {}
        for field, alternatives in PriceDataImportService.PRICE_COLUMNS.items():
            for i, h in enumerate(header_lower):
                if h in alternatives:
                    mapping[field] = i
                    break
        return mapping

    @staticmethod
    def parse_csv(file_content):
        """Parse CSV content and return rows with column mapping."""
        content = file_content.read() if hasattr(file_content, "read") else file_content
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return {"valid": False, "error": "Empty CSV file"}

        headers = rows[0]
        mapping = PriceDataImportService.map_price_columns(headers)

        if mapping.get("timestamp") is None or mapping.get("open") is None or mapping.get("high") is None or mapping.get("low") is None or mapping.get("close") is None:
            return {"valid": False, "error": "CSV must have at least: timestamp, open, high, low, close columns"}

        parsed = []
        for row in rows[1:]:
            if not row or all(cell.strip() == "" for cell in row):
                continue
            parsed.append(row)

        return {
            "valid": True,
            "headers": headers,
            "mapping": mapping,
            "rows": parsed,
            "total_rows": len(parsed),
        }

    @staticmethod
    def import_price_data(csv_data, symbol, timeframe):
        """Parse CSV and create PriceCandle records. Returns import stats."""
        result = PriceDataImportService.parse_csv(csv_data)
        if not result["valid"]:
            return {"imported": 0, "skipped": 0, "errors": 0, "error": result.get("error")}

        asset = Asset.query.filter_by(symbol=symbol.upper()).first()
        if not asset:
            return {"imported": 0, "skipped": 0, "errors": 0, "error": f"Asset '{symbol}' not found. Create it first via /api/backtest/assets"}

        mapping = result["mapping"]
        imported = 0
        skipped = 0
        errors = 0

        for row in result["rows"]:
            try:
                ts_idx = mapping["timestamp"]
                o_idx = mapping["open"]
                h_idx = mapping["high"]
                l_idx = mapping["low"]
                c_idx = mapping["close"]
                v_idx = mapping.get("volume")

                if ts_idx >= len(row) or o_idx >= len(row):
                    errors += 1
                    continue

                timestamp_str = row[ts_idx].strip()
                if not timestamp_str:
                    errors += 1
                    continue

                timestamp = PriceDataImportService._parse_timestamp(timestamp_str)
                if not timestamp:
                    errors += 1
                    continue

                open_val = PriceDataImportService._parse_decimal(row[o_idx])
                high_val = PriceDataImportService._parse_decimal(row[h_idx]) if h_idx < len(row) else None
                low_val = PriceDataImportService._parse_decimal(row[l_idx]) if l_idx < len(row) else None
                close_val = PriceDataImportService._parse_decimal(row[c_idx]) if c_idx < len(row) else None
                volume_val = PriceDataImportService._parse_decimal(row[v_idx]) if v_idx is not None and v_idx < len(row) else None

                if not all([open_val, high_val, low_val, close_val]):
                    errors += 1
                    continue

                existing = PriceCandle.query.filter_by(
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                    timestamp=timestamp,
                ).first()
                if existing:
                    skipped += 1
                    continue

                candle = PriceCandle(
                    asset_id=asset.id,
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=open_val,
                    high=high_val,
                    low=low_val,
                    close=close_val,
                    volume=volume_val,
                )
                db.session.add(candle)
                imported += 1

            except Exception:
                errors += 1
                continue

        db.session.commit()
        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "total": result["total_rows"],
        }

    @staticmethod
    def generate_price_template():
        """Generate a sample CSV template for OHLCV price data."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        writer.writerow(["2024-01-01 00:00:00", "1.10000", "1.10500", "1.09800", "1.10300", "1000"])
        writer.writerow(["2024-01-01 01:00:00", "1.10300", "1.10800", "1.10100", "1.10600", "1200"])
        writer.writerow(["2024-01-01 02:00:00", "1.10600", "1.10900", "1.10200", "1.10400", "800"])
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def _parse_timestamp(value):
        """Parse timestamp from various formats."""
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y.%m.%d %H:%M", "%Y-%m-%d", "%m/%d/%Y %H:%M", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        try:
            from datetime import timezone
            return datetime.fromisoformat(value.strip())
        except (ValueError, AttributeError):
            pass
        return None

    @staticmethod
    def _parse_decimal(value):
        if not value or not value.strip():
            return None
        try:
            return Decimal(str(value).replace(",", ""))
        except (ValueError, ArithmeticError):
            return None
