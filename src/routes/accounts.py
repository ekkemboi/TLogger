"""Account API routes."""

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from src.models import Account, Trade, TradeStatus, TradeOutcome, db

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("/accounts", methods=["GET"])
def get_accounts():
    """Get all active accounts with metrics."""
    accounts = Account.query.filter_by(is_active=True).all()

    result = []
    for account in accounts:
        trades = Trade.query.filter_by(account_id=account.id).all()
        trade_count = len(trades)
        trades_with_pnl = [
            t for t in trades if t.outcome is not None and t.pnl is not None
        ]
        total_pnl = (
            float(
                sum(
                    t.pnl if t.outcome != TradeOutcome.LOSS else -t.pnl
                    for t in trades_with_pnl
                )
            )
            if trades_with_pnl
            else 0
        )
        winning = [t for t in trades_with_pnl if t.outcome == TradeOutcome.WIN]
        win_rate = len(winning) / len(trades_with_pnl) if trades_with_pnl else 0

        opening_balance = (
            float(account.opening_balance) if account.opening_balance else 0
        )
        profit_percent = (
            (total_pnl / opening_balance * 100) if opening_balance > 0 else 0
        )

        result.append(
            {
                "id": account.id,
                "name": account.name,
                "opening_balance": opening_balance,
                "is_active": account.is_active,
                "created_at": account.created_at.isoformat()
                if account.created_at
                else None,
                "trade_count": trade_count,
                "total_pnl": total_pnl,
                "profit_percent": round(profit_percent, 2),
            }
        )

    return jsonify({"accounts": result, "total": len(result)})


@accounts_bp.route("/accounts", methods=["POST"])
def create_account():
    """Create a new account."""
    from decimal import Decimal

    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Missing name"}), 400

    opening_balance = data.get("opening_balance")
    if opening_balance is not None:
        opening_balance = Decimal(str(opening_balance))

    account = Account(
        name=data["name"],
        opening_balance=opening_balance if opening_balance else Decimal("0"),
    )
    db.session.add(account)
    db.session.commit()
    return jsonify(account.to_dict()), 201


@accounts_bp.route("/accounts/<account_id>", methods=["GET"])
def get_account(account_id):
    """Get account by ID."""
    account = Account.query.get(account_id)
    if not account:
        return jsonify({"error": "Account not found"}), 404
    return jsonify(account.to_dict())


@accounts_bp.route("/accounts/<account_id>", methods=["PUT"])
def update_account(account_id):
    """Update account."""
    from decimal import Decimal

    account = Account.query.get(account_id)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    data = request.get_json()
    if "name" in data:
        account.name = data["name"]
    if "is_active" in data:
        account.is_active = data["is_active"]
    if "opening_balance" in data:
        account.opening_balance = Decimal(str(data["opening_balance"]))

    db.session.commit()
    return jsonify(account.to_dict())


@accounts_bp.route("/accounts/<account_id>", methods=["DELETE"])
def delete_account(account_id):
    """Soft delete account."""
    account = Account.query.get(account_id)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    account.is_active = False
    db.session.commit()
    return jsonify({"message": "Account deactivated"}), 200


@accounts_bp.route("/accounts/<account_id>/trades", methods=["GET"])
def get_account_trades(account_id):
    """Get trades for an account."""
    account = Account.query.get(account_id)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    trades = Trade.query.filter_by(account_id=account_id).all()
    return jsonify({"trades": [t.to_dict() for t in trades], "total": len(trades)})


@accounts_bp.route("/accounts/bulk-assign", methods=["POST"])
def bulk_assign_trades():
    """Bulk assign trades to an account."""
    data = request.get_json()
    if not data or "account_id" not in data or "trade_ids" not in data:
        return jsonify({"error": "Missing account_id or trade_ids"}), 400

    account = Account.query.get(data["account_id"])
    if not account:
        return jsonify({"error": "Account not found"}), 404

    updated = []
    failed = []
    for trade_id in data["trade_ids"]:
        trade = Trade.query.get(trade_id)
        if trade:
            trade.account_id = data["account_id"]
            updated.append(trade_id)
        else:
            failed.append(trade_id)

    db.session.commit()

    if failed:
        return jsonify(
            {
                "assigned_count": len(updated),
                "failed_ids": failed,
                "message": f"{len(updated)} trades assigned, {len(failed)} not found",
            }
        ), 207

    return jsonify(
        {
            "assigned_count": len(updated),
            "message": f"{len(updated)} trades assigned to {account.name}",
        }
    ), 200
