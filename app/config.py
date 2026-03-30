import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """Base configuration shared across all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(_BASE_DIR, 'integrals.db'))
    DEBUG_MODE = False
    CORS_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:3000',
        'http://localhost:5000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5000',
    ]


class DevelopmentConfig(Config):
    """Development configuration — debug mode on, verbose logging."""
    DEBUG = True
    DEBUG_MODE = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration — uses in-memory or test database."""
    TESTING = True
    DATABASE_PATH = os.environ.get('TEST_DATABASE_PATH', os.path.join(_BASE_DIR, 'test_integrals.db'))
    LOG_LEVEL = 'WARNING'


class ProductionConfig(Config):
    """Production configuration — strict security, minimal logging."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production
    LOG_LEVEL = 'WARNING'
    PREFERRED_URL_SCHEME = 'https'
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []


def get_config(env_name=None):
    if env_name == "dev":
        return DevelopmentConfig()
    elif env_name == "testing":
        return TestingConfig()
    elif env_name == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()
