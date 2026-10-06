from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import email_service, security
from app.database import get_db
from app.models.users import models, schemas, services


router = APIRouter(prefix="/USERS", tags=["Users & Auth"])


@router.post("/login", response_model=schemas.Token)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate user credentials and return a JWT access token.
    """
    user = services.authenticate_user(
        db=db,
        email=user_credentials.username,
        plain_password=user_credentials.password,
    )

    access_token = security.create_access_token(
        data={"user_id": user.id, "sub": user.email}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Register a new user account and queue an asynchronous verification email.
    """
    hashed_password = security.hash_password(user.password)

    new_user = services.create_user(
        db=db, user=user, password_hashed=hashed_password
    )

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email already registered",
        )

    token = security.create_verification_token(email=new_user.email)

    background_tasks.add_task(
        email_service.send_verification_email, new_user.email, token
    )

    return new_user


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify a user's email address using a token payload and activate their account.
    """
    # 1. Decode token payload and validate scopes
    try:
        payload = jwt.decode(
            token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        email: str = payload.get("sub")
        scope: str = payload.get("scope")

        if email is None or scope != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token scope or payload",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is invalid or has expired",
        )

    # 2. Activate user status via service layer
    user = services.verify_user_email(db=db, email=email)

    return {
        "status": "success",
        "message": f"Account for {user.email} activated successfully! You can now log in.",
    }


@router.post(
    "/doctors",
    response_model=schemas.DoctorDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_doctor(
    user: schemas.DoctorCreateByAdmin,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(
        security.require_roles([schemas.UserRole.admin])
    ),
):
    """
    Create a new doctor profile with user credentials (Admin only).
    """
    hashed_password = security.hash_password(user.password)
    return services.create_doctor(
        db=db, user=user, password_hashed=hashed_password
    )


@router.patch("/{user_id}/status", response_model=schemas.UserResponse)
def update_status(
    user_id: int,
    status_update: schemas.UserStatus,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(
        security.require_roles([schemas.UserRole.admin])
    ),
):
    """
    Update user active/inactive status (Admin only).
    """
    return services.update_status(
        db=db, user_id=user_id, user_status_data=status_update
    )