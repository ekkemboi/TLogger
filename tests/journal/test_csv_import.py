"""Tests for CSV import service."""

import json
import io
import csv
import pytest
from src.models import Trade, Account, db


class TestCSVImport:
    """Tests for CSV import flow."""

    IMPORT_URL = "/api/import/csv"
    PREVIEW_URL = "/api/import/preview"

    def _make_csv(self, rows, fmt="mt4"):
        """Create a CSV file-like object."""
        output = io.StringIO()
        if fmt == "mt4":
            writer = csv.writer(output)
            writer.writerow(["Ticket", "Open Time", "Type", "Size", "Symbol", "Open Price", "SL", "TP", "Close Price", "Commission", "Taxes", "Swap", "Profit"])
            for row in rows:
                writer.writerow(row)
        elif fmt == "tradovate":
            writer = csv.writer(output)
            writer.writerow(["Fill Id", "Order Id", "Account Id", "Instrument", "Trade Date", "Trade Time", "Order Type", "Trade Action", "Quantity", "Price", "Commission", "P&L"])
            for row in rows:
                writer.writerow(row)
        output.seek(0)
        return output

    def test_import_mt4_csv(self, auth_client, app, default_user, default_account):
        csv_data = self._make_csv([
            ["1001", "2024-01-01 10:00:00", "buy", "0.1", "EURUSD", "1.10000", "1.09500", "1.11000", "1.11000", "0", "0", "0", "100.00"],
        ], fmt="mt4")

        response = auth_client.post(
            self.IMPORT_URL,
            data={"file": (io.BytesIO(csv_data.getvalue().encode()), "trades.csv", "text/csv"), "account_id": default_account},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["imported"] == 1
        assert data["skipped"] == 0
        assert data["errors"] == 0

    def test_import_tradovate_csv(self, auth_client, app, default_user, default_account):
        csv_data = self._make_csv([
            ["1001", "2001", "123", "EURUSD", "2024-01-01", "10:00:00", "Limit", "Buy", "10000", "1.10000", "5.00", "50.00"],
        ], fmt="tradovate")

        response = auth_client.post(
            self.IMPORT_URL,
            data={"file": (io.BytesIO(csv_data.getvalue().encode()), "trades.csv", "text/csv"), "account_id": default_account},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["imported"] >= 1

    def test_import_empty_csv(self, auth_client, default_account):
        empty = io.StringIO()
        empty.write("Ticket,Open Time,Type,Size,Symbol,Open Price,SL,TP,Close Price,Commission,Taxes,Swap,Profit\n")
        empty.seek(0)

        response = auth_client.post(
            self.IMPORT_URL,
            data={"file": (io.BytesIO(empty.getvalue().encode()), "empty.csv", "text/csv"), "account_id": default_account},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["imported"] == 0

    def test_import_missing_account(self, auth_client):
        csv_data = self._make_csv([["1001", "2024-01-01", "buy", "0.1", "EURUSD", "1.10", "", "", "1.11", "0", "0", "0", "10"]])
        response = auth_client.post(
            self.IMPORT_URL,
            data={"file": (io.BytesIO(csv_data.getvalue().encode()), "trades.csv", "text/csv")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_import_unauthenticated(self, client, default_account):
        csv_data = self._make_csv([["1001", "2024-01-01", "buy", "0.1", "EURUSD", "1.10", "", "", "1.11", "0", "0", "0", "10"]])
        response = client.post(
            self.IMPORT_URL,
            data={"file": (io.BytesIO(csv_data.getvalue().encode()), "trades.csv", "text/csv"), "account_id": default_account},
            content_type="multipart/form-data",
        )
        assert response.status_code == 401

    def test_import_preview(self, auth_client, default_account):
        csv_data = self._make_csv([
            ["1001", "2024-01-01 10:00:00", "buy", "0.1", "EURUSD", "1.10000", "1.09500", "1.11000", "1.11000", "0", "0", "0", "100.00"],
            ["1002", "2024-01-02 14:00:00", "sell", "0.2", "GBPUSD", "1.25000", "1.25500", "1.24000", "1.24000", "0", "0", "0", "200.00"],
        ])

        response = auth_client.post(
            self.PREVIEW_URL,
            data={"file": (io.BytesIO(csv_data.getvalue().encode()), "trades.csv", "text/csv")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["rows"]) == 2
        assert "columns" in data
        assert "mapping" in data

    def test_import_duplicate_detection(self, auth_client, app, default_user, default_account):
        """Importing the same trade twice should skip the duplicate."""
        csv_data = self._make_csv([
            ["1001", "2024-01-01 10:00:00", "buy", "0.1", "EURUSD", "1.10000", "1.09500", "1.11000", "1.11000", "0", "0", "0", "100.00"],
        ])

        auth_client.post(
            self.IMPORT_URL,
            data={"file": (io.BytesIO(csv_data.getvalue().encode()), "trades.csv", "text/csv"), "account_id": default_account},
            content_type="multipart/form-data",
        )

        response = auth_client.post(
            self.IMPORT_URL,
            data={"file": (io.BytesIO(csv_data.getvalue().encode()), "trades.csv", "text/csv"), "account_id": default_account},
            content_type="multipart/form-data",
        )
        data = response.get_json()
        assert data["imported"] == 0
        assert data["skipped"] == 1


class TestCSVImportHistory:
    """Tests for import history tracking."""

    HISTORY_URL = "/api/import/history"
    IMPORT_URL = "/api/import/csv"

    def test_import_history(self, auth_client, app, default_user, default_account):
        csv_data = io.StringIO()
        csv_data.write("Ticket,Open Time,Type,Size,Symbol,Open Price,SL,TP,Close Price,Commission,Taxes,Swap,Profit\n")
        csv_data.write("1001,2024-01-01,buy,0.1,EURUSD,1.10,,,,,,,\n")
        csv_data.seek(0)

        auth_client.post(
            self.IMPORT_URL,
            data={"file": (io.BytesIO(csv_data.getvalue().encode()), "trades.csv", "text/csv"), "account_id": default_account},
            content_type="multipart/form-data",
        )

        response = auth_client.get(self.HISTORY_URL)
        assert response.status_code == 200
        data = response.get_json()
        assert "history" in data


class TestImportTemplates:
    """Tests for CSV template download."""

    TEMPLATES_URL = "/api/import/templates"

    def test_get_templates_list(self, auth_client):
        response = auth_client.get(self.TEMPLATES_URL)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["templates"]) > 0

    def test_get_mt4_template(self, auth_client):
        response = auth_client.get(f"{self.TEMPLATES_URL}/mt4")
        assert response.status_code == 200
        assert "text/csv" in response.content_type
