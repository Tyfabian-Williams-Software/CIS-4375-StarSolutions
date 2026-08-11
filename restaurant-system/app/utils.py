from app.models import User
from werkzeug.security import generate_password_hash

def create_user(username, password, role):
    user = User(username=username, password=generate_password_hash(password), role=role)
    return user


from functools import wraps
from flask import request, jsonify, redirect, url_for
from flask_login import current_user


def wants_json_response():
    """True if the current request should get a JSON error instead of an HTML redirect."""
    return request.is_json or request.headers.get("Accept", "").lower().startswith("application/json")


def roles_required(*allowed_roles):
    """Decorator to require that the current_user has one of the allowed roles.

    Behavior:
    - For API endpoints (requests with Accept: application/json or JSON bodies), return JSON error + 403.
    - For view endpoints, redirect to login if not allowed (preserves previous behavior).

    Usage: @roles_required('admin', 'kitchen')
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Not authenticated
            if not current_user.is_authenticated:
                if wants_json_response():
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for("auth.login"))

            # If no role restriction, allow
            if not allowed_roles:
                return f(*args, **kwargs)

            # Check role membership
            if current_user.role not in allowed_roles:
                if wants_json_response():
                    return jsonify({"error": "Forbidden"}), 403
                # For views, redirect to login (or you might choose a 403 page)
                return redirect(url_for("auth.login"))

            return f(*args, **kwargs)

        return wrapped

    return decorator