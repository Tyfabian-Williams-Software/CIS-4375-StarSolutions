from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_cors import CORS
import os

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Load config
    from .config import Config
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    # Import blueprints/routes
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # Import sockets
    from . import sockets  # noqa: F401 (registers events)

    return app