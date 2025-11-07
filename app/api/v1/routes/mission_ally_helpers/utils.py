"""Utility functions for WebSocket handling"""


def sanitize_error_message(error_msg: str) -> str:
    """Sanitize error messages to prevent leaking sensitive information"""
    if "postgresql://" in error_msg or "postgres://" in error_msg:
        return "Database connection error"
    return error_msg
