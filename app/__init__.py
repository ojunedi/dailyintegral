from flask import Flask
from flask_cors import CORS
import logging

from app.config import get_config


def create_app(env_name=None) -> Flask:
    """Initialize the Flask application."""
    app = Flask(__name__)
    config = get_config(env_name)
    app.config.from_object(config)

    CORS(app, origins=config.CORS_ORIGINS)

    configure_logging(app)

    # Register API blueprint
    from app.api import api_bp
    app.register_blueprint(api_bp)

    return app


def configure_logging(app: Flask) -> None:
    """Configure logging for the Flask application.

    Args:
        app: Flask application instance
    """
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    handler.setFormatter(formatter)

    if not app.logger.handlers:
        app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)
