from app.database import Base
from app.models.appointments import schemas
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Appointments(Base):
   
    __tablename__ = "appointments"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    schedule_id = Column(
        Integer, ForeignKey("doctor_schedules.id"), unique=True, nullable=False
    )


    status = Column(
        SQLEnum(schemas.AppointmentStatus),
        nullable=False,
        default=schemas.AppointmentStatus.SCHEDULED,
    )
    notes = Column(Text, nullable=True)


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    patient = relationship("Patients", back_populates="appointments")
    doctor = relationship("Doctors", back_populates="appointments")
    medical_record = relationship(
        "MedicalRecords",
        back_populates="appointment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    invoice = relationship(
        "Invoices",
        back_populates="appointment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    schedule = relationship("DoctorSchedules", back_populates="appointment")