from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Order

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        return "Access denied", 403
    orders = Order.query.all()
    return render_template("admin/dashboard.html", orders=orders)