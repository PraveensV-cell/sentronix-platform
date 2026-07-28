from sqlalchemy.orm import Session

from src.auth.password import hash_password
from src.core.logger import app_logger
from src.database.session import SessionLocal
from src.models.user import User


def seed_super_admin() -> None:
    """
    Create the default Super Admin if it does not already exist.
    """

    db: Session = SessionLocal()

    try:
        existing = db.query(User).filter(User.username == "admin").first()

        if existing:
            app_logger.info("Super Admin already exists.")
            return

        admin = User(
            username="admin",
            email="admin@sentronix.ai",
            full_name="Super Administrator",
            hashed_password=hash_password("Sentronix123"),
            role="super_admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        app_logger.info("Default Super Admin created successfully.")

    except Exception as exc:
        db.rollback()
        app_logger.exception(f"Failed to create Super Admin: {exc}")
        raise

    finally:
        db.close()
