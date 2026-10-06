from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.models.users import models as user_models, schemas as user_schemas
from app.database import get_db
from app import security
from app.models.billing import schemas as biling_schemas
from app.models.billing import services


router = APIRouter(prefix="/biling", tags=["Invoice Flow"])


@router.get("/get_invoice{appointment_id}", response_model=biling_schemas.InvoiceResponse)
def get_invoice(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([
            user_schemas.UserRole.admin,
            user_schemas.UserRole.doctor,
            user_schemas.UserRole.patient
        ])
    )
):
    """
    Retrieve invoice details associated with a specific appointment ID.
    Accessible by Admin, Doctor, or Patient roles.
    """
    return services.get_invoice(
        db=db,
        appointment_id=appointment_id
    )


@router.patch(
    "/{invoice_id}/discount",
    response_model=biling_schemas.InvoiceResponse,
)
def apply_discount(
    invoice_id: int,
    data: biling_schemas.ApplyDiscountRequest,
    db: Session = Depends(get_db),
    current_user: user_models.Users = Depends(
        security.require_roles([
            user_schemas.UserRole.admin,
            user_schemas.UserRole.doctor,
        ])
    )
):
    """
    Apply a percentage discount to a target invoice.
    Restricted to Admin and Doctor roles.
    """
    return services.apply_invoice_discount(
        db=db,
        invoice_id=invoice_id,
        discount_percentage=data.discount_percentage,
        user=current_user
    )