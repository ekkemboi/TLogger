"""Metrics routes for TradeLogger API."""

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from src.models import Trade, TradeDirection, TradeOutcome, db

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Get trading metrics and statistics
    ---
    tags:
      - Metrics
    parameters:
      - name: account_id
        in: query
        type: string
        description: Filter metrics by account ID
      - name: start_date
        in: query
        type: string
        description: Filter trades from this date (YYYY-MM-DD)
      - name: end_date
        in: query
        type: string
        description: Filter trades until this date (YYYY-MM-DD)
    responses:
      200:
        description: Trading metrics including win rate, P&L, and statistics
        schema:
          type: object
          properties:
            total_trades:
              type: integer
            winning_trades:
              type: integer
            losing_trades:
              type: integer
            win_rate:
              type: number
            total_pnl:
              type: number
            profit_factor:
              type: number
            avg_win:
              type: number
            avg_loss:
              type: number
            best_trade:
              type: number
            worst_trade:
              type: number
            by_symbol:
              type: array
              items:
                type: object
                properties:
                  symbol:
                    type: string
                  count:
                    type: integer
                  pnl:
                    type: number
            by_direction:
              type: array
              items:
                type: object
                properties:
                  direction:
                    type: string
                  count:
                    type: integer
                  pnl:
                    type: number
            recent_pnl:
              type: array
              items:
                type: number
    """
    account_id = request.args.get("account_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Trade.query
    if account_id:
        query = query.filter(Trade.account_id == account_id)
    if start_date:
        query = query.filter(Trade.trade_date >= start_date)
    if end_date:
        query = query.filter(Trade.trade_date <= end_date)

    total_trades = query.count()

    # Use outcome field instead of status for filtering
    trades_with_pnl = query.filter(Trade.outcome.isnot(None)).all()

    winning_trades = [
        t
        for t in trades_with_pnl
        if t.outcome == TradeOutcome.WIN and t.pnl is not None
    ]
    losing_trades = [
        t
        for t in trades_with_pnl
        if t.outcome == TradeOutcome.LOSS and t.pnl is not None
    ]

    def get_signed_pnl(t):
        if t.pnl is None:
            return 0
        return t.pnl if t.outcome != TradeOutcome.LOSS else -t.pnl

    total_pnl = (
        sum(get_signed_pnl(t) for t in trades_with_pnl) if trades_with_pnl else 0
    )
    win_rate = len(winning_trades) / len(trades_with_pnl) if trades_with_pnl else 0

    avg_win = (
        sum(t.pnl for t in winning_trades) / len(winning_trades)
        if winning_trades
        else 0
    )
    avg_loss = (
        sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
    )

    best_trade = max((get_signed_pnl(t) for t in trades_with_pnl), default=0)
    worst_trade = min((get_signed_pnl(t) for t in trades_with_pnl), default=0)

    gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
    gross_loss = sum(t.pnl for t in losing_trades) if losing_trades else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    symbol_query = db.session.query(
        Trade.symbol,
        func.count(Trade.id).label("count"),
        func.sum(Trade.pnl).label("pnl"),
    ).filter(Trade.pnl.isnot(None))
    if account_id:
        symbol_query = symbol_query.filter(Trade.account_id == account_id)
    if start_date:
        symbol_query = symbol_query.filter(Trade.trade_date >= start_date)
    if end_date:
        symbol_query = symbol_query.filter(Trade.trade_date <= end_date)
    symbol_stats = symbol_query.group_by(Trade.symbol).all()

    direction_query = db.session.query(
        Trade.direction,
        func.count(Trade.id).label("count"),
        func.sum(Trade.pnl).label("pnl"),
    ).filter(Trade.pnl.isnot(None))
    if account_id:
        direction_query = direction_query.filter(Trade.account_id == account_id)
    if start_date:
        direction_query = direction_query.filter(Trade.trade_date >= start_date)
    if end_date:
        direction_query = direction_query.filter(Trade.trade_date <= end_date)
    direction_stats = direction_query.group_by(Trade.direction).all()

    recent_query = Trade.query.filter(Trade.pnl.isnot(None))
    if account_id:
        recent_query = recent_query.filter(Trade.account_id == account_id)
    if start_date:
        recent_query = recent_query.filter(Trade.trade_date >= start_date)
    if end_date:
        recent_query = recent_query.filter(Trade.trade_date <= end_date)
    recent_trades = recent_query.order_by(Trade.created_at.desc()).limit(10).all()
    recent_pnl = [float(t.pnl) for t in reversed(recent_trades)]

    return jsonify(
        {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 4),
            "total_pnl": float(total_pnl),
            "avg_pnl_per_trade": (
                float(total_pnl / len(trades_with_pnl)) if trades_with_pnl else 0
            ),
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "best_trade": float(best_trade),
            "worst_trade": float(worst_trade),
            "profit_factor": float(round(profit_factor, 2)),
            "by_symbol": [
                {"symbol": s, "count": c, "pnl": float(p) if p else 0}
                for s, c, p in symbol_stats
            ],
            "by_direction": [
                {"direction": d.value, "count": c, "pnl": float(p) if p else 0}
                for d, c, p in direction_stats
            ],
            "recent_pnl": recent_pnl,
        }
    )
