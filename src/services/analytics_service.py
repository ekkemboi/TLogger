"""Analytics service for advanced trade analysis."""

import random
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from src.models import Trade, TradeOutcome, db


class AnalyticsService:
    """Service for advanced trade analytics."""

    @staticmethod
    def get_time_based(user_id, group_by="hour", account_id=None):
        """Get win rate and P&L grouped by time period."""
        query = Trade.query.filter_by(user_id=user_id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        trades = query.all()
        if not trades:
            return {"results": []}

        groups = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "pnl": 0})

        for trade in trades:
            td = trade.trade_date or date.today()
            pnl = float(trade.pnl or 0)

            if group_by == "hour":
                key = td.isoformat()[:13]
            elif group_by == "day":
                key = td.isoformat()
            elif group_by == "session":
                hour = td.weekday()
                if hour < 8:
                    key = "Asia"
                elif hour < 16:
                    key = "London"
                else:
                    key = "New York"
            else:
                key = td.isoformat()

            groups[key]["trades"] += 1
            groups[key]["pnl"] += pnl
            if trade.outcome == TradeOutcome.WIN:
                groups[key]["wins"] += 1
            elif trade.outcome == TradeOutcome.LOSS:
                groups[key]["losses"] += 1

        results = []
        for key, data in sorted(groups.items()):
            results.append({
                "period": key,
                "trades": data["trades"],
                "wins": data["wins"],
                "losses": data["losses"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 2) if data["trades"] else 0,
                "pnl": round(data["pnl"], 2),
            })

        return {"results": results}

    @staticmethod
    def get_calendar(user_id, year, month, account_id=None):
        """Get performance calendar for a specific month."""
        query = Trade.query.filter_by(user_id=user_id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)

        trades = query.filter(
            Trade.trade_date >= start,
            Trade.trade_date < end,
        ).all()

        days = {}
        for trade in trades:
            td = trade.trade_date or date.today()
            pnl = float(trade.pnl or 0)
            if td.isoformat() not in days:
                days[td.isoformat()] = {"date": td.isoformat(), "pnl": 0, "trades": 0, "wins": 0, "losses": 0}
            days[td.isoformat()]["pnl"] += pnl
            days[td.isoformat()]["trades"] += 1
            if trade.outcome == TradeOutcome.WIN:
                days[td.isoformat()]["wins"] += 1
            elif trade.outcome == TradeOutcome.LOSS:
                days[td.isoformat()]["losses"] += 1

        return {
            "year": year,
            "month": month,
            "days": list(days.values()),
        }

    @staticmethod
    def run_monte_carlo(user_id, simulations=1000, account_id=None):
        """Run Monte Carlo simulation on actual trade outcomes."""
        query = Trade.query.filter_by(user_id=user_id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        trades = query.filter(Trade.pnl.isnot(None)).all()
        if not trades:
            return None

        pnls = [float(t.pnl or 0) for t in trades]
        results = []

        for _ in range(simulations):
            random.shuffle(pnls)
            running = 0
            curve = []
            for pnl in pnls:
                running += pnl
                curve.append(round(running, 2))
            results.append({
                "final_pnl": round(running, 2),
                "curve": curve,
            })

        results.sort(key=lambda r: r["final_pnl"])
        percentiles = {
            "p5": results[int(len(results) * 0.05)]["final_pnl"],
            "p25": results[int(len(results) * 0.25)]["final_pnl"],
            "p50": results[int(len(results) * 0.50)]["final_pnl"],
            "p75": results[int(len(results) * 0.75)]["final_pnl"],
            "p95": results[int(len(results) * 0.95)]["final_pnl"],
        }

        return {
            "simulations": simulations,
            "total_trades": len(trades),
            "percentiles": percentiles,
            "results": results[:10],
        }

    @staticmethod
    def get_drawdown(user_id, account_id=None):
        """Calculate drawdown metrics."""
        query = Trade.query.filter_by(user_id=user_id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        trades = query.filter(Trade.pnl.isnot(None)).order_by(Trade.trade_date.asc(), Trade.created_at.asc()).all()
        if not trades:
            return {"max_drawdown": 0, "average_drawdown": 0}

        cumulative = 0
        peak = 0
        drawdowns = []

        for trade in trades:
            cumulative += float(trade.pnl or 0)
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > 0:
                drawdowns.append(dd)

        max_dd = max(drawdowns) if drawdowns else 0
        avg_dd = sum(drawdowns) / len(drawdowns) if drawdowns else 0

        return {
            "max_drawdown": round(max_dd, 2),
            "average_drawdown": round(avg_dd, 2),
        }

    @staticmethod
    def get_tag_analysis(user_id, account_id=None):
        """Analyze win rate by tag combinations."""
        query = Trade.query.filter_by(user_id=user_id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        trades = query.all()
        combos = defaultdict(lambda: {"trades": 0, "wins": 0, "pnl": 0})

        for trade in trades:
            tags = trade.tags or []
            key = "+".join(sorted(tags)) if tags else "untagged"
            combos[key]["trades"] += 1
            combos[key]["pnl"] += float(trade.pnl or 0)
            if trade.outcome == TradeOutcome.WIN:
                combos[key]["wins"] += 1

        results = []
        for key, data in sorted(combos.items(), key=lambda x: x[1]["trades"], reverse=True):
            results.append({
                "tags": key.split("+") if key != "untagged" else [],
                "trades": data["trades"],
                "wins": data["wins"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 2) if data["trades"] else 0,
                "pnl": round(data["pnl"], 2),
            })

        return {"combinations": results}

    @staticmethod
    def get_equity_curve(user_id, account_id=None):
        """Calculate equity curve from cumulative P&L."""
        query = Trade.query.filter_by(user_id=user_id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        trades = query.filter(Trade.pnl.isnot(None)).order_by(Trade.trade_date.asc(), Trade.created_at.asc()).all()
        cumulative = 0
        points = []

        for trade in trades:
            cumulative += float(trade.pnl or 0)
            points.append({
                "date": trade.trade_date.isoformat() if trade.trade_date else None,
                "pnl": float(trade.pnl or 0),
                "cumulative": round(cumulative, 2),
            })

        return {"points": points}

    @staticmethod
    def get_risk_metrics(user_id, account_id=None):
        """Calculate risk-adjusted return metrics."""
        query = Trade.query.filter_by(user_id=user_id)
        if account_id:
            query = query.filter_by(account_id=account_id)

        trades = query.filter(Trade.pnl.isnot(None)).all()
        if not trades:
            return {"total_trades": 0, "sharpe_ratio": 0, "profit_factor": 0}

        pnls = [float(t.pnl or 0) for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        total_pnl = sum(pnls)
        avg_pnl = total_pnl / len(pnls)
        std_dev = (sum((p - avg_pnl) ** 2 for p in pnls) / len(pnls)) ** 0.5 if len(pnls) > 1 else 0

        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1

        return {
            "total_trades": len(trades),
            "total_pnl": round(total_pnl, 2),
            "avg_pnl": round(avg_pnl, 2),
            "sharpe_ratio": round(avg_pnl / std_dev * (252 ** 0.5), 2) if std_dev > 0 else 0,
            "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else 0,
            "win_rate": round(len(wins) / len(pnls) * 100, 2) if pnls else 0,
        }
