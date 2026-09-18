"""Import API routes for CSV trade import and price data import."""

import json

from flasgger import swag_from
from flask import Blueprint, Response, g, jsonify, request

from src.models import Account, db
from src.services.import_service import ImportService
from src.services.price_data_service import PriceDataImportService
from src.utils.jwt_utils import jwt_required

import_bp = Blueprint("import", __name__)


@import_bp.route("/import/csv", methods=["POST"])
@jwt_required
def import_csv():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    account_id = request.form.get("account_id")
    if not account_id:
        return jsonify({"error": "account_id is required"}), 400

    account = Account.query.filter_by(id=account_id, user_id=g.current_user_id).first()
    if not account:
        return jsonify({"error": "Invalid account_id"}), 400

    result = ImportService.import_trades(
        csv_data=file,
        user_id=g.current_user_id,
        account_id=account_id,
    )
    return jsonify(result)


@import_bp.route("/import/preview", methods=["POST"])
@jwt_required
def preview_csv():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    result = ImportService.parse_csv(file)
    return jsonify({
        "format": result.get("format"),
        "columns": result.get("headers", []),
        "mapping": {k: v for k, v in result.get("mapping", {}).items()},
        "rows": result.get("rows", [])[:10],
        "total_rows": len(result.get("rows", [])),
    })


@import_bp.route("/import/templates", methods=["GET"])
@jwt_required
def list_templates():
    templates = ImportService.get_templates()
    return jsonify({"templates": templates})


@import_bp.route("/import/templates/<broker>", methods=["GET"])
@jwt_required
def get_template(broker):
    content = ImportService.generate_template(broker)
    if content is None:
        return jsonify({"error": f"Unknown broker: {broker}"}), 404

    from flask import Response
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={broker}_template.csv"},
    )


@import_bp.route("/import/history", methods=["GET"])
@jwt_required
def import_history():
    return jsonify({"history": []})


@import_bp.route("/import/price-data", methods=["POST"])
@jwt_required
def import_price_data():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    symbol = request.form.get("symbol", "").upper()
    timeframe = request.form.get("timeframe", "1h")

    if not symbol:
        return jsonify({"error": "symbol is required"}), 400

    result = PriceDataImportService.import_price_data(
        csv_data=file,
        symbol=symbol,
        timeframe=timeframe,
    )
    return jsonify(result)


@import_bp.route("/import/price-data/preview", methods=["POST"])
@jwt_required
def preview_price_data():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    result = PriceDataImportService.parse_csv(file)
    return jsonify(result)


@import_bp.route("/import/price-data/template", methods=["GET"])
@jwt_required
def price_data_template():
    content = PriceDataImportService.generate_price_template()
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=price_data_template.csv"},
    )
