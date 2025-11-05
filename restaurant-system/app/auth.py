from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from urllib.parse import urlparse
from app.models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            # Admins always land on the admin dashboard first; do not honor `next` for admins
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))

            # For non-admins, respect a safe 'next' parameter when present
            next_page = request.args.get('next') or request.form.get('next')
            if next_page:
                # ensure the redirect target is relative/safe
                if urlparse(next_page).netloc == '':
                    return redirect(next_page)

            # default role-based redirect for non-admins
            if user.role == "front":
                return redirect(url_for("routes.front"))
            elif user.role == "kitchen":
                return redirect(url_for("routes.kitchen"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))