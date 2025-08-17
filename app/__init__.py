from flask import Flask
from flask_cors import CORS
import logging
import os

def create_app():
    """Initialize the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-development-only'
    
    # Enable CORS for React frontend
    CORS(app, origins=['http://localhost:5173'])

    configure_logging(app)

    # Register blueprints
    from app.routes import main_bp
    from app.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app


def configure_logging(app):
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

