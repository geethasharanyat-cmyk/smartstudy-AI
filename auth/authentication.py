"""
Authentication and user management module for SmartStudy AI.
Provides password hashing, user registration, login verification,
and profile updates with database persistence.
"""

import hashlib
import hmac
import os
import re
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from database.models import User
from database.db import get_db
from database.seeds import seed_default_curriculum


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with a random 16-byte salt.
    Format: salt_hex$hash_hex
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifies a plain password against the stored salt$hash string.
    Uses constant-time comparison to prevent timing attacks.
    """
    try:
        if not stored_hash or "$" not in stored_hash:
            return False
        salt_hex, hash_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key.hex(), hash_hex)
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """Validates basic email format."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


def register_user(
    username: str,
    email: str,
    password: str,
    full_name: str = "",
    course: str = "",
    year_of_study: str = ""
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Registers a new student account.
    Validates credentials and ensures uniqueness of username and email.
    """
    username = username.strip()
    email = email.strip().lower()
    password = password.strip()

    if len(username) < 3:
        return False, "Username must be at least 3 characters long.", None

    if not validate_email(email):
        return False, "Please enter a valid email address.", None

    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", None

    with get_db() as db:
        # Check existing username
        if db.query(User).filter(User.username == username).first():
            return False, f"Username '{username}' is already taken.", None

        # Check existing email
        if db.query(User).filter(User.email == email).first():
            return False, f"Email '{email}' is already registered.", None

        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            course=course.strip(),
            year_of_study=year_of_study.strip(),
            preferred_study_hours=3.0,
            preferred_study_time="Evening (6:00 PM - 10:00 PM)"
        )
        db.add(new_user)
        db.flush()  # to populate new_user.id

        # Seed the 5 default subjects + topics for every new student
        seed_default_curriculum(new_user.id, db)

        user_info = {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "course": new_user.course,
            "year_of_study": new_user.year_of_study,
            "preferred_study_hours": new_user.preferred_study_hours,
            "preferred_study_time": new_user.preferred_study_time,
        }

    return True, "Account created successfully! You can now log in.", user_info


def authenticate_user(identifier: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticates a user via username or email and verifies password.
    Returns (success, message, user_dict).
    """
    identifier = identifier.strip()
    if not identifier or not password:
        return False, "Please provide both username/email and password.", None

    with get_db() as db:
        user = db.query(User).filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if not user:
            return False, "No account found with those credentials.", None

        if not verify_password(password, user.password_hash):
            return False, "Incorrect password. Please try again.", None

        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "course": user.course,
            "year_of_study": user.year_of_study,
            "preferred_study_hours": user.preferred_study_hours,
            "preferred_study_time": user.preferred_study_time,
        }
        return True, f"Welcome back, {user.full_name or user.username}!", user_info


def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches user profile details by user ID."""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "course": user.course,
            "year_of_study": user.year_of_study,
            "preferred_study_hours": user.preferred_study_hours,
            "preferred_study_time": user.preferred_study_time,
            "created_at": user.created_at,
        }


def update_user_profile(
    user_id: int,
    full_name: str,
    course: str,
    year_of_study: str,
    preferred_study_hours: float,
    preferred_study_time: str
) -> Tuple[bool, str]:
    """Updates user profile information in the database."""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found."

        user.full_name = full_name.strip()
        user.course = course.strip()
        user.year_of_study = year_of_study.strip()
        user.preferred_study_hours = max(0.5, float(preferred_study_hours))
        user.preferred_study_time = preferred_study_time.strip()

        return True, "Profile updated successfully!"


def update_user_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """Updates user password after verifying old password."""
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found."

        if not verify_password(old_password, user.password_hash):
            return False, "Current password does not match."

        user.password_hash = hash_password(new_password)
        return True, "Password updated successfully!"
