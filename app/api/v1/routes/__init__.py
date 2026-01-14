"""
API routes
"""
from app.api.v1.routes import health, users, auth

__all__ = ["health", "users", "auth"]