from app.database import Base
from app.models.medical_records import schemas
from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class MedicalRecords(Base):
    """
    SQLAlchemy model representing the medical_records table.
    Stores diagnostic information, prescriptions, and attachments related to a specific appointment.
    """
    __tablename__ = "medical_records"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    appointment_id = Column(
        Integer, ForeignKey("appointments.id"), unique=True, nullable=False
    )


    diagnosis = Column(Text, nullable=False)
    prescription = Column(Text, nullable=True)
    attachment_url = Column(String, nullable=True)


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    appointment = relationship("Appointments", back_populates="medical_record")
    lab_tests = relationship(
        "LabTests", back_populates="medical_record", cascade="all, delete-orphan"
    )


class LabTests(Base):
    """
    SQLAlchemy model representing individual laboratory tests ordered within a medical record.
    Tracks test status, results, and attachment files.
    """
    __tablename__ = "lab_tests"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    medical_record_id = Column(
        Integer, ForeignKey("medical_records.id"), nullable=False
    )
    test_catalog_id = Column(
        Integer, ForeignKey("available_tests.id"), nullable=False
    )

    result = Column(Text, nullable=True)
    result_file_url = Column(String, nullable=True)
    status = Column(SQLEnum(schemas.TestStatus), default="PENDING", nullable=False)


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    medical_record = relationship("MedicalRecords", back_populates="lab_tests")
    test_info = relationship("AvailableTests")


class AvailableTests(Base):
    """
    SQLAlchemy model cataloging all available laboratory tests offered by the facility,
    including pricing and availability status.
    """
    __tablename__ = "available_tests"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)


    name = Column(String(150), nullable=False, unique=True, index=True)
    test_type = Column(SQLEnum(schemas.TestTypeEnum), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)