from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Order
from app import db
from app.models import User
from werkzeug.security import generate_password_hash
from app.utils import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@roles_required("admin")
def dashboard():
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    def _revenue(since):
        total = (
            db.session.query(db.func.coalesce(db.func.sum(Order.order_price), 0))
            .filter(Order.order_date >= since)
            .scalar()
        )
        return float(total or 0)

    stats = {
        "revenue_today": _revenue(today_start),
        "revenue_week": _revenue(week_start),
        "orders_today": Order.query.filter(Order.order_date >= today_start).count(),
    }
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(15).all()
    users = User.query.order_by(User.username).all()
    return render_template("admin/dashboard.html",
                           stats=stats, recent_orders=recent_orders, users=users)


# Admin JSON API for user management


@admin_bp.route("/api/users", methods=["GET"])
@login_required
@roles_required("admin")
def api_list_users():
    users = User.query.all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


@admin_bp.route("/api/users", methods=["POST"])
@login_required
@roles_required("admin")
def api_create_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")
    if not username or not password or not role:
        return jsonify({"error": "username, password and role are required"}), 400
    if role not in ("front", "kitchen", "admin"):
        return jsonify({"error": "invalid role"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 400

    user = User(username=username, password=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@admin_bp.route("/api/users/<int:user_id>", methods=["GET"])
@login_required
@roles_required("admin")
def api_get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


@admin_bp.route("/api/users/<int:user_id>", methods=["PUT", "PATCH"])
@login_required
@roles_required("admin")
def api_update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json(silent=True) or {}
    if "username" in data:
        user.username = data.get("username")
    if "role" in data:
        role = data.get("role")
        if role not in ("front", "kitchen", "admin"):
            return jsonify({"error": "invalid role"}), 400
        user.role = role
    if "password" in data:
        user.password = generate_password_hash(data.get("password"))
    db.session.commit()
    return jsonify(user.to_dict()), 200


@admin_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@login_required
@roles_required("admin")
def api_delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return ("", 204)