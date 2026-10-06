from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal

# ==========================================
# 1. Enums
# ==========================================


class TestTypeEnum(str, Enum):
    """
    Enum representing the classification type of a medical test.
    """
    LAB = "LAB"
    RADIOLOGY = "RADIOLOGY"


class TestStatus(str, Enum):
   
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ==========================================
# 2. Available Tests Schemas (Test Catalog)
# ==========================================


class AvailableTestBase(BaseModel):
    """
    Base schema for test catalog entries containing core attributes.
    """
    name: str = Field(..., max_length=150, example="Complete Blood Count (CBC)")
    test_type: TestTypeEnum
    price: Decimal = Field(..., gt=0, example=150.00)
    is_available: bool = True


class AvailableTestCreate(AvailableTestBase):
   
    pass


class AvailableTestUpdate(BaseModel):
   
    test_id: int
    name: Optional[str] = None
    test_type: Optional[TestTypeEnum] = None
    price: Optional[Decimal] = Field(None, gt=0)
    is_available: Optional[bool] = None


class AvailableTestResponse(AvailableTestBase):
    
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Lab Tests Schemas (Patient Lab Orders)
# ==========================================


class LabTestBase(BaseModel):
    """
    Base schema for patient lab test orders referencing a test catalog item.
    """
    test_catalog_id: int


class LabTestCreate(LabTestBase):
   
    pass


class LabTestUpdateResults(BaseModel):
   
    id: int
    result: Optional[str] = None
    result_file_url: Optional[str] = None
    status: Optional[TestStatus] = Field(default=TestStatus.COMPLETED)


class LabTestResponse(LabTestBase):
    
    id: int
    medical_record_id: int
    result: Optional[str] = None
    result_file_url: Optional[str] = None
    status: TestStatus
    created_at: datetime
    test_info: AvailableTestResponse

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. Medical Record Schemas
# ==========================================


class MedicalRecordBase(BaseModel):
    """
    Base schema for medical records containing diagnosis and prescription details.
    """
    appointment_id: int
    diagnosis: str = Field(..., min_length=3)
    prescription: Optional[str] = None
    attachment_url: Optional[str] = None


class MedicalRecordCreate(MedicalRecordBase):
    
    pass


class MedicalRecordUpdate(BaseModel):
   
    diagnosis: Optional[str] = Field(None, min_length=3)
    prescription: Optional[str] = None
    attachment_url: Optional[str] = None


class MedicalRecordResponse(MedicalRecordBase):
    
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)