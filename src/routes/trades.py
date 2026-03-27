"""Trade routes for TradeLogger API."""

from flasgger import swag_from
from flask import Blueprint, jsonify, request, send_from_directory

from src.models import Account
from src.services.trade_service import TradeService

trades_bp = Blueprint("trades", __name__)


@trades_bp.route("/screenshots/<filename>")
def get_screenshot(filename):
    """Serve a screenshot file."""
    from flask import current_app

    screenshot_dir = current_app.config["SCREENSHOT_DIR"]
    return send_from_directory(screenshot_dir, filename)


@trades_bp.route("/trades", methods=["POST"])
def create_trade():
    """
    Create a new trade
    ---
    tags:
      - Trades
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - symbol
            - direction
            - entry_price
          properties:
            symbol:
              type: string
              example: BTCUSDT
            direction:
              type: string
              enum: [long, short]
              example: long
            entry_price:
              type: number
              example: 67200.00
            exit_price:
              type: number
              example: 68100.00
            stop_loss:
              type: number
              example: 66800.00
            take_profit:
              type: number
              example: 68500.00
            position_size:
              type: number
              example: 0.5
            notes:
              type: string
              example: Breakout trade
            tags:
              type: array
              items:
                type: string
              example: [breakout, btc]
    responses:
      201:
        description: Trade created successfully
      400:
        description: Missing required fields
    """
    data = request.form.to_dict() if request.form else request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["symbol", "direction", "entry_price"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    if "account_id" not in data or not data["account_id"]:
        return jsonify({"error": "Missing account_id"}), 400

    # Verify account exists
    account = Account.query.get(data["account_id"])
    if not account:
        return jsonify({"error": "Invalid account_id"}), 400

    if "outcome" in data and data["outcome"].upper() not in (
        "WIN",
        "LOSS",
        "BREAK_EVEN",
    ):
        return jsonify({"error": "Outcome must be 'win', 'loss', or 'break_even'"}), 400

    # Normalize outcome to uppercase to match enum
    if "outcome" in data:
        data["outcome"] = data["outcome"].upper()

    screenshot_file = request.files.get("screenshot")

    if "tags" in data and isinstance(data["tags"], str):
        data["tags"] = [t.strip() for t in data["tags"].split(",") if t.strip()]

    trade = TradeService.create_trade(data, screenshot_file)
    return jsonify(trade.to_dict()), 201


@trades_bp.route("/trades", methods=["GET"])
def get_trades():
    """
    Get all trades with optional filters
    ---
    tags:
      - Trades
    parameters:
      - name: symbol
        in: query
        type: string
        description: Filter by symbol
      - name: direction
        in: query
        type: string
        enum: [long, short]
      - name: status
        in: query
        type: string
        enum: [pending, confirmed, closed]
      - name: start_date
        in: query
        type: string
        format: date
        description: Filter trades from this date (ISO format)
      - name: end_date
        in: query
        type: string
        format: date
        description: Filter trades until this date
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 50
    responses:
      200:
        description: List of trades with pagination
    """
    filters = {
        "symbol": request.args.get("symbol"),
        "direction": request.args.get("direction"),
        "status": request.args.get("status"),
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date"),
    }
    filters = {k: v for k, v in filters.items() if v is not None}

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    pagination = TradeService.get_trades(filters, page, per_page)

    return jsonify(
        {
            "trades": [t.to_dict() for t in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "per_page": pagination.per_page,
        }
    )


@trades_bp.route("/trades/pending", methods=["GET"])
def get_pending_trades():
    """
    Get open positions (trades without exit price)
    ---
    tags:
      - Trades
    responses:
      200:
        description: List of open positions
    """
    trades = TradeService.get_pending_trades()
    return jsonify([t.to_dict() for t in trades])


@trades_bp.route("/trades/<trade_id>", methods=["GET"])
def get_trade(trade_id):
    """
    Get a single trade by ID
    ---
    tags:
      - Trades
    parameters:
      - name: trade_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Trade details
      404:
        description: Trade not found
    """
    trade = TradeService.get_trade(trade_id)
    if not trade:
        return jsonify({"error": "Trade not found"}), 404
    return jsonify(trade.to_dict())


@trades_bp.route("/trades/<trade_id>", methods=["PUT"])
def update_trade(trade_id):
    """
    Update a trade
    ---
    tags:
      - Trades
    parameters:
      - name: trade_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            exit_price:
              type: number
              description: Closing price (calculates P&L)
            notes:
              type: string
            tags:
              type: array
              items:
                type: string
            fees:
              type: number
    responses:
      200:
        description: Updated trade
      404:
        description: Trade not found
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "symbol" in data and (not data["symbol"] or not data["symbol"].strip()):
        return jsonify({"error": "Symbol must be a non-empty string"}), 400

    if "direction" in data and data["direction"] not in ("long", "short"):
        return jsonify({"error": "Direction must be 'long' or 'short'"}), 400

    if "entry_price" in data and (
        data["entry_price"] is None or float(data["entry_price"]) <= 0
    ):
        return jsonify({"error": "Entry price must be positive"}), 400

    if (
        "stop_loss" in data
        and data["stop_loss"] is not None
        and float(data["stop_loss"]) <= 0
    ):
        return jsonify({"error": "Stop loss must be positive"}), 400

    if (
        "take_profit" in data
        and data["take_profit"] is not None
        and float(data["take_profit"]) <= 0
    ):
        return jsonify({"error": "Take profit must be positive"}), 400

    if (
        "position_size" in data
        and data["position_size"] is not None
        and float(data["position_size"]) <= 0
    ):
        return jsonify({"error": "Position size must be positive"}), 400

    if "fees" in data and data["fees"] is not None and float(data["fees"]) < 0:
        return jsonify({"error": "Fees must be non-negative"}), 400

    trade = TradeService.update_trade(trade_id, data)
    if not trade:
        return jsonify({"error": "Trade not found"}), 404
    return jsonify(trade.to_dict())


@trades_bp.route("/trades/<trade_id>", methods=["DELETE"])
def delete_trade(trade_id):
    """
    Delete a trade
    ---
    tags:
      - Trades
    parameters:
      - name: trade_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Trade deleted
      404:
        description: Trade not found
    """
    success = TradeService.delete_trade(trade_id)
    if not success:
        return jsonify({"error": "Trade not found"}), 404
    return jsonify({"message": "Trade deleted"}), 200
