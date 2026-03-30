from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

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
