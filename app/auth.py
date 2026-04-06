"""Authentication middleware using Supabase JWT verification."""

from functools import wraps

from flask import current_app, g, jsonify, request
from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Create a Supabase client using app config."""
    url = current_app.config['SUPABASE_URL']
    key = current_app.config['SUPABASE_KEY']
    return create_client(url, key)


def require_auth(f):
    """Decorator that verifies Supabase JWT and sets g.user_id."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Missing or invalid Authorization header'}), 401

        token = auth_header.split(' ', 1)[1]
        try:
            client = get_supabase_client()
            user_response = client.auth.get_user(token)
            g.user_id = user_response.user.id
        except Exception as e:
            current_app.logger.warning(f"Auth failed: {e}")
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401

        return f(*args, **kwargs)
    return decorated
