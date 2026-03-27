"""Account API routes."""

from flask import Blueprint, jsonify, request

from src.models import Account, Trade, db

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("/accounts", methods=["GET"])
def get_accounts():
    """Get all active accounts."""
    accounts = Account.query.filter_by(is_active=True).all()
    return jsonify(
        {"accounts": [a.to_dict() for a in accounts], "total": len(accounts)}
    )


@accounts_bp.route("/accounts", methods=["POST"])
def create_account():
    """Create a new account."""
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Missing name"}), 400

    account = Account(name=data["name"])
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
    account = Account.query.get(account_id)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    data = request.get_json()
    if "name" in data:
        account.name = data["name"]
    if "is_active" in data:
        account.is_active = data["is_active"]

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
