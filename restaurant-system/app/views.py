from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def home():
    """Public landing page; signed-in staff go straight to their workspace."""
    if not current_user.is_authenticated:
        return render_template("home.html")
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    if current_user.role == "kitchen":
        return redirect(url_for("routes.kitchen"))
    return redirect(url_for("routes.front"))
