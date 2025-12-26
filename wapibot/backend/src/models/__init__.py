"""Domain models package.

Exports all validated Pydantic models organized by domain.
"""

from models.core import ValidationResult, ExtractionMetadata, ConfidenceThresholdConfig
from models.customer import Name, Phone, Email
from models.vehicle import VehicleBrand, VehicleDetails
from models.appointment import Date, Appointment
from models.sentiment import SentimentDimension, SentimentScores
from models.intent import IntentClass, Intent
from models.response import ChatbotResponse, ExtractionResult
from models.payment_session import PaymentSession, PaymentStatus
from models.payment_transaction import PaymentTransaction, TransactionType
from models.payment_reminder import PaymentReminder, ReminderStatus

__all__ = [
    # Core
    "ValidationResult",
    "ExtractionMetadata",
    "ConfidenceThresholdConfig",
    # Customer
    "Name",
    "Phone",
    "Email",
    # Vehicle
    "VehicleBrand",
    "VehicleDetails",
    # Appointment
    "Date",
    "Appointment",
    # Sentiment
    "SentimentDimension",
    "SentimentScores",
    # Intent
    "IntentClass",
    "Intent",
    # Response
    "ChatbotResponse",
    "ExtractionResult",
    # Payment
    "PaymentSession",
    "PaymentStatus",
    "PaymentTransaction",
    "TransactionType",
    "PaymentReminder",
    "ReminderStatus",
]
