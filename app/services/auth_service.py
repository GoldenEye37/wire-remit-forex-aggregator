import re
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from email_validator import EmailNotValidError, validate_email
from flask import current_app as app
from loguru import logger

from app.extensions import db
from app.models import User


class AuthService:
    def __init__(self):
        self.password_hasher = PasswordHasher()
        self.jwt_secret = app.config["JWT_SECRET_KEY"]
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = app.config["JWT_EXPIRATION_HOURS"]

    def _hash_password(self, password: str) -> str:
        try:
            return self.password_hasher.hash(password)
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        try:
            self.password_hasher.verify(hashed_password, password)
            return True
        except VerifyMismatchError:
            return False
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def _generate_jwt(self, user: User) -> str:
        try:
            payload = {
                "user_id": user.id,
                "email": user.email,
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(hours=self.jwt_expiration_hours),
            }
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            logger.info(f"JWT token generated for user {user.email}")
            return token
        except Exception as e:
            logger.error(f"Error generating JWT: {e}")
            raise

    def _verify_jwt(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying JWT: {e}")
            return None

    @staticmethod
    def validate_email_address(email: str) -> bool:
        # Validate email
        try:
            valid = validate_email(email)
            email = valid.email
            return True
        except EmailNotValidError:
            return False

    @staticmethod
    def validate_password_strength(password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        return True, ""

    def register_user(
        self, email: str, password: str, first_name: str = None, last_name: str = None
    ) -> dict:
        try:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return {
                    "success": False,
                    "message": "User with this email already exists",
                }

            hashed_password = self._hash_password(password)

            new_user = User(
                email=email,
                password_hash=hashed_password,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )

            db.session.add(new_user)
            db.session.commit()

            token = self._generate_jwt(new_user)

            logger.info(f"User registered successfully: {email}")
            return {
                "success": True,
                "message": "User registered successfully",
                "user": new_user.to_dict(),
                "token": token,
            }

        except Exception as e:
            logger.error(f"Error registering user: {e}")
            db.session.rollback()
            return {"success": False, "message": "Registration failed"}

    def login_user(self, email: str, password: str) -> dict:
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                return {"success": False, "message": "Invalid email or password"}

            if not user.is_active:
                return {"success": False, "message": "Account is deactivated"}

            if not self._verify_password(password, user.password_hash):
                return {"success": False, "message": "Invalid email or password"}

            user.last_login = datetime.now(UTC)
            db.session.commit()

            # Generate JWT token
            token = self._generate_jwt(user)

            logger.info(f"User logged in successfully: {email}")
            return {
                "success": True,
                "message": "Login successful",
                "user": user.to_dict(),
                "token": token,
            }

        except Exception as e:
            logger.error(f"Error during login: {e}")
            return {"success": False, "message": "Login failed"}

    def get_user_from_token(self, token: str) -> User | None:
        """
        Get user object from JWT token.
        """
        payload = self._verify_jwt(token)
        if not payload:
            return None

        user = User.query.get(payload.get("user_id"))
        if not user or not user.is_active:
            return None

        return user
