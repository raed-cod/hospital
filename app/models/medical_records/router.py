from fastapi import APIRouter, Depends
from app.models.medical_records import schemas as medical_schemas, services
from sqlalchemy.orm import Session
from app.models.users import models as user_models, schemas as user_schemas
from app.database import get_db
from app import security


router = APIRouter(prefix="/medicalRecords", tags=["MedicalRecords Flow"])


@router.post("/Test_avalibale", response_model=medical_schemas.AvailableTestResponse)
def create_test_avalibale(
    data: medical_schemas.AvailableTestCreate,
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.admin])
    ),
    db: Session = Depends(get_db),
):
    """
    Create a new available test entry in the catalog (Admin only).
    """
    return services.create_test(
        data=data,
        db=db,
        user=current_user,
    )


@router.patch("/available-tests/{test_id}", response_model=medical_schemas.AvailableTestResponse)
def update_data(
    data: medical_schemas.AvailableTestUpdate,
    test_id: int,
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.admin])
    ),
    db: Session = Depends(get_db),
):
    """
    Update test catalog details for a given test ID (Admin only).
    """
    return services.update_test_data(
        data=data,
        db=db,
        test_id=test_id,
        user=current_user,
    )


@router.get("/get_avalibal_tst", response_model=list[medical_schemas.AvailableTestResponse])
def get_avalible_tst(
    urrent_user: user_models.Users = Depends(
        security.require_roles([
            user_schemas.UserRole.doctor,
            user_schemas.UserRole.admin,
        ])
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve all available tests from the catalog (Accessible by Doctor and Admin).
    """
    return services.get_tsts(db=db)


@router.post("/medical_records", response_model=medical_schemas.MedicalRecordResponse)
def create_medical_record(
    data: medical_schemas.MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.doctor])
    ),
):
    """
    Create a new medical record for an appointment (Doctor only).
    """
    return services.create_medical_records(
        data=data,
        db=db,
    )


@router.patch("/medical_records_update/{medical_id}", response_model=medical_schemas.MedicalRecordResponse)
def update_medical_record(
    data: medical_schemas.MedicalRecordUpdate,
    medical_record_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.doctor])
    ),
):
    """
    Update an existing medical record by ID (Doctor only).
    """
    return services.update_medical_record(
        data=data,
        medical_record_id=medical_record_id,
        db=db,
        user=current_user,
    )


@router.get("/get_medical_records/{medical_id}", response_model=medical_schemas.MedicalRecordResponse)
def get_medical_record(
    medical_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([
            user_schemas.UserRole.doctor,
            user_schemas.UserRole.admin,
        ])
    ),
):
    """
    Retrieve medical record details by ID (Accessible by Doctor and Admin).
    """
    return services.get_medical_record(
        medical_id=medical_id,
        db=db,
        user=current_user,
    )


@router.post("/lab_tst/{medical_id}", response_model=medical_schemas.LabTestResponse)
def create_lab_tst(
    data: medical_schemas.LabTestCreate,
    medical_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.doctor])
    ),
):
    """
    Order a new lab test associated with a medical record (Doctor only).
    """
    return services.create_lab_tst(
        data=data,
        medical_id=medical_id,
        db=db,
        user=current_user,
    )


@router.patch("/update/lab_tst{lab_id}", response_model=medical_schemas.LabTestResponse)
def update_lab_tst(
    data: medical_schemas.LabTestUpdateResults,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.doctor])
    ),
):
    """
    Update results or status for a specific lab test (Doctor only).
    """
    return services.update_lab_tst(
        data=data,
        db=db,
    )


@router.get("/get_lab_tst{lab_id}", response_model=medical_schemas.LabTestResponse)
def get_lab_tst(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.doctor])
    ),
):
    """
    Retrieve lab test details by ID (Doctor only).
    """
    return services.get_lab_tsts(
        lab_id=lab_id,
        db=db,
    )


@router.get("/get_all_tst{patein_id}", response_model=list[medical_schemas.LabTestResponse])
def get_all_lab_tst(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([user_schemas.UserRole.doctor])
    ),
):
    """
    Retrieve all lab tests performed for a specific patient (Doctor only).
    """
    return services.get_patient_lab_tests(
        db=db,
        patient_id=patient_id,
    )