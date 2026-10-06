from datetime import date, datetime, time
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

# ==========================================
# 1. Enums
# ==========================================


class DayOfWeekEnum(str, Enum):
    """
    Enum representing days of the week for recurring schedules.
    """
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


# ==========================================
# 2. Doctor Working Hours Schemas
# ==========================================


class DoctorWorkingHourBase(BaseModel):
    """
    Base schema defining doctor working hours and slot duration constraints.
    """
    day_of_week: DayOfWeekEnum
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(default=30, ge=10, le=120)


class DoctorWorkingHourCreate(DoctorWorkingHourBase):
    """
    Schema for defining new doctor working hours.
    """
    pass


class DoctorWorkingHourUpdate(BaseModel):
    """
    Schema for updating existing doctor working hours.
    """
    working_hour_id: int
    day_of_week: Optional[DayOfWeekEnum] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    slot_duration_minutes: int = Field(default=30, ge=10, le=120)


class DoctorWorkingHourResponse(DoctorWorkingHourBase):
    """
    Response schema returning doctor working hours details.
    """
    id: int
    doctor_id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Doctor Schedule Schemas (Available Time Slots)
# ==========================================


class DoctorScheduleBase(BaseModel):
    """
    Base schema referencing doctor ID and schedule date.
    """
    doctor_id: int
    date: date


class DoctorScheduleCreate(DoctorScheduleBase):
    """
    Schema for triggering daily schedule slot generation.
    """
    pass


class TimeSlotSchema(BaseModel):
    """
    Schema representing an individual time slot within a doctor's schedule.
    """
    id: int
    start_time: time
    end_time: time
    is_booked: bool

    model_config = ConfigDict(from_attributes=True)


class DoctorScheduleResponse(BaseModel):
    """
    Response schema returning a full schedule of generated time slots for a specific date.
    """
    doctor_id: int
    date: date
    day_of_week: DayOfWeekEnum
    slots: List[TimeSlotSchema]

    model_config = ConfigDict(from_attributes=True)


class AvailableSlotResponse(BaseModel):
    """
    Response schema returning detailed information about an individual time slot.
    """
    id: int
    doctor_id: int
    date: date
    day_of_week: str
    start_time: time
    end_time: time
    is_booked: bool

    model_config = ConfigDict(from_attributes=True)