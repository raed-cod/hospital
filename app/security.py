from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import database
from app.config import settings
from app.models.users import models, schemas

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/USERS/login")


def hash_password(password: str) -> str:
    """Hash a plain text password using the Bcrypt algorithm."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against the stored Bcrypt hash."""
    plain_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hashed_bytes)


def create_access_token(data: dict) -> str:
    """Generates an encoded JWT access token with an expiration time."""
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_verification_token(email: str) -> str:
    """Generates a 24-hour verification JWT token for email confirmation."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)

    to_encode = {
        "sub": email,
        "scope": "email_verification",
        "exp": expire,
    }

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db),
) -> models.Users:
    """Dependency to retrieve and validate the authenticated user from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

        token_data = schemas.TokenData(user_id=user_id)

    except JWTError:
        raise credentials_exception

    user = (
        db.query(models.Users)
        .filter(models.Users.id == token_data.user_id)
        .first()
    )

    if user is None:
        raise credentials_exception

    return user


def require_roles(allowed_roles: list[str]):
    """Dependency wrapper to enforce role-based authorization for endpoints."""

    def role_checker(
        current_user: models.Users = Depends(get_current_user),
    ) -> models.Users:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account",
            )
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have enough permissions",
            )
        return current_user

    return role_checker