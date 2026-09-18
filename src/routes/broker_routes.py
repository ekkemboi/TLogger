"""Broker sync API routes."""

from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, g, jsonify, request

from src.models import BrokerConnection, db
from src.utils.jwt_utils import jwt_required

brokers_bp = Blueprint("brokers", __name__)


@brokers_bp.route("/brokers", methods=["GET"])
@jwt_required
def list_connections():
    connections = BrokerConnection.query.filter_by(user_id=g.current_user_id).all()
    return jsonify({"connections": [c.to_dict() for c in connections]})


@brokers_bp.route("/brokers", methods=["POST"])
@jwt_required
def create_connection():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    broker = data.get("broker")
    label = data.get("label")
    if not broker or not label:
        return jsonify({"error": "broker and label are required"}), 400

    conn = BrokerConnection(
        user_id=g.current_user_id,
        broker=broker,
        label=label,
        api_key=data.get("api_key"),
        api_secret=data.get("api_secret"),
        account_id=data.get("account_id"),
        sync_interval=data.get("sync_interval", 60),
    )
    db.session.add(conn)
    db.session.commit()

    return jsonify(conn.to_dict()), 201


@brokers_bp.route("/brokers/<conn_id>", methods=["PUT"])
@jwt_required
def update_connection(conn_id):
    conn = BrokerConnection.query.filter_by(id=conn_id, user_id=g.current_user_id).first()
    if not conn:
        return jsonify({"error": "Connection not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "label" in data:
        conn.label = data["label"]
    if "api_key" in data:
        conn.api_key = data["api_key"]
    if "api_secret" in data:
        conn.api_secret = data["api_secret"]
    if "account_id" in data:
        conn.account_id = data["account_id"]
    if "sync_interval" in data:
        conn.sync_interval = data["sync_interval"]
    if "is_active" in data:
        conn.is_active = data["is_active"]

    db.session.commit()
    return jsonify(conn.to_dict())


@brokers_bp.route("/brokers/<conn_id>", methods=["DELETE"])
@jwt_required
def delete_connection(conn_id):
    conn = BrokerConnection.query.filter_by(id=conn_id, user_id=g.current_user_id).first()
    if not conn:
        return jsonify({"error": "Connection not found"}), 404

    db.session.delete(conn)
    db.session.commit()
    return jsonify({"message": "Connection deleted"})


@brokers_bp.route("/brokers/<conn_id>/sync", methods=["POST"])
@jwt_required
def trigger_sync(conn_id):
    conn = BrokerConnection.query.filter_by(id=conn_id, user_id=g.current_user_id).first()
    if not conn:
        return jsonify({"error": "Connection not found"}), 404

    # Mark last sync time (actual sync implementation comes later)
    conn.last_sync_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"status": "synced", "last_sync_at": conn.last_sync_at.isoformat()})


@brokers_bp.route("/brokers/<conn_id>/sync-status", methods=["GET"])
@jwt_required
def get_sync_status(conn_id):
    conn = BrokerConnection.query.filter_by(id=conn_id, user_id=g.current_user_id).first()
    if not conn:
        return jsonify({"error": "Connection not found"}), 404

    return jsonify({
        "broker": conn.broker,
        "label": conn.label,
        "is_active": conn.is_active,
        "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
        "sync_interval": conn.sync_interval,
    })
