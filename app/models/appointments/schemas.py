from datetime import datetime, date, time
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.scheduling.schemas import DoctorScheduleResponse
from app.models.users import models


class AppointmentStatus(str, Enum):
    """
    Enum representing all possible statuses of an appointment throughout its lifecycle.
    """
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class AppointmentBase(BaseModel):
    """
    Base schema for appointment payload containing shared optional fields.
    """
    notes: Optional[str] = Field(None, max_length=500)


class AppointmentCreate(AppointmentBase):
    """
    Schema required for creating/booking a new appointment.
    """
    schedule_id: int = Field(
        ..., description="ID of the time slot to book from doctor_schedules table"
    )


class DoctorScheduleMinimal(BaseModel):
    """
    Minimal representation of doctor schedule details embedded in appointment responses.
    """
    id: int
    date: date
    start_time: time
    end_time: time

    model_config = ConfigDict(from_attributes=True)


class AppointmentResponse(AppointmentBase):
    """
    Schema for output response when returning appointment details.
    """
    id: int
    patient_id: int
    doctor_id: int
    status: AppointmentStatus
    created_at: datetime
    schedule: DoctorScheduleMinimal

    model_config = ConfigDict(from_attributes=True)


class AppointmentUpdate(BaseModel):
    """
    Schema for updating the status of an existing appointment.
    """
    status: AppointmentStatus