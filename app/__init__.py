from flask import Flask, send_from_directory
from flask_cors import CORS
import logging
import os


def create_app() -> Flask:
    """Initialize the Flask application."""
    # In production, serve React build from frontend/dist
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')

    app = Flask(__name__, static_folder=static_folder, static_url_path='')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-development-only'
    app.config['DEBUG_MODE'] = os.environ.get('DAILY_INTEGRAL_DEBUG', '').strip() not in ('', '0', 'false')

    # CORS: allow localhost in dev, production domain handles itself (same-origin)
    cors_origins = [
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:3000',
        'http://localhost:5000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5000'
    ]
    # Add production domain if set
    prod_url = os.environ.get('RENDER_EXTERNAL_URL')
    if prod_url:
        cors_origins.append(prod_url)

    CORS(app, origins=cors_origins)

    configure_logging(app)

    # Register API blueprint (React frontend handles UI)
    from app.api import api_bp
    app.register_blueprint(api_bp)

    # Serve React app for all non-API routes in production
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def not_found(e):
        # If it's an API route, return JSON 404
        from flask import request, jsonify
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        # Otherwise serve the React app (client-side routing)
        return send_from_directory(app.static_folder, 'index.html')

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
