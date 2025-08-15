from datetime import UTC, datetime

from loguru import logger

from app.extensions import db
from app.models import User
from app.services.auth_service import AuthService


class UserService:
    def __init__(self):
        self.auth_service = AuthService()

    @staticmethod
    def create_admin_user(
        email: str,
        password: str,
        first_name: str = None,
        last_name: str = None,
        created_by_user_id: int = None,
    ) -> dict:
        """
        Create a new admin user. Only existing admin users can create new admin users.
        Returns dict with success status and user data or error message.
        """
        try:
            if not email or not password:
                return {"success": False, "message": "Email and password are required"}

            # validate email
            email_valid = AuthService.validate_email_address(email)
            if email_valid is False:
                return {"success": False, "message": "Invalid email address"}

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return {
                    "success": False,
                    "message": "User with this email already exists",
                }

            auth_service = AuthService()
            try:
                hashed_password = auth_service._hash_password(password)
            except Exception as e:
                logger.error(f"Failed to hash admin password: {e}")
                return {"success": False, "message": "Failed to hash password!"}

            new_user = User(
                email=email,
                password_hash=hashed_password,
                first_name=first_name.strip() if first_name else None,
                last_name=last_name.strip() if last_name else None,
                role="admin",
                is_active=True,
                is_admin=True,
                created_by=created_by_user_id,
                created_at=datetime.now(UTC),
            )

            db.session.add(new_user)
            db.session.commit()

            logger.info(
                f"Admin user created successfully: {email} by user_id: {created_by_user_id}"
            )
            return {
                "success": True,
                "message": "Admin user created successfully",
                "user": new_user.to_dict(),
            }

        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            db.session.rollback()
            return {"success": False, "message": "Failed to create admin user"}
