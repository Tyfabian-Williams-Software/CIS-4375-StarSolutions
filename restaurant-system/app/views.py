from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
@login_required
def home():
    """Send each role to its workspace."""
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    if current_user.role == "kitchen":
        return redirect(url_for("routes.kitchen"))
    return redirect(url_for("routes.front"))
