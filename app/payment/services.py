from decimal import Decimal
import logging
from typing import Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import stripe

from app.config import settings
from app.models.billing import models, schemas

# Configure Module Logger
logger = logging.getLogger(__name__)

# Initialize Stripe API Key from Configuration
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_invoice_checkout_session(db: Session, invoice_id: int) -> str:
    """
    Generate a Stripe Checkout session URL for an unpaid invoice using system configuration settings.

    Args:
        db (Session): Database session instance.
        invoice_id (int): Primary key ID of the invoice to process.

    Returns:
        str: Directly navigable Stripe Checkout URL.
    """
    invoice = (
        db.query(models.Invoices)
        .filter(models.Invoices.id == invoice_id)
        .first()
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    if invoice.status == schemas.InvoiceStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice is already paid",
        )

    amount_in_cents = int(invoice.final_amount * Decimal("100"))

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Invoice #{invoice.id}",
                        },
                        "unit_amount": amount_in_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.BASE_URL}/payments/success?invoice_id={invoice.id}",
            cancel_url=f"{settings.BASE_URL}/payments/cancel?invoice_id={invoice.id}",
            metadata={"invoice_id": str(invoice.id)},
        )

        logger.info(f"Created Stripe Session #{session.id} for Invoice #{invoice.id}")
        return session.url

    except stripe.error.StripeError as e:
        logger.error(f"Stripe Session creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


def process_stripe_webhook_payload(
    payload: bytes, sig_header: str, db: Session
) -> Dict[str, str]:
    """
    Construct and verify incoming Stripe Webhook events to update invoice payment records.

    Args:
        payload (bytes): Raw HTTP binary payload.
        sig_header (str): Stripe signature header content.
        db (Session): Database session instance.

    Returns:
        Dict[str, str]: Execution status message.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"].to_dict()
        metadata = session_data.get("metadata", {}) or {}

        raw_invoice_id = metadata.get("invoice_id")
        invoice_id = (
            str(raw_invoice_id).strip()
            if raw_invoice_id is not None
            else None
        )

        payment_status = session_data.get("payment_status") or session_data.get(
            "status"
        )

        logger.debug(
            f"Webhook Processing: raw_invoice_id={raw_invoice_id}, "
            f"invoice_id={invoice_id}, payment_status={payment_status}"
        )

        is_paid = payment_status in ["paid", "complete", "succeeded"]

        if invoice_id and invoice_id != "None" and is_paid:
            try:
                parsed_id = int(invoice_id)
                invoice = (
                    db.query(models.Invoices)
                    .filter(models.Invoices.id == parsed_id)
                    .first()
                )

                if invoice:
                    invoice.status = schemas.InvoiceStatus.PAID
                    db.commit()
                    db.refresh(invoice)
                    logger.info(f"Invoice #{invoice.id} status updated to PAID.")
                else:
                    logger.warning(f"Invoice #{parsed_id} not found in database.")

            except Exception as e:
                db.rollback()
                logger.error(f"Database update failed during webhook execution: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database error: {str(e)}",
                )
        else:
            logger.warning(
                f"Webhook verification bypassed - valid_invoice_id: {bool(invoice_id and invoice_id != 'None')}, "
                f"is_paid: {is_paid}"
            )

    return {"status": "success"}