"""Flask application factory."""

import os

from dotenv import load_dotenv
from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application."""
    load_dotenv()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload

    # Register blueprints
    from app.routes.analysis import analysis_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)

    return app
