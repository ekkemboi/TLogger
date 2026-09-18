"""Backtesting API routes for TradeLogger."""

from datetime import datetime
from decimal import Decimal

from flasgger import swag_from
from flask import Blueprint, g, jsonify, request

from src.models import Account, Asset, BacktestSession, PriceCandle, Trade, TradeDirection, TradeOutcome, db
from src.services.trade_service import TradeService
from src.utils.jwt_utils import jwt_required

backtest_bp = Blueprint("backtest", __name__)


@backtest_bp.route("/assets", methods=["GET"])
@jwt_required
def list_assets():
    assets = Asset.query.filter_by(is_active=True).order_by(Asset.symbol).all()
    return jsonify({"assets": [a.to_dict() for a in assets]})


@backtest_bp.route("/assets", methods=["POST"])
@jwt_required
def create_asset():
    data = request.get_json()
    if not data or "symbol" not in data or "asset_type" not in data:
        return jsonify({"error": "symbol and asset_type are required"}), 400

    existing = Asset.query.filter_by(symbol=data["symbol"].upper()).first()
    if existing:
        return jsonify(existing.to_dict())

    asset = Asset(
        symbol=data["symbol"].upper(),
        name=data.get("name"),
        asset_type=data["asset_type"],
        point_value=Decimal(str(data.get("point_value", 1))),
        tick_size=Decimal(str(data["tick_size"])) if data.get("tick_size") else None,
        min_lot=Decimal(str(data.get("min_lot", 0.01))),
    )
    db.session.add(asset)
    db.session.commit()
    return jsonify(asset.to_dict()), 201


@backtest_bp.route("/candles", methods=["POST"])
@jwt_required
def create_candle():
    data = request.get_json()
    if not data or "symbol" not in data or "timeframe" not in data:
        return jsonify({"error": "symbol, timeframe, and timestamp are required"}), 400

    asset = Asset.query.filter_by(symbol=data["symbol"].upper()).first()
    if not asset:
        return jsonify({"error": f"Asset {data['symbol']} not found. Create asset first."}), 400

    candle = PriceCandle(
        asset_id=asset.id,
        symbol=data["symbol"].upper(),
        timeframe=data["timeframe"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        open=Decimal(str(data["open"])),
        high=Decimal(str(data["high"])),
        low=Decimal(str(data["low"])),
        close=Decimal(str(data["close"])),
        volume=Decimal(str(data.get("volume", 0))),
    )
    db.session.add(candle)
    db.session.commit()
    return jsonify(candle.to_dict()), 201


@backtest_bp.route("/candles", methods=["GET"])
@jwt_required
def get_candles():
    symbol = request.args.get("symbol")
    timeframe = request.args.get("timeframe")
    if not symbol or not timeframe:
        return jsonify({"error": "symbol and timeframe are required"}), 400

    query = PriceCandle.query.filter_by(symbol=symbol.upper(), timeframe=timeframe)

    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        query = query.filter(PriceCandle.timestamp >= datetime.fromisoformat(start))
    if end:
        query = query.filter(PriceCandle.timestamp <= datetime.fromisoformat(end))

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 500, type=int)

    query = query.order_by(PriceCandle.timestamp.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "candles": [c.to_dict() for c in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
    })


@backtest_bp.route("/sessions", methods=["POST"])
@jwt_required
def create_session():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name")
    symbol = data.get("symbol")
    timeframe = data.get("timeframe")
    starting_balance = data.get("starting_balance")

    if not all([name, symbol, timeframe, starting_balance]):
        return jsonify({"error": "name, symbol, timeframe, and starting_balance are required"}), 400

    account = Account(
        user_id=g.current_user_id,
        name=name,
        opening_balance=Decimal(str(starting_balance)),
        is_backtest=True,
    )
    db.session.add(account)
    db.session.flush()

    session = BacktestSession(
        user_id=g.current_user_id,
        account_id=account.id,
        symbol=symbol.upper(),
        timeframe=timeframe,
        starting_balance=Decimal(str(starting_balance)),
        current_balance=Decimal(str(starting_balance)),
        start_date=(
            datetime.fromisoformat(data["start_date"])
            if data.get("start_date")
            else None
        ),
        end_date=(
            datetime.fromisoformat(data["end_date"])
            if data.get("end_date")
            else None
        ),
    )
    db.session.add(session)
    db.session.commit()

    return jsonify({
        "session": session.to_dict(),
        "account": account.to_dict(),
    }), 201


@backtest_bp.route("/sessions", methods=["GET"])
@jwt_required
def list_sessions():
    sessions = (
        BacktestSession.query.filter_by(user_id=g.current_user_id)
        .order_by(BacktestSession.created_at.desc())
        .all()
    )
    return jsonify({"sessions": [s.to_dict() for s in sessions]})


@backtest_bp.route("/sessions/<session_id>", methods=["GET"])
@jwt_required
def get_session(session_id):
    session = BacktestSession.query.filter_by(id=session_id, user_id=g.current_user_id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session.to_dict())


@backtest_bp.route("/sessions/<session_id>/controls", methods=["PUT"])
@jwt_required
def update_session_controls(session_id):
    session = BacktestSession.query.filter_by(id=session_id, user_id=g.current_user_id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "status" in data:
        if data["status"] in ("active", "paused", "completed"):
            session.status = data["status"]
            if data["status"] == "completed":
                session.completed_at = datetime.utcnow()

    if "speed" in data:
        speed = int(data["speed"])
        if speed < 1 or speed > 10:
            return jsonify({"error": "Speed must be between 1 and 10"}), 400

    db.session.commit()
    return jsonify(session.to_dict())


@backtest_bp.route("/sessions/<session_id>/trades", methods=["POST"])
@jwt_required
def enter_trade(session_id):
    session = BacktestSession.query.filter_by(id=session_id, user_id=g.current_user_id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    account_id = data.get("account_id")
    account = Account.query.filter_by(id=account_id, user_id=g.current_user_id).first()
    if not account:
        return jsonify({"error": "Invalid account_id"}), 400
    if not account.is_backtest:
        return jsonify({"error": "Backtest trades must use a backtest account"}), 400

    required = ["symbol", "direction", "entry_price"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    trade = Trade(
        user_id=g.current_user_id,
        account_id=account_id,
        symbol=data["symbol"].upper(),
        direction=TradeDirection(data["direction"]),
        entry_price=Decimal(str(data["entry_price"])),
        stop_loss=Decimal(str(data["stop_loss"])) if data.get("stop_loss") else None,
        take_profit=Decimal(str(data["take_profit"])) if data.get("take_profit") else None,
        position_size=Decimal(str(data["position_size"])) if data.get("position_size") else None,
        status="confirmed",
    )
    db.session.add(trade)
    db.session.commit()

    return jsonify(trade.to_dict()), 201


@backtest_bp.route("/sessions/<session_id>/summary", methods=["GET"])
@jwt_required
def get_session_summary(session_id):
    session = BacktestSession.query.filter_by(id=session_id, user_id=g.current_user_id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    trades = Trade.query.filter_by(user_id=g.current_user_id).all()
    total_trades = len(trades)
    wins = sum(1 for t in trades if t.outcome == TradeOutcome.WIN)
    losses = sum(1 for t in trades if t.outcome == TradeOutcome.LOSS)
    total_pnl = sum(float(t.pnl or 0) for t in trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    return jsonify({
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "max_drawdown": 0,
        "starting_balance": float(session.starting_balance),
        "current_balance": float(session.current_balance),
    })


@backtest_bp.route("/sessions/<session_id>", methods=["DELETE"])
@jwt_required
def delete_session(session_id):
    session = BacktestSession.query.filter_by(id=session_id, user_id=g.current_user_id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    db.session.delete(session)
    db.session.commit()
    return jsonify({"message": "Session deleted"})
