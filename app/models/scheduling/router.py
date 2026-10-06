from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import security
from app.models.scheduling import schemas, services
from app.models.users import models as user_models, schemas as user_schemas


router = APIRouter(prefix="/SCHEDULING")


@router.post(
    "/working-hours",
    response_model=schemas.DoctorWorkingHourResponse,
    tags=["CREATING WORKINGHOURE"],
)
def creat_working_hour(
    data: schemas.DoctorWorkingHourCreate,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.doctor, user_schemas.UserRole.admin])
    ),
):
    """
    Define recurring weekly working hours and slot durations for a doctor.
    """
    return services.create_working_hour(
        data=data,
        db=db,
        user=current_user,
    )


@router.patch(
    "/working-hours/{id}/update",
    response_model=schemas.DoctorWorkingHourResponse,
    tags=["UPDATE WORKINGHOURE"],
)
def update_working_hour(
    data: schemas.DoctorWorkingHourUpdate,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.doctor, user_schemas.UserRole.admin])
    ),
):
    """
    Update existing working hours or slot configurations for a doctor.
    """
    return services.update_working_hour(
        data=data,
        db=db,
        user=current_user,
    )


@router.post(
    "/generate",
    response_model=schemas.DoctorScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_schedule_slots(
    payload: schemas.DoctorScheduleCreate,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.admin, user_schemas.UserRole.doctor])
    ),
):
    """
    Generate individual available appointment slots for a specific doctor on a targeted date.
    """
    return services.generate_daily_slots(
        db=db,
        doctor_id=payload.doctor_id,
        target_date=payload.date,
        current_user=current_user,
    )