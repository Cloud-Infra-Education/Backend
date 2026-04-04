"""
API routes
"""
from . import health, users, auth, contents, content_likes, watch_history, video_assets, contents_internal, videos, video_assets_internal, search

__all__ = [
    "health",
    "users",
    "auth",
    "contents",
    "content_likes",
    "watch_history",
    "video_assets",
    "contents_internal",
    "videos",
    "video_assets_internal",
    "search",
]