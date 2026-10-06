from sqlalchemy import Boolean, Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.users import schemas 


class Users(Base):
    """
    SQLAlchemy model representing system users.
    Handles core authentication details, role assignments, and account statuses.
    """
    __tablename__ = "users"

    # Primary key and account details
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(50), nullable=False)
    telefon = Column(String(30), nullable=True)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(schemas.UserRole), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Profile relationships
    doctor_profile = relationship(
        "Doctors",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    patient_profile = relationship(
        "Patients",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Doctors(Base):
    """
    SQLAlchemy model for doctor profiles.
    Extends user records with specialization details, consultation fees, and schedule links.
    """
    __tablename__ = "doctors"

    # Primary key and foreign key
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)


    specialization = Column(
        SQLEnum(schemas.SpecializationEnum), nullable=False
    )
    consultation_fee = Column(
        Numeric(10, 2), nullable=False
    )

    # Relationships
    user = relationship("Users", back_populates="doctor_profile")
    appointments = relationship(
        "Appointments", back_populates="doctor", cascade="all, delete-orphan"
    )
    schedules = relationship("DoctorSchedules", back_populates="doctor")
    working_hours = relationship("DoctorWorkingHours", back_populates="doctor")


class Patients(Base):
    """
    SQLAlchemy model for patient profiles.
    Extends user records with birth dates, medical histories, and appointment links.
    """
    __tablename__ = "patients"

    # Primary key and foreign key
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)


    date_of_birth = Column(Date, nullable=True)
    medical_history_summary = Column(Text, nullable=True)

    # Relationships
    user = relationship("Users", back_populates="patient_profile")
    appointments = relationship(
        "Appointments", back_populates="patient", cascade="all, delete-orphan"
    )