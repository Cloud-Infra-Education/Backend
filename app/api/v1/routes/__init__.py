"""
API routes
"""
from app.api.v1.routes import health, users, auth, contents_internal

__all__ = ["health", "users", "auth", "contents_internal"]