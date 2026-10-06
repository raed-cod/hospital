from datetime import date, timedelta
from typing import Optional, List
from fastapi import status, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.scheduling import models as scheduling_models
from app.models.users import models as user_models, schemas as user_schemas
from app.models.appointments import schemas, models
from app.models.billing import models as invoice_models, schemas as invoice_schemas


def get_doctors_by_specialty(
    db: Session, specialization: user_schemas.SpecializationEnum
):
    """
    Query and return all doctors matching a specific medical specialization,
    including their user profile data.
    """
    return (
        db.query(user_models.Doctors)
        .options(joinedload(user_models.Doctors.user))
        .filter(user_models.Doctors.specialization == specialization)
        .all()
    )




def get_available_slots(
    db: Session, doctor_id: int, target_date: Optional[date] = None
):
    """
    Retrieve unbooked schedule time slots for a given doctor.
    Filters by target date or limits to the next 7 days by default.
    """
    if target_date and target_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_date cannot be in the past",
        )

    doctor = (
        db.query(user_models.Doctors)
        .filter(user_models.Doctors.id == doctor_id)
        .first()
    )
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    query = db.query(scheduling_models.DoctorSchedules).filter(
        scheduling_models.DoctorSchedules.doctor_id == doctor_id,
        scheduling_models.DoctorSchedules.is_booked == False,
        scheduling_models.DoctorSchedules.date >= date.today(),
    )

    if target_date:
        query = query.filter(
            scheduling_models.DoctorSchedules.date == target_date
        )
    else:
        # Restrict available slots to the next 7 days if target_date is not specified
        max_date = date.today() + timedelta(days=7)
        query = query.filter(
            scheduling_models.DoctorSchedules.date <= max_date
        )

    return query.order_by(
        scheduling_models.DoctorSchedules.date,
        scheduling_models.DoctorSchedules.start_time,
    ).all()





def create_appointment(
    db: Session, user_id: int, payload: schemas.AppointmentCreate
):
    """
    Create a new appointment for a patient by locking and booking the specified time slot.
    """
    patient = (
        db.query(user_models.Patients)
        .filter(user_models.Patients.user_id == user_id)
        .first()
    )
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found for this user.",
        )

    slot = (
        db.query(scheduling_models.DoctorSchedules)
        .filter(scheduling_models.DoctorSchedules.id == payload.schedule_id)
        .with_for_update()
        .first()
    )

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found.",
        )

    if slot.is_booked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This time slot is already booked.",
        )

    new_appointment = models.Appointments(
        patient_id=patient.id,
        doctor_id=slot.doctor_id,
        schedule_id=slot.id,
        status=schemas.AppointmentStatus.SCHEDULED,
        notes=payload.notes,
    )

    slot.is_booked = True

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return new_appointment





def update_status_appointment(
    db: Session,
    appointment_id: int,
    new_status: schemas.AppointmentStatus,
    user: user_models.Users,
):
    """
    Update appointment status with permission checks based on user roles.
    Handles automatic invoice creation on confirmation and releases slot/invoice on cancellation.
    """
    appointment = (
        db.query(models.Appointments)
        .filter(models.Appointments.id == appointment_id)
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    invoice = (
        db.query(invoice_models.Invoices)
        .filter(invoice_models.Invoices.appointment_id == appointment_id)
        .first()
    )

    if user.role == user_schemas.UserRole.patient:
        patient = (
            db.query(user_models.Patients)
            .filter(user_models.Patients.user_id == user.id)
            .first()
        )

        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to change status for this appointment.",
            )

        if new_status != schemas.AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patients can only change appointment status to CANCELLED.",
            )

    elif user.role == user_schemas.UserRole.doctor:
        doctor = (
            db.query(user_models.Doctors)
            .filter(user_models.Doctors.user_id == user.id)
            .first()
        )

        if not doctor or appointment.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this appointment.",
            )

    # Automatically generate an invoice upon confirmation (CONFIRMED)
    if new_status == schemas.AppointmentStatus.CONFIRMED:
        if not invoice:
            doctor_fee = (
                appointment.doctor.consultation_fee
                if hasattr(appointment.doctor, "consultation_fee")
                else 0.0
            )

            new_invoice = invoice_models.Invoices(
                appointment_id=appointment.id,
                amount=doctor_fee,
                status=invoice_schemas.InvoiceStatus.PENDING,  # Initial invoice status: Unpaid
            )
            db.add(new_invoice)

    # Handle appointment cancellation (CANCELLED)
    elif new_status == schemas.AppointmentStatus.CANCELLED:
        slot = (
            db.query(scheduling_models.DoctorSchedules)
            .filter(
                scheduling_models.DoctorSchedules.id == appointment.schedule_id
            )
            .first()
        )

        if slot:
            slot.is_booked = False

        if invoice:
            invoice.status = invoice_schemas.InvoiceStatus.CANCELLED

    appointment.status = new_status

    db.commit()
    db.refresh(appointment)

    return appointment






def get_patient_appointments(
    db: Session,
    user_id: int,
    status_filter: Optional[schemas.AppointmentStatus] = None,
) -> List[models.Appointments]:
    """
    Retrieve all appointments belonging to the logged-in patient, with an optional status filter.
    """
    patient = (
        db.query(user_models.Patients)
        .filter(user_models.Patients.user_id == user_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    query = (
        db.query(models.Appointments)
        .options(joinedload(models.Appointments.schedule))
        .filter(models.Appointments.patient_id == patient.id)
    )

    if status_filter:
        query = query.filter(
            models.Appointments.status == status_filter
        )

    return query.order_by(
        models.Appointments.created_at.desc()
    ).all()






def get_appointments_for_admin_by_patient(
    db: Session,
    patient_id: int,
    status_filter: Optional[schemas.AppointmentStatus] = None,
) -> List[models.Appointments]:
    """
    Retrieve all appointments for a specific patient ID (Admin-only view).
    """
    patient_exists = (
        db.query(user_models.Patients)
        .filter(user_models.Patients.id == patient_id)
        .first()
    )

    if not patient_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    query = (
        db.query(models.Appointments)
        .options(joinedload(models.Appointments.schedule))
        .filter(models.Appointments.patient_id == patient_id)
    )

    if status_filter:
        query = query.filter(
            models.Appointments.status == status_filter
        )

    return query.order_by(
        models.Appointments.created_at.desc()
    ).all()