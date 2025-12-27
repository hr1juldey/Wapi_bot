"""Shared example data for API documentation.

All realistic Yawlit data used in Swagger examples.
Based on real chat.txt conversations from WhatsApp interactions.

This module provides DRY (Don't Repeat Yourself) example constants
for consistent, realistic API documentation across all endpoints.
"""

# Customer Examples (from chat.txt)
EXAMPLE_CUSTOMER_NAME = "Ayush"
EXAMPLE_CUSTOMER_NAME_ALT = "Test Contact"
EXAMPLE_CUSTOMER_PHONE = "917464026177"
EXAMPLE_CUSTOMER_PHONE_ALT = "919876543210"
EXAMPLE_CUSTOMER_EMAIL = "ayush@example.com"

# Vehicle Examples (from chat.txt - real registrations)
EXAMPLE_VEHICLE_HONDA = {
    "brand": "Honda",
    "model": "City",
    "registration": "BR01AB1999",
    "type": "Hatchback"
}

EXAMPLE_VEHICLE_TATA = {
    "brand": "Tata",
    "model": "Punch",
    "registration": "BR01AB2342",
    "type": "SUV"
}

EXAMPLE_VEHICLE_CRETA = {
    "brand": "Honda",
    "model": "Creta",
    "registration": "BR01AB2346",
    "type": "Sedan"
}

# Service Examples (from chat.txt - actual Yawlit services)
EXAMPLE_SERVICE_HATCHBACK = {
    "id": "SERV-HATCH-001",
    "product_id": "HatchBack-Premium-One-Time",
    "name": "HatchBack Premium (One Time)",
    "price": 499.0,
    "vehicle_type": "Hatchback"
}

EXAMPLE_SERVICE_SEDAN = {
    "id": "SERV-SEDAN-001",
    "product_id": "Sedan-Premium-One-Time",
    "name": "Sedan Premium (One Time)",
    "price": 599.0,
    "vehicle_type": "Sedan"
}

EXAMPLE_SERVICE_SUV = {
    "id": "SERV-SUV-001",
    "product_id": "SUV-Premium-One-Time",
    "name": "Suv Premium (One Time)",
    "price": 599.0,
    "vehicle_type": "SUV"
}

# Payment Examples (UUIDs and transaction data)
EXAMPLE_SESSION_UUID = "550e8400-e29b-41d4-a716-446655440000"
EXAMPLE_SESSION_UUID_ALT = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
EXAMPLE_SESSION_UUID_THIRD = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

# UPI Examples (Yawlit's actual UPI ID)
EXAMPLE_UPI_ID = "yawlit@paytm"
EXAMPLE_UPI_STRING = f"upi://pay?pa={EXAMPLE_UPI_ID}&pn=Yawlit&am=499.00&cu=INR&tn=Booking"
EXAMPLE_UPI_STRING_ALT = f"upi://pay?pa={EXAMPLE_UPI_ID}&pn=Yawlit&am=599.00&cu=INR&tn=Booking"

# Payment Amounts (from chat.txt - actual service prices)
EXAMPLE_PAYMENT_AMOUNT_HATCHBACK = 499.00
EXAMPLE_PAYMENT_AMOUNT_SEDAN = 599.00
EXAMPLE_PAYMENT_AMOUNT_SUV = 599.00

# Transaction References (realistic UTR format)
EXAMPLE_UTR_NUMBER = "UTR123456789"
EXAMPLE_UTR_NUMBER_ALT = "TXN987654321"
EXAMPLE_TRANSACTION_ID = "TXN20251227001"

# Admin Examples
EXAMPLE_ADMIN_EMAIL = "admin@yawlit.com"
EXAMPLE_ADMIN_EMAIL_ALT = "support@yawlit.com"

# Booking Examples (from chat.txt - realistic booking flow)
EXAMPLE_BOOKING_ID = "BOOK-2025-001"
EXAMPLE_BOOKING_ID_ALT = "DEMO-20251224135933"
EXAMPLE_BOOKING_DATE = "2025-12-28"
EXAMPLE_BOOKING_DATE_ALT = "2025-12-29"

# Time Slot Examples (from chat.txt - actual slots)
EXAMPLE_TIME_SLOT_MORNING = "10:00 - 12:00"
EXAMPLE_TIME_SLOT_AFTERNOON = "16:00 - 18:00"
EXAMPLE_TIME_SLOT_EVENING = "18:00 - 20:00"

# Slot ID Examples
EXAMPLE_SLOT_ID = "SLOT-2025-001"
EXAMPLE_SLOT_ID_MORNING = "SLOT-MORNING-1000"
EXAMPLE_SLOT_ID_AFTERNOON = "SLOT-AFTERNOON-1600"

# Address Examples
EXAMPLE_ADDRESS_ID = "ADDR-2025-001"
EXAMPLE_ADDRESS_CITY = "Patna"
EXAMPLE_ADDRESS_FULL = "123, Gandhi Maidan, Patna, Bihar 800001"

# Conversation Examples
EXAMPLE_CONVERSATION_ID = "919876543210"
EXAMPLE_CONVERSATION_ID_ALT = "917464026177"

# Timestamp Examples (ISO format)
EXAMPLE_TIMESTAMP_CREATED = "2025-12-27T10:00:00"
EXAMPLE_TIMESTAMP_CONFIRMED = "2025-12-27T14:30:45.123456"
EXAMPLE_TIMESTAMP_REMINDED = "2025-12-27T12:00:00"

# Brain/RL Gym Examples
EXAMPLE_DREAM_TASK_ID = "celery-task-123abc"
EXAMPLE_TRAIN_TASK_ID = "celery-task-456def"
EXAMPLE_DECISION_COUNT = 1523
EXAMPLE_CONVERSATION_THRESHOLD = 50

# Error Message Examples
EXAMPLE_ERROR_NOT_FOUND = "Payment session not found"
EXAMPLE_ERROR_ALREADY_CONFIRMED = "Payment already confirmed"
EXAMPLE_ERROR_INVALID_REQUEST = "Invalid request parameters"
EXAMPLE_ERROR_SERVER_ERROR = "Internal server error occurred"
