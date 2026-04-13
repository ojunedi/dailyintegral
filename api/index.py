import sys
import os

# Add project root to path so the app module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

env = os.environ.get('FLASK_ENV', 'dev')
app = create_app(env)
