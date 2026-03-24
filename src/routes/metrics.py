"""Metrics routes for TradeLogger API."""

from flask import Blueprint, jsonify
from sqlalchemy import func

from src.models import Trade, TradeDirection, TradeStatus, db

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Get trading metrics and statistics
    ---
    tags:
      - Metrics
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
    total_trades = Trade.query.count()
    confirmed_trades = Trade.query.filter(Trade.status == TradeStatus.CONFIRMED).count()
    closed_trades = Trade.query.filter(Trade.status == TradeStatus.CLOSED).count()

    trades_with_pnl = Trade.query.filter(Trade.pnl.isnot(None)).all()

    winning_trades = [t for t in trades_with_pnl if t.pnl > 0]
    losing_trades = [t for t in trades_with_pnl if t.pnl < 0]

    total_pnl = sum(t.pnl for t in trades_with_pnl) if trades_with_pnl else 0
    win_rate = len(winning_trades) / len(trades_with_pnl) if trades_with_pnl else 0

    avg_win = (
        sum(t.pnl for t in winning_trades) / len(winning_trades)
        if winning_trades
        else 0
    )
    avg_loss = (
        sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
    )

    best_trade = max((t.pnl for t in trades_with_pnl), default=0)
    worst_trade = min((t.pnl for t in trades_with_pnl), default=0)

    gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
    gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    symbol_stats = (
        db.session.query(
            Trade.symbol,
            func.count(Trade.id).label("count"),
            func.sum(Trade.pnl).label("pnl"),
        )
        .filter(Trade.pnl.isnot(None))
        .group_by(Trade.symbol)
        .all()
    )

    direction_stats = (
        db.session.query(
            Trade.direction,
            func.count(Trade.id).label("count"),
            func.sum(Trade.pnl).label("pnl"),
        )
        .filter(Trade.pnl.isnot(None))
        .group_by(Trade.direction)
        .all()
    )

    recent_trades = (
        Trade.query.filter(Trade.pnl.isnot(None))
        .order_by(Trade.created_at.desc())
        .limit(10)
        .all()
    )
    recent_pnl = [float(t.pnl) for t in reversed(recent_trades)]

    return jsonify(
        {
            "total_trades": total_trades,
            "confirmed_trades": confirmed_trades,
            "closed_trades": closed_trades,
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
            "profit_factor": round(profit_factor, 2),
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
