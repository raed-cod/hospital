from enum import Enum as PyEnum
from app.database import Base
from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Enum as SQLEnum, Time
from sqlalchemy.orm import relationship


class DayOfWeekEnum(str, PyEnum):
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


class DoctorWorkingHours(Base):
    """
    SQLAlchemy model representing weekly recurring working hours for doctors.
    Defines default start/end times and slot durations per day of the week.
    """
    __tablename__ = "doctor_working_hours"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)


    day_of_week = Column(SQLEnum(DayOfWeekEnum), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=30, nullable=False)

    # Relationship
    doctor = relationship("Doctors", back_populates="working_hours")


class DoctorSchedules(Base):
    """
    SQLAlchemy model representing individual generated time slots for specific dates.
    Tracks slot booking status and connects directly to appointments.
    """
    __tablename__ = "doctor_schedules"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)

    date = Column(Date, nullable=False, index=True)
    day_of_week = Column(SQLEnum(DayOfWeekEnum), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_booked = Column(Boolean, default=False, nullable=False)

    # Relationships
    doctor = relationship("Doctors", back_populates="schedules")
    appointment = relationship(
        "Appointments", back_populates="schedule", uselist=False
    )