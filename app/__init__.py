from flask import Flask
from flask_cors import CORS
import logging
import os


def create_app() -> Flask:
    """Initialize the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-development-only'
    app.config['DEBUG_MODE'] = os.environ.get('DAILY_INTEGRAL_DEBUG', '').strip() not in ('', '0', 'false')

    # CORS: allow localhost in dev; in production (Vercel), same-origin so not needed
    CORS(app, origins=[
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:3000',
        'http://localhost:5000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5000'
    ])

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
