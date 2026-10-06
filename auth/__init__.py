"""Authentication package for SmartStudy AI."""
from .authentication import (
    register_user,
    authenticate_user,
    get_user_profile,
    update_user_profile,
    update_user_password,
    hash_password,
    verify_password,
)

__all__ = [
    "register_user",
    "authenticate_user",
    "get_user_profile",
    "update_user_profile",
    "update_user_password",
    "hash_password",
    "verify_password",
]
