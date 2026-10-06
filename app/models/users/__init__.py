from sqlalchemy.orm import Session

from app import security
from app.config import settings
from app.models.users import models, schemas


def init_first_admin(db: Session) -> None:
    """Initializes the default system administrator account if it does not exist."""
    admin_email = settings.FIRST_ADMIN_EMAIL

    existing_admin = (
        db.query(models.Users)
        .filter(models.Users.email == admin_email)
        .first()
    )

    if not existing_admin:
        hashed_password = security.hash_password(settings.FIRST_ADMIN_PASSWORD)
        admin_user = models.Users(
            full_name="System Administrator",
            telefon="0000000000",
            email=admin_email,
            hashed_password=hashed_password,
            role=schemas.UserRole.admin,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        print("First Admin Account Created Successfully!")