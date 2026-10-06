from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal

# ==========================================
# 1. Enums
# ==========================================


class InvoiceStatus(str, Enum):
    """
    Enum representing the current payment status of an invoice.
    """
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


# ==========================================
# 2. Invoice Schemas
# ==========================================


class InvoiceBase(BaseModel):
    """
    Base schema for invoice payloads containing core financial fields.
    """
    amount: Decimal = Field(...)


class InvoiceCreate(InvoiceBase):
    """
    Schema for creating a new invoice record.
    """
    pass


class ApplyDiscountRequest(BaseModel):
    """
    Schema for requesting a discount application on an existing invoice.
    """
    discount_percentage: Decimal = Field(
        ..., 
        ge=0, 
        le=100, 
        description="Discount percentage to be applied (0-100)"
    )


class InvoiceUpdate(BaseModel):
    """
    Schema for updating the status of an existing invoice.
    """
    status: Optional[InvoiceStatus] = None


class InvoiceResponse(InvoiceBase):
    """
    Schema for output response when returning invoice details, including discount calculations.
    """
    id: int
    appointment_id: int
    amount: Decimal               # Original price before discount
    discount_percentage: Decimal  # Percentage discount applied
    discount_amount: Decimal      # Absolute monetary value of the discount
    final_amount: Decimal         # Final calculated price after discount
    status: InvoiceStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)