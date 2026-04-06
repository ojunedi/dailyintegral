import logging

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import get_config

limiter = Limiter(key_func=get_remote_address, default_limits=["60 per minute"])


def create_app(env_name=None) -> Flask:
    """Initialize the Flask application."""
    app = Flask(__name__)
    config = get_config(env_name)
    app.config.from_object(config)

    CORS(app, origins=config.CORS_ORIGINS)
    limiter.init_app(app)

    configure_logging(app)

    # HTTPS redirect in production (behind reverse proxy)
    if not app.config.get('DEBUG') and not app.config.get('TESTING'):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Register API blueprint
    from app.api import api_bp
    app.register_blueprint(api_bp)

    # Custom error handlers
    register_error_handlers(app)

    return app


def register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers for common HTTP errors."""
    from flask import jsonify

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal server error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"success": False, "error": "Rate limit exceeded. Try again later."}), 429


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
