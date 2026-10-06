from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import security
from app.models.users import models, schemas


# ==========================================
# 1. User Retrieval Queries
# ==========================================


def get_user_by_email(db: Session, email: str) -> Optional[models.Users]:
    """
    Retrieve a user record by email address.
    """
    return db.query(models.Users).filter(models.Users.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.Users]:
    """
    Retrieve a user record by primary key ID.
    """
    return db.query(models.Users).filter(models.Users.id == user_id).first()


def get_all_users(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Users]:
    """
    Retrieve a paginated list of all registered users.
    """
    return db.query(models.Users).offset(skip).limit(limit).all()


def count_all_users(db: Session) -> int:
    """
    Count total number of registered users in the database.
    """
    return db.query(models.Users).count()


# ==========================================
# 2. User & Profile Creation Services
# ==========================================


def create_user(
    db: Session, user: schemas.UserCreate, password_hashed: str
) -> Optional[models.Users]:
    """
    Create a standard patient user alongside their corresponding patient profile.
    """
    existing_user = get_user_by_email(db, email=user.email)
    if existing_user:
        return None

    db_user = models.Users(
        full_name=user.full_name,
        telefon=user.telefon,
        email=user.email,
        hashed_password=password_hashed,
        role=schemas.UserRole.patient,
    )
    db.add(db_user)
    db.flush()

    db_patient = models.Patients(user_id=db_user.id)
    db.add(db_patient)

    db.commit()
    db.refresh(db_user)

    return db_user


def create_doctor(
    db: Session, user: schemas.DoctorCreateByAdmin, password_hashed: str
) -> models.Doctors:
    """
    Administrative endpoint service to create a doctor account and profile.
    """
    control = get_user_by_email(db=db, email=user.email)
    if control:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    new_user = models.Users(
        full_name=user.full_name,
        telefon=user.telefon,
        email=user.email,
        hashed_password=password_hashed,
        role=schemas.UserRole.doctor,
    )
    db.add(new_user)
    db.flush()

    new_doctor = models.Doctors(
        user_id=new_user.id,
        specialization=user.specialization,
        consultation_fee=user.consultation_fee,
    )
    db.add(new_doctor)

    db.commit()
    db.refresh(new_doctor)

    return new_doctor


# ==========================================
# 3. Authentication & Account State Management
# ==========================================


def authenticate_user(
    db: Session, email: str, plain_password: str
) -> models.Users:
    """
    Authenticate user credentials against stored password hashes and verify account status.
    """
    user = get_user_by_email(db=db, email=email)

    if not user or not security.verify_password(
        plain_password=plain_password, hashed_password=user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    return user


def verify_user_email(db: Session, email: str) -> models.Users:
    """
    Activate user account following successful verification token confirmation.
    """
    user = get_user_by_email(db=db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_active:
        return user

    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


def update_status(
    db: Session, user_id: int, user_status_data: schemas.UserStatus
) -> models.Users:
    """
    Update active status attribute for a specific user ID.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The user with id: {user_id} was not found",
        )

    user.is_active = user_status_data == schemas.UserStatus.true

    db.commit()
    db.refresh(user)
    return user


def update_user_password(
    db: Session, user_id: int, new_plain_password: str
) -> dict:
    """
    Re-hash and update password string for a given user account.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.hashed_password = security.hash_password(new_plain_password)
    db.commit()
    return {"message": f"Password updated successfully for user {user.email}"}