"""Trade routes for TradeLogger API."""

import json
from decimal import Decimal

from flasgger import swag_from
from flask import Blueprint, g, jsonify, request, send_from_directory

from src.models import Account, Trade, db
from src.services.trade_service import TradeService
from src.utils.jwt_utils import jwt_required

trades_bp = Blueprint("trades", __name__)


@trades_bp.route("/screenshots/<filename>")
def get_screenshot(filename):
    """Serve a screenshot file."""
    from flask import current_app

    screenshot_dir = current_app.config["SCREENSHOT_DIR"]
    return send_from_directory(screenshot_dir, filename)


@trades_bp.route("/trades", methods=["POST"])
@jwt_required
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
      401:
        description: Authentication required
    """
    data = request.form.to_dict() if request.form else request.get_json()

    # Parse exit_transactions if it's a JSON string (sent from widget via FormData)
    if "exit_transactions" in data and isinstance(data["exit_transactions"], str):
        try:
            data["exit_transactions"] = json.loads(data["exit_transactions"])
        except (json.JSONDecodeError, ValueError):
            data["exit_transactions"] = []

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["symbol", "direction", "entry_price"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    if "account_id" not in data or not data["account_id"]:
        return jsonify({"error": "Missing account_id"}), 400

    # Verify account exists and belongs to current user
    account = Account.query.filter_by(
        id=data["account_id"], user_id=g.current_user_id
    ).first()
    if not account:
        return jsonify({"error": "Invalid account_id"}), 400

    # Validate price logic based on direction
    direction = data.get("direction", "").lower()
    entry_price = data.get("entry_price")
    take_profit = data.get("take_profit")
    stop_loss = data.get("stop_loss")

    if entry_price and direction:
        entry_price = float(entry_price)

        if direction == "long":
            if take_profit is not None and float(take_profit) <= entry_price:
                return jsonify(
                    {
                        "error": "For LONG trades, take profit must be higher than entry price"
                    }
                ), 400
            if stop_loss is not None and float(stop_loss) >= entry_price:
                return jsonify(
                    {
                        "error": "For LONG trades, stop loss must be lower than entry price"
                    }
                ), 400
        elif direction == "short":
            if take_profit is not None and float(take_profit) >= entry_price:
                return jsonify(
                    {
                        "error": "For SHORT trades, take profit must be lower than entry price"
                    }
                ), 400
            if stop_loss is not None and float(stop_loss) <= entry_price:
                return jsonify(
                    {
                        "error": "For SHORT trades, stop loss must be higher than entry price"
                    }
                ), 400

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

    # Force user_id to current user
    data["user_id"] = g.current_user_id

    trade = TradeService.create_trade(data, screenshot_file)
    return jsonify(trade.to_dict()), 201


@trades_bp.route("/trades", methods=["GET"])
@jwt_required
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
      401:
        description: Authentication required
    """
    filters = {
        "symbol": request.args.get("symbol"),
        "direction": request.args.get("direction"),
        "status": request.args.get("status"),
        "account_id": request.args.get("account_id"),
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date"),
        "user_id": g.current_user_id,  # Enforce user isolation
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
@jwt_required
def get_pending_trades():
    """
    Get open positions (trades without exit price)
    ---
    tags:
      - Trades
    responses:
      200:
        description: List of open positions
      401:
        description: Authentication required
    """
    trades = TradeService.get_pending_trades(g.current_user_id)
    return jsonify([t.to_dict() for t in trades])


@trades_bp.route("/trades/<trade_id>", methods=["GET"])
@jwt_required
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
      401:
        description: Authentication required
      403:
        description: Access denied
    """
    trade = TradeService.get_trade(trade_id)
    if not trade:
        return jsonify({"error": "Trade not found"}), 404

    # IDOR protection: verify user owns this trade
    if trade.user_id != g.current_user_id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify(trade.to_dict())


@trades_bp.route("/trades/<trade_id>", methods=["PUT"])
@jwt_required
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
      401:
        description: Authentication required
      403:
        description: Access denied
    """
    # First verify ownership
    existing_trade = TradeService.get_trade(trade_id)
    if not existing_trade:
        return jsonify({"error": "Trade not found"}), 404

    if existing_trade.user_id != g.current_user_id:
        return jsonify({"error": "Access denied"}), 403

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

    # Validate price logic based on direction
    # Get existing or new direction and entry_price
    direction = data.get("direction")
    entry_price = data.get("entry_price")
    take_profit = data.get("take_profit")
    stop_loss = data.get("stop_loss")

    # If updating these fields, we need to validate - get existing trade for missing values
    if (
        take_profit is not None
        or stop_loss is not None
        or direction is not None
        or entry_price is not None
    ):
        direction = direction if direction else existing_trade.direction.value
        entry_price = (
            float(entry_price) if entry_price else float(existing_trade.entry_price)
        )
        take_profit = (
            float(take_profit)
            if take_profit is not None
            else (
                float(existing_trade.take_profit)
                if existing_trade.take_profit
                else None
            )
        )
        stop_loss = (
            float(stop_loss)
            if stop_loss is not None
            else (float(existing_trade.stop_loss) if existing_trade.stop_loss else None)
        )

        direction = direction.lower()

        if direction == "long":
            if take_profit is not None and take_profit <= entry_price:
                return jsonify(
                    {
                        "error": "For LONG trades, take profit must be higher than entry price"
                    }
                ), 400
            if stop_loss is not None and stop_loss >= entry_price:
                return jsonify(
                    {
                        "error": "For LONG trades, stop loss must be lower than entry price"
                    }
                ), 400
        elif direction == "short":
            if take_profit is not None and take_profit >= entry_price:
                return jsonify(
                    {
                        "error": "For SHORT trades, take profit must be lower than entry price"
                    }
                ), 400
            if stop_loss is not None and stop_loss <= entry_price:
                return jsonify(
                    {
                        "error": "For SHORT trades, stop loss must be higher than entry price"
                    }
                ), 400

    trade = TradeService.update_trade(trade_id, data)
    if not trade:
        return jsonify({"error": "Trade not found"}), 404
    return jsonify(trade.to_dict())


@trades_bp.route("/trades/<trade_id>", methods=["DELETE"])
@jwt_required
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
      401:
        description: Authentication required
      403:
        description: Access denied
    """
    # First verify ownership
    trade = TradeService.get_trade(trade_id)
    if not trade:
        return jsonify({"error": "Trade not found"}), 404

    if trade.user_id != g.current_user_id:
        return jsonify({"error": "Access denied"}), 403

    success = TradeService.delete_trade(trade_id)
    if not success:
        return jsonify({"error": "Trade not found"}), 404
    return jsonify({"message": "Trade deleted"}), 200


# =============================================================================
# Partial Exits API
# =============================================================================


@trades_bp.route("/trades/<trade_id>/partial-exits", methods=["GET"])
@jwt_required
def get_trade_partial_exits(trade_id):
    """
    Get all partial exits for a trade
    ---
    tags:
      - Partial Exits
    parameters:
      - name: trade_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: List of partial exits
      401:
        description: Authentication required
      403:
        description: Access denied
    """
    from src.models import TradePartialExit

    # Verify trade ownership first
    trade = Trade.query.filter_by(id=trade_id, user_id=g.current_user_id).first()
    if not trade:
        return jsonify({"error": "Trade not found or access denied"}), 404

    partial_exits = TradePartialExit.query.filter_by(trade_id=trade_id).all()
    return jsonify(
        {
            "partial_exits": [pe.to_dict() for pe in partial_exits],
            "total": len(partial_exits),
        }
    )


@trades_bp.route("/trades/<trade_id>/partial-exits", methods=["POST"])
@jwt_required
def create_trade_partial_exit(trade_id):
    """
    Add a partial exit to a trade
    ---
    tags:
      - Partial Exits
    parameters:
      - name: trade_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - qty
            - exit_price
          properties:
            qty:
              type: number
              example: 0.5
            exit_price:
              type: number
              example: 52000
            fees:
              type: number
              example: 5
    responses:
      201:
        description: Partial exit created
      401:
        description: Authentication required
      403:
        description: Access denied
    """
    from src.models import Trade, TradePartialExit

    # Verify trade ownership first
    trade = Trade.query.filter_by(id=trade_id, user_id=g.current_user_id).first()
    if not trade:
        return jsonify({"error": "Trade not found or access denied"}), 404

    data = request.get_json() or {}

    if not data.get("qty"):
        return jsonify({"error": "qty is required"}), 400
    if not data.get("exit_price"):
        return jsonify({"error": "exit_price is required"}), 400

    partial_exit = TradePartialExit(
        trade_id=trade_id,
        qty=Decimal(str(data["qty"])),
        exit_price=Decimal(str(data["exit_price"])),
        fees=Decimal(str(data.get("fees", 0))) if data.get("fees") else Decimal("0"),
    )

    db.session.add(partial_exit)

    # Recalculate P&L
    trade.pnl = TradeService.calculate_pnl(trade)

    db.session.commit()

    return jsonify(partial_exit.to_dict()), 201


@trades_bp.route("/partial-exits/<partial_exit_id>", methods=["PUT"])
@jwt_required
def update_partial_exit(partial_exit_id):
    """
    Update a partial exit
    ---
    tags:
      - Partial Exits
    parameters:
      - name: partial_exit_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Partial exit updated
      401:
        description: Authentication required
      403:
        description: Access denied
    """
    from src.models import Trade, TradePartialExit

    # Verify ownership through trade
    partial_exit = TradePartialExit.query.get(partial_exit_id)
    if not partial_exit:
        return jsonify({"error": "Partial exit not found"}), 404

    trade = Trade.query.filter_by(
        id=partial_exit.trade_id, user_id=g.current_user_id
    ).first()
    if not trade:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}

    if "qty" in data:
        partial_exit.qty = Decimal(str(data["qty"]))
    if "exit_price" in data:
        partial_exit.exit_price = Decimal(str(data["exit_price"]))
    if "fees" in data:
        partial_exit.fees = Decimal(str(data["fees"]))

    # Recalculate P&L for the trade
    trade.pnl = TradeService.calculate_pnl(trade)

    db.session.commit()

    return jsonify(partial_exit.to_dict())


@trades_bp.route("/partial-exits/<partial_exit_id>", methods=["DELETE"])
@jwt_required
def delete_partial_exit(partial_exit_id):
    """
    Delete a partial exit
    ---
    tags:
      - Partial Exits
    parameters:
      - name: partial_exit_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Partial exit deleted
      401:
        description: Authentication required
      403:
        description: Access denied
    """
    from src.models import Trade, TradePartialExit

    # Verify ownership through trade
    partial_exit = TradePartialExit.query.get(partial_exit_id)
    if not partial_exit:
        return jsonify({"error": "Partial exit not found"}), 404

    trade = Trade.query.filter_by(
        id=partial_exit.trade_id, user_id=g.current_user_id
    ).first()
    if not trade:
        return jsonify({"error": "Access denied"}), 403

    trade_id = partial_exit.trade_id

    db.session.delete(partial_exit)

    # Recalculate P&L for the trade
    trade.pnl = TradeService.calculate_pnl(trade)

    db.session.commit()

    return jsonify({"message": "Partial exit deleted"})
