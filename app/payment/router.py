from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.payment import services

router = APIRouter(prefix="/payments", tags=["Payments"])


# ==========================================
# 1. Response Schemas
# ==========================================


class CheckoutResponse(BaseModel):
    checkout_url: str


class PaymentRedirectResponse(BaseModel):
    status: str
    message: str
    invoice_id: int


# ==========================================
# 2. Payment Endpoints
# ==========================================


@router.post(
    "/checkout/{invoice_id}",
    response_model=CheckoutResponse,
    status_code=status.HTTP_200_OK,
)
def create_checkout(
    invoice_id: int, db: Session = Depends(get_db)
) -> CheckoutResponse:
    """
    Generate a Stripe Checkout session URL for a given invoice ID.
    """
    checkout_url = services.create_invoice_checkout_session(
        db=db, invoice_id=invoice_id
    )
    return CheckoutResponse(checkout_url=checkout_url)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(
    request: Request, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Handle asynchronous Stripe webhooks to process payment state updates.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    return services.process_stripe_webhook_payload(
        payload=payload, sig_header=sig_header, db=db
    )


@router.get(
    "/success",
    response_model=PaymentRedirectResponse,
    status_code=status.HTTP_200_OK,
)
def payment_success(invoice_id: int) -> PaymentRedirectResponse:
    """
    Redirect endpoint displayed to users upon successful payment processing.
    """
    return PaymentRedirectResponse(
        status="success",
        message=f"Payment completed successfully for invoice #{invoice_id}!",
        invoice_id=invoice_id,
    )


@router.get(
    "/cancel",
    response_model=PaymentRedirectResponse,
    status_code=status.HTTP_200_OK,
)
def payment_cancel(invoice_id: int) -> PaymentRedirectResponse:
    """
    Redirect endpoint displayed to users when a checkout process is cancelled.
    """
    return PaymentRedirectResponse(
        status="cancelled",
        message=f"Payment process was cancelled for invoice #{invoice_id}.",
        invoice_id=invoice_id,
    )