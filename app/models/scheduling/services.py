from datetime import date, datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.scheduling import models, schemas
from app.models.users import models as user_models, schemas as user_schemas


def create_working_hour(
    data: schemas.DoctorWorkingHourCreate,
    db: Session,
    user: user_models.Users,
):
    """
    Create a new recurring working hour configuration for a doctor.
    Verifies active status and validates doctor ownership or admin authority.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user accounts do not have permission to perform this action.",
        )

    doctor = (
        db.query(user_models.Doctors)
        .filter(user_models.Doctors.user_id == user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for the active user.",
        )

    new_working_hour = models.DoctorWorkingHours(
        doctor_id=doctor.id,
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time,
        slot_duration_minutes=data.slot_duration_minutes,
    )

    db.add(new_working_hour)
    db.commit()
    db.refresh(new_working_hour)

    return new_working_hour


def update_working_hour(
    data: schemas.DoctorWorkingHourUpdate,
    db: Session,
    current_user: user_models.Users,
):
    """
    Update an existing working hour record.
    Verifies that the requesting user is either an admin or the owner doctor.
    """
    working_hour = (
        db.query(models.DoctorWorkingHours)
        .filter(models.DoctorWorkingHours.id == data.working_hour_id)
        .first()
    )

    if not working_hour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Working hour record not found. Please verify working_hour_id.",
        )

    doctor = (
        db.query(user_models.Doctors)
        .filter(user_models.Doctors.id == working_hour.doctor_id)
        .first()
    )

    # Permission check: Requester must be Admin or the assigned doctor
    is_admin = current_user.role == user_schemas.UserRole.admin
    is_owner_doctor = doctor and doctor.user_id == current_user.id

    if not (is_admin or is_owner_doctor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this working hour.",
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key != "working_hour_id" and value is not None:
            setattr(working_hour, key, value)

    db.commit()
    db.refresh(working_hour)

    return working_hour


def generate_daily_slots(
    db: Session,
    doctor_id: int,
    target_date: date,
    current_user: user_models.Users,
):
    """
    Generate individual available appointment time slots for a specific doctor on a target date.
    Calculates intervals using configured working hours and slot durations.
    """
    # 1. Verify doctor existence
    doctor = (
        db.query(user_models.Doctors)
        .filter(user_models.Doctors.id == doctor_id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with id {doctor_id} not found.",
        )

    # 2. Authorization check (Admin or assigned doctor)
    is_admin = current_user.role == user_schemas.UserRole.admin
    is_owner_doctor = doctor.user_id == current_user.id

    if not (is_admin or is_owner_doctor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to generate schedules for this doctor.",
        )

    day_name = target_date.strftime("%A").upper()

    # 3. Check if slots already exist for this target date to prevent duplicates
    existing_slots = (
        db.query(models.DoctorSchedules)
        .filter(
            models.DoctorSchedules.doctor_id == doctor_id,
            models.DoctorSchedules.date == target_date,
        )
        .order_by(models.DoctorSchedules.start_time.asc())
        .all()
    )

    if existing_slots:
        return {
            "doctor_id": doctor_id,
            "date": target_date,
            "day_of_week": day_name,
            "slots": existing_slots,
        }

    # 4. Fetch doctor's recurring working hours for the target day
    working_hours = (
        db.query(models.DoctorWorkingHours)
        .filter(
            models.DoctorWorkingHours.doctor_id == doctor_id,
            models.DoctorWorkingHours.day_of_week == day_name,
        )
        .first()
    )

    if not working_hours:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Doctor does not have working hours configured for {day_name}.",
        )

    # 5. Divide the working interval into discrete time slots
    current_slot_start = datetime.combine(target_date, working_hours.start_time)
    work_end = datetime.combine(target_date, working_hours.end_time)
    slot_delta = timedelta(minutes=working_hours.slot_duration_minutes)

    created_slots = []
    while current_slot_start + slot_delta <= work_end:
        current_slot_end = current_slot_start + slot_delta

        new_schedule_slot = models.DoctorSchedules(
            doctor_id=doctor_id,
            date=target_date,
            day_of_week=day_name,
            start_time=current_slot_start.time(),
            end_time=current_slot_end.time(),
            is_booked=False,
        )
        db.add(new_schedule_slot)
        created_slots.append(new_schedule_slot)

        current_slot_start = current_slot_end

    db.commit()

    for slot in created_slots:
        db.refresh(slot)

    return {
        "doctor_id": doctor_id,
        "date": target_date,
        "day_of_week": day_name,
        "slots": created_slots,
    }