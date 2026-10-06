from fastapi import APIRouter, Query, Depends, status, HTTPException
from app.models.users import schemas as user_schemas, models as user_models
from sqlalchemy.orm import Session
from app.database import get_db
from typing import List, Optional
from app import security
from datetime import date
from app.models.appointments import services, schemas 
from app.models.scheduling import schemas as scheduling_schemas


router = APIRouter(prefix="/appointments", tags=["Appointments Flow"])


@router.get("/doctor", response_model=list[user_schemas.DoctorListResponse])
def get_doctors_by_specialty(
    specialization: user_schemas.SpecializationEnum = Query(...),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of doctors filtered by their medical specialization.
    """
    return services.get_doctors_by_specialty(
        db=db, specialization=specialization
    )


@router.get(
    "/doctors/{doctor_id}/available-slots",
    response_model=List[scheduling_schemas.AvailableSlotResponse],
)
def get_doctor_available_slots(
    doctor_id: int,
    target_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Fetch available schedule time slots for a specific doctor, optionally filtered by date.
    """
    return services.get_available_slots(
        db=db, doctor_id=doctor_id, target_date=target_date
    )


@router.post(
    "/book",
    response_model=schemas.AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def book_appointment(
    payload: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.patient])
    ),
):
    """
    Book a new appointment for the currently authenticated patient.
    """
    return services.create_appointment(
        db=db, user_id=current_user.id, payload=payload
    )


@router.patch(
    "/{appointment_id}/status", response_model=schemas.AppointmentResponse
)
def update_status_appointment(
    appointment_id: int,
    status_update: schemas.AppointmentUpdate,
    current_user: user_models.Users = Depends(
        security.require_roles([
            user_schemas.UserRole.admin,
            user_schemas.UserRole.patient,
            user_schemas.UserRole.doctor,
        ])
    ),
    db: Session = Depends(get_db),
):
    """
    Update the status of an existing appointment (accessible by Admin, Patient, or Doctor).
    """
    return services.update_status_appointment(
        db=db,
        appointment_id=appointment_id,
        new_status=status_update.status,
        user=current_user,
    )


@router.get(
    "/my-appointments", response_model=List[schemas.AppointmentResponse]
)
def get_my_appointments(
    status_filter: Optional[schemas.AppointmentStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.patient])
    ),
):
    """
    Get all appointments for the currently logged-in patient with an optional status filter.
    """
    return services.get_patient_appointments(
        db=db, user_id=current_user.id, status_filter=status_filter
    )


# --------------------------------------------------
# Admin Endpoint: Retrieve appointments for any patient
# --------------------------------------------------


@router.get(
    "/admin/patients/{patient_id}",
    response_model=List[schemas.AppointmentResponse],
)
def get_appointments_by_patient_id_for_admin(
    patient_id: int,
    status_filter: Optional[schemas.AppointmentStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.admin])
    ),
):
    """
    Administrative endpoint to retrieve all appointments for a specific patient ID.
    """
    return services.get_appointments_for_admin_by_patient(
        db=db, patient_id=patient_id, status_filter=status_filter
    )