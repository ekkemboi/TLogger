"""Favorites API routes."""

from decimal import Decimal

from flask import Blueprint, g, jsonify, request

from src.models import FavoriteProduct, db
from src.utils.jwt_utils import jwt_required

favorites_bp = Blueprint("favorites", __name__)


@favorites_bp.route("/favorites", methods=["GET"])
@jwt_required
def get_favorites():
    """Get all active favorite products for current user."""
    products = FavoriteProduct.query.filter_by(
        is_active=True, user_id=g.current_user_id
    ).all()
    return jsonify([p.to_dict() for p in products])


@favorites_bp.route("/favorites", methods=["POST"])
@jwt_required
def create_favorite():
    """Add a new favorite product for current user."""
    data = request.get_json()
    if not data or "symbol" not in data:
        return jsonify({"error": "Missing symbol"}), 400

    symbol = data["symbol"].upper().strip()

    # Check for existing symbol for this user
    existing = FavoriteProduct.query.filter_by(
        symbol=symbol, user_id=g.current_user_id
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            if "point_value" in data:
                existing.point_value = Decimal(str(data["point_value"]))
            if "fees" in data:
                existing.fees = Decimal(str(data["fees"]))
            db.session.commit()
            return jsonify(existing.to_dict()), 200
        return jsonify({"error": "Symbol already exists"}), 409

    product = FavoriteProduct(
        user_id=g.current_user_id,
        symbol=symbol,
        point_value=Decimal(str(data.get("point_value", 1))),
        fees=Decimal(str(data.get("fees", 0))),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@favorites_bp.route("/favorites/<favorite_id>", methods=["PUT"])
@jwt_required
def update_favorite(favorite_id):
    """Update a favorite product."""
    product = FavoriteProduct.query.filter_by(
        id=favorite_id, user_id=g.current_user_id
    ).first()
    if not product:
        return jsonify({"error": "Favorite not found"}), 404

    data = request.get_json()
    if "is_active" in data:
        product.is_active = data["is_active"]
    if "symbol" in data:
        product.symbol = data["symbol"].upper().strip()
    if "point_value" in data:
        product.point_value = Decimal(str(data["point_value"]))
    if "fees" in data:
        product.fees = Decimal(str(data["fees"]))

    db.session.commit()
    return jsonify(product.to_dict())


@favorites_bp.route("/favorites/<favorite_id>", methods=["DELETE"])
@jwt_required
def delete_favorite(favorite_id):
    """Soft delete a favorite product."""
    product = FavoriteProduct.query.filter_by(
        id=favorite_id, user_id=g.current_user_id
    ).first()
    if not product:
        return jsonify({"error": "Favorite not found"}), 404

    product.is_active = False
    db.session.commit()
    return jsonify({"message": "Favorite deactivated"}), 200
