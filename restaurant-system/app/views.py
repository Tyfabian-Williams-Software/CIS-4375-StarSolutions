from flask import Blueprint, render_template
from flask_login import login_required
from datetime import datetime

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
@login_required
def home():
    # Render the front-facing order dashboard by default
    return render_template("front.html", current_year=datetime.utcnow().year)