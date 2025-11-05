from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .config import Config
from .sockets import init_sockets, socketio

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    # Return JSON 401 for API requests instead of redirecting to login page.
    @login_manager.unauthorized_handler
    def _unauthorized():
        from flask import request, jsonify, redirect, url_for
        # Treat requests with JSON content or explicit Accept: application/json as API calls
        if request.is_json or request.headers.get("Accept", "").lower().startswith("application/json"):
            return jsonify({"error": "Authentication required"}), 401
        return redirect(url_for("auth.login"))

    # Register blueprints
    from app.auth import auth_bp
    from app.routes import routes_bp
    from app.admin import admin_bp
    from app.views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(views_bp)

    # Initialize sockets
    init_sockets(app)

    return app