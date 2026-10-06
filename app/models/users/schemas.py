from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ==========================================
# 1. Enums
# ==========================================


class UserRole(str, Enum):
    """
    Enum representing system-wide user roles.
    """
    admin = "Admin"
    patient = "Patient"
    doctor = "Doctor"


class UserStatus(str, Enum):
    """
    Enum representing active status flags for user activation updates.
    """
    true = "True"
    false = "False"


class SpecializationEnum(str, Enum):
    """
    Enum representing medical specializations for doctors.
    """
    CARDIOLOGY = "CARDIOLOGY"
    PULMONOLOGY = "PULMONOLOGY"
    INTERNAL_MEDICINE = "INTERNAL_MEDICINE"
    PEDIATRICS = "PEDIATRICS"
    ORTHOPEDICS = "ORTHOPEDICS"
    NEUROLOGY = "NEUROLOGY"
    DERMATOLOGY = "DERMATOLOGY"
    OPHTHALMOLOGY = "OPHTHALMOLOGY"
    ENT = "ENT"
    GENERAL_SURGERY = "GENERAL_SURGERY"


# ==========================================
# 2. User Schemas
# ==========================================


class UserBase(BaseModel):
    """
    Base schema containing common user profile attributes.
    """
    full_name: str = Field(..., min_length=3, max_length=50)
    telefon: Optional[str] = Field(None, max_length=20)
    email: EmailStr


class UserCreate(UserBase):
   
    password: str = Field(..., min_length=8)


class DoctorCreateByAdmin(UserBase):
   
    password: str = Field(..., min_length=8)
    specialization: str
    consultation_fee: float


class UserUpdate(BaseModel):
   
    is_active: UserStatus


class UserResponse(UserBase):
   
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPublicResponse(BaseModel):
   
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Doctor Profile Schemas
# ==========================================


class DoctorBase(BaseModel):
    """
    Base schema defining doctor specialization and consultation fees.
    """
    specialization: SpecializationEnum
    consultation_fee: Decimal


class DoctorProfileCreate(DoctorBase):
    
    pass


class DoctorProfileUpdate(BaseModel):
   
    specialization: Optional[SpecializationEnum] = None
    consultation_fee: Optional[Decimal] = None


class DoctorProfileResponse(DoctorBase):
   
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class DoctorDetailResponse(DoctorProfileResponse):
   
    user: UserPublicResponse
    specialization: SpecializationEnum
    consultation_fee: Decimal

    model_config = ConfigDict(from_attributes=True)


class DoctorUserMinimal(BaseModel):
    """
    Minimal user details schema included in doctor listing outputs.
    """
    full_name: str
    email: str
    telefon: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DoctorListResponse(BaseModel):
   
    id: int  
    user_id: int
    specialization: SpecializationEnum
    consultation_fee: float
    user: DoctorUserMinimal

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. Patient Profile Schemas
# ==========================================


class PatientBase(BaseModel):
    """
    Base schema for patient medical and personal details.
    """
    date_of_birth: Optional[date] = None
    medical_history_summary: Optional[str] = None


class PatientProfileCreate(PatientBase):
   
    pass


class PatientProfileResponse(PatientBase):
    
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. Authentication & Token Schemas
# ==========================================


class Userlogin(BaseModel):
    """
    Schema for handling user login credentials.
    """
    email: EmailStr
    password: str


class Token(BaseModel):
    """
    Response schema returning standard JWT access token payloads.
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Decoded token payload schema storing authenticated user ID context.
    """
    user_id: Optional[int] = None