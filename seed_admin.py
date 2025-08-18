from app import create_app
from app.models import User
from app.services.user_service import UserService


def seed_admin_user():
    """Seed the database with an admin user."""
    app = create_app()
    with app.app_context():
        existing_admin = User.query.filter_by(is_admin=True).first()
        if existing_admin:
            print("Admin user already exists. Skipping seeding.")
            return

        try:
            print("Creating admin user...")
            admin_user_creator = UserService()
            result = admin_user_creator.create_admin_user(
                email="admin@wiremit.com",
                password="admin1pwd23",
                first_name="Admin",
                last_name="User",
                created_by_user_id=None,
            )
            print(result)
        except Exception as e:
            print(f"Error initializing UserService: {e}")
            return


if __name__ == "__main__":
    seed_admin_user()
