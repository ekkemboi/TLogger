"""Analytics API routes."""

from flasgger import swag_from
from flask import Blueprint, g, jsonify, request

from src.models import Account
from src.services.analytics_service import AnalyticsService
from src.utils.jwt_utils import jwt_required

analytics_bp = Blueprint("analytics", __name__)


def _get_account_id():
    """Get account_id from query params if provided."""
    return request.args.get("account_id")


@analytics_bp.route("/analytics/time-based", methods=["GET"])
@jwt_required
def time_based():
    group_by = request.args.get("group_by", "hour")
    result = AnalyticsService.get_time_based(
        user_id=g.current_user_id,
        group_by=group_by,
        account_id=_get_account_id(),
    )
    return jsonify(result)


@analytics_bp.route("/analytics/calendar", methods=["GET"])
@jwt_required
def calendar():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    if not year or not month:
        return jsonify({"error": "year and month are required"}), 400

    result = AnalyticsService.get_calendar(
        user_id=g.current_user_id,
        year=year,
        month=month,
        account_id=_get_account_id(),
    )
    return jsonify(result)


@analytics_bp.route("/analytics/monte-carlo", methods=["POST"])
@jwt_required
def monte_carlo():
    data = request.get_json() or {}
    simulations = data.get("simulations", 1000)

    result = AnalyticsService.run_monte_carlo(
        user_id=g.current_user_id,
        simulations=simulations,
        account_id=data.get("account_id") or _get_account_id(),
    )
    if result is None:
        return jsonify({"error": "Not enough trades to run simulation"}), 400
    return jsonify(result)


@analytics_bp.route("/analytics/drawdown", methods=["GET"])
@jwt_required
def drawdown():
    result = AnalyticsService.get_drawdown(
        user_id=g.current_user_id,
        account_id=_get_account_id(),
    )
    return jsonify(result)


@analytics_bp.route("/analytics/tags", methods=["GET"])
@jwt_required
def tag_analysis():
    result = AnalyticsService.get_tag_analysis(
        user_id=g.current_user_id,
        account_id=_get_account_id(),
    )
    return jsonify(result)


@analytics_bp.route("/analytics/equity", methods=["GET"])
@jwt_required
def equity_curve():
    result = AnalyticsService.get_equity_curve(
        user_id=g.current_user_id,
        account_id=_get_account_id(),
    )
    return jsonify(result)


@analytics_bp.route("/analytics/risk-metrics", methods=["GET"])
@jwt_required
def risk_metrics():
    result = AnalyticsService.get_risk_metrics(
        user_id=g.current_user_id,
        account_id=_get_account_id(),
    )
    return jsonify(result)
