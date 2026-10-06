from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
import stripe
from datetime import datetime, timezone

from app.models.billing import models, schemas
from app.models.users import models as user_models, schemas as user_schemas
from app.models.appointments import models as appointment_models


# Maximum allowed discount percentage limits based on user role
MAX_DISCOUNT_LIMITS = {
    user_schemas.UserRole.doctor: Decimal("20.00"),  # Doctor limit: 20%
    user_schemas.UserRole.admin: Decimal("100.00"),  # Admin limit: 100%
}


def apply_invoice_discount(
    db: Session,
    invoice_id: int,
    discount_percentage: Decimal,
    user: user_models.Users
):
    """
    Apply a percentage discount to an unpaid invoice, ensuring the discount
    percentage does not exceed the role-based maximum limits.
    """
    # 1. Retrieve the maximum allowed discount limit based on the user's role
    max_allowed = MAX_DISCOUNT_LIMITS.get(user.role, Decimal("0.00"))

    if discount_percentage > max_allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You do not have permission to grant a discount higher than {max_allowed}%"
        )

    # 2. Retrieve the invoice by ID
    invoice = db.query(models.Invoices).filter(
        models.Invoices.id == invoice_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # 3. Verify that doctors can only modify invoices belonging to their own appointments
    if user.role == user_schemas.UserRole.doctor:
        doctor = db.query(user_models.Doctors).filter(
            user_models.Doctors.user_id == user.id
        ).first()

        if not doctor or invoice.appointment.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to discount this invoice"
            )

    # 4. Ensure discounts are not applied to already paid invoices
    if invoice.status == schemas.InvoiceStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply discount to a PAID invoice"
        )

    # 5. Calculate discount amount and update the invoice record
    calculated_discount = invoice.amount * (discount_percentage / Decimal("100"))

    invoice.discount_percentage = discount_percentage
    invoice.discount_amount = round(calculated_discount, 2)

    db.commit()
    db.refresh(invoice)

    return invoice


def get_invoice(db: Session, appointment_id: int):
    """
    Retrieve invoice details associated with a specific appointment ID.
    """
    invoice = db.query(models.Invoices).filter(
        models.Invoices.appointment_id == appointment_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found for this appointment"
        )

    return invoice