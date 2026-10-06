from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.medical_records import schemas as medical_schemas, models as medical_models
from app.models.users import models as user_models
from app.models.appointments import models as appointment_models
from app.models.billing import models as invoice_models, schemas as invoice_schemas


def create_test(
    data: medical_schemas.AvailableTestCreate,
    db: Session,
    user: user_models.Users
):
    """
    Create a new test entry in the available tests catalog.
    Checks for existing entries by name to prevent duplicates.
    """
    control = db.query(medical_models.AvailableTests).filter(
        medical_models.AvailableTests.name == data.name
    ).first()

    if control:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A test with this name has already been added."
        )

    new_tst = medical_models.AvailableTests(
        name=data.name,
        test_type=data.test_type,
        price=data.price,
        is_available=data.is_available
    )

    db.add(new_tst)
    db.commit()
    db.refresh(new_tst)

    return new_tst


def update_test_data(
    data: medical_schemas.AvailableTestUpdate,
    db: Session,
    test_id: int,
    user: user_models.Users
):
    """
    Update catalog details for a specific available test by ID.
    Prevents duplicate names across different catalog items.
    """
    available_tst = db.query(medical_models.AvailableTests).filter(
        medical_models.AvailableTests.id == test_id
    ).first()

    if not available_tst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Available test not found."
        )

    if data.name and data.name != available_tst.name:
        existing_test = (
            db.query(medical_models.AvailableTests)
            .filter(
                medical_models.AvailableTests.name == data.name,
                medical_models.AvailableTests.id != test_id,
            ).first()
        )
        if existing_test:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another test with this name already exists!"
            )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key != "test_id" and value is not None:
            setattr(available_tst, key, value)

    db.commit()
    db.refresh(available_tst)

    return available_tst


def get_tsts(db: Session) -> list[medical_schemas.AvailableTestResponse]:
    """
    Retrieve all test catalog entries from the database.
    """
    return db.query(medical_models.AvailableTests).all()


def create_medical_records(data: medical_schemas.MedicalRecordCreate, db: Session):
    """
    Create a new medical record for an appointment.
    Ensures that an appointment has at most one medical record.
    """
    control = (
        db.query(medical_models.MedicalRecords)
        .filter(medical_models.MedicalRecords.appointment_id == data.appointment_id)
        .first()
    )

    if control:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A medical record has already been added for this appointment!"
        )

    new_medical = medical_models.MedicalRecords(
        appointment_id=data.appointment_id,
        diagnosis=data.diagnosis,
        prescription=data.prescription,
        attachment_url=data.attachment_url
    )

    db.add(new_medical)
    db.commit()
    db.refresh(new_medical)

    return new_medical


def update_medical_record(
    data: medical_schemas.MedicalRecordUpdate,
    medical_record_id: int,
    db: Session,
    user: user_models.Users
):
    """
    Update an existing medical record.
    Validates that the requesting user is a doctor assigned to the associated appointment.
    """
    medical_record = db.query(medical_models.MedicalRecords).filter(
        medical_models.MedicalRecords.id == medical_record_id
    ).first()

    if not medical_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )

    doctor_data = db.query(user_models.Doctors).filter(
        user_models.Doctors.user_id == user.id
    ).first()

    if not doctor_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can update medical records"
        )

    if not medical_record.appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated appointment not found"
        )

    if medical_record.appointment.doctor_id != doctor_data.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this record"
        )

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key != "id" and value is not None:
            setattr(medical_record, key, value)

    db.commit()
    db.refresh(medical_record)

    return medical_record


def get_medical_record(
    medical_id: int,
    db: Session,
    user: user_models.Users
):
    """
    Retrieve medical record details by ID.
    Verifies that the requesting doctor is assigned to the record's appointment.
    """
    medical_record = db.query(medical_models.MedicalRecords).filter(
        medical_models.MedicalRecords.id == medical_id
    ).first()

    if not medical_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found. Please verify the medical_id."
        )

    doctor = db.query(user_models.Doctors).filter(
        user_models.Doctors.user_id == user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can access medical records"
        )

    if doctor.id != medical_record.appointment.doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this record"
        )

    return medical_record


def create_lab_tst(
    data: medical_schemas.LabTestCreate,
    medical_id: int,
    db: Session,
    user: user_models.Users
):
    """
    Order a new lab test for a medical record and automatically add its cost to the appointment invoice.
    """
    medical_record = db.query(medical_models.MedicalRecords).filter(
        medical_models.MedicalRecords.id == medical_id
    ).first()

    if not medical_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )

    doctor = db.query(user_models.Doctors).filter(
        user_models.Doctors.user_id == user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not registered as a doctor"
        )

    if not medical_record.appointment or doctor.id != medical_record.appointment.doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add lab tests to this record"
        )

    test_catalog = db.query(medical_models.AvailableTests).filter(
        medical_models.AvailableTests.id == data.test_catalog_id
    ).first()

    if not test_catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested lab test catalog entry was not found"
        )

    invoice = medical_record.appointment.invoice

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create lab test: No active invoice exists for this appointment."
        )

    invoice.amount += test_catalog.price

    new_lab_tst = medical_models.LabTests(
        medical_record_id=medical_id,
        test_catalog_id=data.test_catalog_id
    )

    db.add(new_lab_tst)
    db.commit()
    db.refresh(new_lab_tst)

    return new_lab_tst


def update_lab_tst(
    data: medical_schemas.LabTestUpdateResults,
    db: Session
):
    """
    Update status, results, or attached files for a specific lab test order.
    """
    lab_tst = db.query(medical_models.LabTests).filter(
        medical_models.LabTests.id == data.id
    ).first()

    if not lab_tst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab test order not found."
        )

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key != "id" and value is not None:
            setattr(lab_tst, key, value)

    db.commit()
    db.refresh(lab_tst)

    return lab_tst


def get_lab_tsts(lab_id: int, db: Session):
    """
    Retrieve lab test order details by ID.
    """
    lab_tst = db.query(medical_models.LabTests).filter(
        medical_models.LabTests.id == lab_id
    ).first()

    if not lab_tst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab test order not found."
        )

    return lab_tst


def get_patient_lab_tests(db: Session, patient_id: int):
    """
    Retrieve all historical lab test orders for a given patient ID, sorted newest first.
    """
    patient_exists = db.query(user_models.Patients).filter(
        user_models.Patients.id == patient_id
    ).first()

    if not patient_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    lab_tests = (
        db.query(medical_models.LabTests)
        .join(medical_models.LabTests.medical_record)
        .join(medical_models.MedicalRecords.appointment)
        .filter(appointment_models.Appointments.patient_id == patient_id)
        .options(joinedload(medical_models.LabTests.test_info))
        .order_by(medical_models.LabTests.created_at.desc())
        .all()
    )

    return lab_tests