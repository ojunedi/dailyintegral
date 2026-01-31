from flask import Flask
from flask_cors import CORS
import logging
import os


def create_app() -> Flask:
    """Initialize the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-development-only'

    # Enable CORS for React frontend (allow both frontend and any localhost development)
    CORS(app, origins=[
        'http://localhost:5173',  # Vite default
        'http://localhost:5174',  # Vite alternate port
        'http://localhost:3000',  # React dev server default
        'http://localhost:5000',  # Flask on port 5001 (avoiding macOS AirPlay conflict)
        'http://127.0.0.1:5173',  # IPv4 localhost variants
        'http://127.0.0.1:5174',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5000'
    ])

    configure_logging(app)

    # Register API blueprint (React frontend handles UI)
    from app.api import api_bp
    app.register_blueprint(api_bp)

    return app


def configure_logging(app: Flask) -> None:
    """Configure logging for the Flask application.

    Args:
        app: Flask application instance
    """
    # Set level and format for logging
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)  # or DEBUG, WARNING, etc.
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    handler.setFormatter(formatter)

    # Attach the handler to the app's logger
    if not app.logger.handlers:
        app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)
