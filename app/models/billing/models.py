from app.database import Base
from app.models.billing import schemas
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import relationship


class Invoices(Base):
    """
    SQLAlchemy model representing the invoices table in the database.
    Handles billing details for appointments, including base amounts,
    discounts, payment status, and timestamps.
    """
    __tablename__ = "invoices"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    appointment_id = Column(
        Integer, ForeignKey("appointments.id"), unique=True, nullable=False
    )


    amount = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0.00, nullable=False)  # Discount percentage (e.g., 15.00%)
    discount_amount = Column(Numeric(10, 2), default=0.00, nullable=False)      # Discount value in absolute terms
    status = Column(
        SQLEnum(schemas.InvoiceStatus),
        default=schemas.InvoiceStatus.PENDING,
        nullable=False,
    )

    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    appointment = relationship("Appointments", back_populates="invoice")

    @property
    def final_amount(self):
        """
        Calculates the net payable amount after subtracting discount_amount from total amount.
        """
        return self.amount - self.discount_amount